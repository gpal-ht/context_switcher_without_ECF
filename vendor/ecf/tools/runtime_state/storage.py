"""
Runtime-state storage primitives: constrained block-YAML round-trip, atomic
writes, path safety, and content fingerprinting.

Design notes
------------
* state.yaml / manifest.yaml are emitted as constrained block YAML so they stay
  readable by the read-only planner (which parses `provenance.mode` and the
  manifest `tasks:` list). This module both emits and parses that subset.
* lock / journal are JSON (a strict YAML subset) for robust round-trip.
* Every mutation goes through an atomic temp-write + os.replace on the SAME
  filesystem. Nothing is ever written directly to a final path.
* All paths are validated to resolve strictly under the run directory. Absolute
  paths, `..` traversal, and symlink escapes are rejected.

Standard library only.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

# Reuse the approved fingerprint tool.
import sys
_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from artifact_fingerprint import fingerprint as fp  # noqa: E402


class StorageError(Exception):
    """Raised for serialization, atomic-write, or path-safety failures."""


class PathSafetyError(StorageError):
    """Raised when a path would escape the run directory or is unsafe."""


# --------------------------------------------------------------------------- #
# Path safety
# --------------------------------------------------------------------------- #

def safe_join(run_dir: Path, relative: str) -> Path:
    """
    Resolve `relative` strictly under `run_dir`.

    Rejects absolute paths, `..` traversal, and any resolution (including via
    symlinks) that escapes the run root.
    """
    if relative is None or relative == "":
        raise PathSafetyError("empty path")
    rel = str(relative).replace("\\", "/")
    p = Path(rel)
    if p.is_absolute() or (len(rel) >= 2 and rel[1] == ":"):
        raise PathSafetyError(f"absolute paths are not allowed: {relative}")
    if ".." in p.parts:
        raise PathSafetyError(f"path traversal is not allowed: {relative}")
    root = Path(os.path.realpath(run_dir))
    candidate = Path(os.path.realpath(run_dir / p))
    try:
        candidate.relative_to(root)
    except ValueError:
        raise PathSafetyError(f"path escapes the run directory: {relative}")
    return run_dir / p


def assert_no_unsafe_symlink(path: Path, run_dir: Path) -> None:
    """Refuse to promote onto/through a symlink that escapes the run root."""
    root = Path(os.path.realpath(run_dir))
    node = path
    for parent in [path, *path.parents]:
        if parent == run_dir or parent == root:
            break
        if parent.is_symlink():
            target = Path(os.path.realpath(parent))
            try:
                target.relative_to(root)
            except ValueError:
                raise PathSafetyError(f"unsafe symlink escapes run directory: {parent}")
    _ = node


# --------------------------------------------------------------------------- #
# Atomic writes
# --------------------------------------------------------------------------- #

def atomic_write_text(path: Path, text: str) -> None:
    """Write text atomically: temp file in the same directory, fsync, os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # atomic on same filesystem
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes atomically (temp file in the same directory, fsync, os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_promote(src: Path, dst: Path, run_dir: Path) -> None:
    """Atomically move a staged file to its final path (rejecting symlink escapes)."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    assert_no_unsafe_symlink(dst, run_dir)
    os.replace(src, dst)


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n").replace("\r", "\n")


def sha256_file(path: Path) -> str:
    return fp.sha256_file(path)


# --------------------------------------------------------------------------- #
# JSON (lock / journal)
# --------------------------------------------------------------------------- #

def dump_json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=False)


def load_json(text: str):
    return json.loads(text)


# --------------------------------------------------------------------------- #
# Constrained block-YAML (state.yaml / manifest.yaml)
# --------------------------------------------------------------------------- #

# Constrained shape (deliberately restricted for robust round-trip):
#   top-level: mapping
#   value:     scalar | flat-map (scalar leaves) | list
#   list item: scalar | flat-dict (scalar leaves, incl. inline [a, b] scalar lists)
# There are NO nested lists inside list items and NO maps inside list items,
# which keeps the parser small and unambiguous. Per-task findings live at the
# manifest top level, not nested under each task.

_SPECIAL = set(":#{}[],&*!|>'\"%@`")


def _fmt_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, dict):   # only empty dicts reach here (non-empty handled by _emit)
        return "{}"
    if isinstance(v, list):  # inline flow list of scalars
        return "[" + ", ".join(_fmt_scalar(x) for x in v) + "]"
    s = str(v)
    if s == "" or s[0] in " -?[{" or s[-1] == " " or any(c in _SPECIAL for c in s) \
            or s.lower() in ("null", "true", "false", "yes", "no"):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _is_flat(d: dict) -> bool:
    return all(not isinstance(v, dict) for v in d.values())


def _emit(obj, indent, lines):
    pad = "  " * indent
    for k, v in obj.items():
        if isinstance(v, dict) and v:
            if not _is_flat(v):
                raise StorageError(f"nested non-flat map not supported: {k}")
            lines.append(f"{pad}{k}:")
            _emit(v, indent + 1, lines)
        elif isinstance(v, list) and v and any(isinstance(x, dict) for x in v):
            lines.append(f"{pad}{k}:")
            for item in v:
                _emit_dict_item(item, indent + 1, lines)
        else:
            lines.append(f"{pad}{k}: {_fmt_scalar(v)}")


def _emit_dict_item(item: dict, indent, lines):
    pad = "  " * indent
    keys = list(item.items())
    if not keys:
        lines.append(f"{pad}- {{}}")
        return
    (fk, fv), rest = keys[0], keys[1:]
    lines.append(f"{pad}- {fk}: {_fmt_scalar(fv)}")
    for k, v in rest:
        lines.append(f"{pad}  {k}: {_fmt_scalar(v)}")


def dump_yaml(obj: dict) -> str:
    if not isinstance(obj, dict):
        raise StorageError("top-level YAML must be a mapping")
    lines: list = []
    _emit(obj, 0, lines)
    return "\n".join(lines) + "\n"


def _parse_scalar(tok: str):
    tok = tok.strip()
    if tok in ("", "null", "~"):
        return None
    if tok == "true":
        return True
    if tok == "false":
        return False
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return tok[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if tok == "{}":
        return {}
    if tok == "[]":
        return []
    if tok[0] == "[" and tok[-1] == "]":
        inner = tok[1:-1].strip()
        return [_parse_scalar(x) for x in inner.split(",")] if inner else []
    if tok.lstrip("-").isdigit():
        try:
            return int(tok)
        except ValueError:
            pass
    return tok


def _rows(text: str):
    rows = []
    for raw in text.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        rows.append((indent, raw.strip()))
    return rows


def load_yaml(text: str):
    rows = _rows(text)
    if not rows:
        return {}
    value, _ = _parse_map(rows, 0, rows[0][0])
    return value


def _parse_map(rows, i, indent):
    result = {}
    while i < len(rows):
        cur_indent, content = rows[i]
        if cur_indent < indent or content.startswith("- "):
            break
        if cur_indent > indent:
            raise StorageError(f"unexpected indent: {content!r}")
        key, _, rest = content.partition(":")
        key, rest = key.strip(), rest.strip()
        if rest != "":
            result[key] = _parse_scalar(rest)
            i += 1
            continue
        # nested block: list of dict items, or a flat sub-map
        if i + 1 < len(rows) and rows[i + 1][1].startswith("- ") and rows[i + 1][0] > indent:
            child, i = _parse_dict_list(rows, i + 1, rows[i + 1][0])
            result[key] = child
        elif i + 1 < len(rows) and rows[i + 1][0] > indent:
            child, i = _parse_map(rows, i + 1, rows[i + 1][0])
            result[key] = child
        else:
            result[key] = None
            i += 1
    return result, i


def _parse_dict_list(rows, i, indent):
    items = []
    while i < len(rows):
        cur_indent, content = rows[i]
        if cur_indent != indent or not content.startswith("- "):
            break
        first = content[2:].strip()
        item = {}
        if ":" in first:
            k, _, v = first.partition(":")
            item[k.strip()] = _parse_scalar(v.strip())
        else:
            # scalar list item
            items.append(_parse_scalar(first))
            i += 1
            continue
        i += 1
        while i < len(rows) and rows[i][0] == indent + 2 and not rows[i][1].startswith("- "):
            k, _, v = rows[i][1].partition(":")
            item[k.strip()] = _parse_scalar(v.strip())
            i += 1
        items.append(item)
    return items, i
