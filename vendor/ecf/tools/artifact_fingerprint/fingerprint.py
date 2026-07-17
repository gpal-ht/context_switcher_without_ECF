#!/usr/bin/env python3
"""
Artifact fingerprinting (read-only, standard library only).

Produces lowercase hexadecimal SHA-256 digests of files. Files are hashed in
binary mode and streamed in fixed-size chunks so large artifacts are never
loaded entirely into memory. The hashed file is never modified.

CLI:
    python -m tools.artifact_fingerprint.fingerprint <path>
    python -m tools.artifact_fingerprint.fingerprint <path> --format json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# 64 KiB streaming chunk — bounded memory for arbitrarily large files.
CHUNK_SIZE = 65536


class FingerprintError(Exception):
    """Raised for missing paths, directories, or unreadable files."""


def sha256_file(path, chunk_size: int = CHUNK_SIZE) -> str:
    """
    Return the lowercase hex SHA-256 of a file's bytes.

    Streams the file in `chunk_size` blocks (never loads it whole). Read-only.

    Raises FingerprintError for a missing path, a directory, or a read error.
    Directory hashing is intentionally not implemented.
    """
    p = Path(path)
    if not p.exists():
        raise FingerprintError(f"path does not exist: {p}")
    if p.is_dir():
        raise FingerprintError(f"path is a directory (directory hashing not supported): {p}")
    if not p.is_file():
        raise FingerprintError(f"path is not a regular file: {p}")

    h = hashlib.sha256()
    try:
        with open(p, "rb") as fh:  # binary mode; read-only
            for block in iter(lambda: fh.read(chunk_size), b""):
                h.update(block)
    except OSError as exc:
        raise FingerprintError(f"cannot read file: {p} ({exc})")
    return h.hexdigest()  # hexdigest() is already lowercase


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of a byte string."""
    if not isinstance(data, (bytes, bytearray)):
        raise FingerprintError("sha256_bytes requires bytes")
    return hashlib.sha256(data).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only SHA-256 fingerprint of a file.")
    parser.add_argument("path", help="File to fingerprint.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        digest = sha256_file(args.path)
    except FingerprintError as exc:
        sys.stderr.write(f"FINGERPRINT ERROR: {exc}\n")
        return 2

    if args.format == "json":
        print(json.dumps({
            "path": str(Path(args.path).as_posix()),
            "algorithm": "sha256",
            "sha256": digest,
        }, indent=2))
    else:
        print(f"{digest}  {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
