"""
Tests for the artifact fingerprint tool.

Read-only. Temporary files are created under the OS temporary directory only.
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_PKG_PARENT = Path(__file__).resolve().parents[2]  # tools/
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from artifact_fingerprint import fingerprint as fp  # noqa: E402

# Known SHA-256 of b"abc".
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


class TestFingerprint(unittest.TestCase):
    def test_sha256_bytes_known_value(self):
        self.assertEqual(fp.sha256_bytes(b"abc"), ABC)

    def test_sha256_file_known_value(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"abc")
            self.assertEqual(fp.sha256_file(p), ABC)

    def test_lowercase_hex(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"Hello, world!\n")
            digest = fp.sha256_file(p)
            self.assertEqual(digest, digest.lower())
            self.assertEqual(len(digest), 64)

    def test_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"payload")
            before = (p.stat().st_mtime_ns, p.stat().st_size, p.read_bytes())
            fp.sha256_file(p)
            fp.sha256_file(p)
            after = (p.stat().st_mtime_ns, p.stat().st_size, p.read_bytes())
            self.assertEqual(before, after)

    def test_streaming_matches_oneshot(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "big.bin"
            data = b"x" * (250 * 1024)  # > several chunks
            p.write_bytes(data)
            self.assertEqual(fp.sha256_file(p, chunk_size=1024), fp.sha256_bytes(data))

    def test_missing_file_fails_clearly(self):
        with self.assertRaises(fp.FingerprintError):
            fp.sha256_file(Path("this-does-not-exist.xyz"))

    def test_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fp.FingerprintError):
                fp.sha256_file(Path(d))

    def test_cli_text(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"abc")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = fp.main([str(p)])
            self.assertEqual(rc, 0)
            self.assertIn(ABC, buf.getvalue())

    def test_cli_json(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"abc")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = fp.main([str(p), "--format", "json"])
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data["sha256"], ABC)
            self.assertEqual(data["algorithm"], "sha256")

    def test_cli_missing_exit_2(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = fp.main(["definitely-missing.xyz"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
