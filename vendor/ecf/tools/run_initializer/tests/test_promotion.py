"""
Windows promotion hardening for run initialization.

Unit-tests promote_run_directory with injectable rename/sleep: transient Windows
sharing/access errors are retried (bounded), non-transient/logic errors are not,
the destination is never overwritten, and there is never a partial final run.
"""
import errno
import os
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from run_initializer.initializer import promote_run_directory   # noqa: E402
from run_initializer.models import InitError                    # noqa: E402


def _transient():
    e = PermissionError("Access is denied")
    e.winerror = 5  # ERROR_ACCESS_DENIED
    return e


def _non_transient():
    e = OSError("logic error / missing source")
    e.winerror = 1234
    e.errno = errno.ENOENT
    return e


def flaky(fail_times, err_factory):
    """A rename that raises err_factory() the first `fail_times` calls, then does
    a real os.rename."""
    state = {"n": 0}

    def _rename(src, dst):
        if state["n"] < fail_times:
            state["n"] += 1
            raise err_factory()
        os.rename(src, dst)

    _rename.state = state
    return _rename


class SleepSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, d):
        self.calls.append(d)


class TestPromotion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.temp_dir = self.root / ".init-RUN-X-abc123"
        self.temp_dir.mkdir()
        (self.temp_dir / "state.yaml").write_text("run_id: RUN-X\n", encoding="utf-8")
        self.final = self.root / "RUN-X"

    def tearDown(self):
        self.tmp.cleanup()

    def test_21_normal_promotion_succeeds(self):
        promote_run_directory(self.temp_dir, self.final)
        self.assertTrue((self.final / "state.yaml").is_file())
        self.assertFalse(self.temp_dir.exists())

    def test_22_first_transient_then_success(self):
        sleep = SleepSpy()
        promote_run_directory(self.temp_dir, self.final, sleep=sleep, rename=flaky(1, _transient))
        self.assertTrue((self.final / "state.yaml").is_file())
        self.assertFalse(self.temp_dir.exists())
        self.assertEqual(len(sleep.calls), 1)

    def test_23_multiple_transient_then_success_within_limit(self):
        sleep = SleepSpy()
        promote_run_directory(self.temp_dir, self.final, retries=5, sleep=sleep,
                              rename=flaky(3, _transient))
        self.assertTrue((self.final / "state.yaml").is_file())
        self.assertEqual(len(sleep.calls), 3)

    def test_24_retry_exhaustion_cleans_temp_and_leaves_no_final(self):
        sleep = SleepSpy()
        with self.assertRaises(InitError):
            promote_run_directory(self.temp_dir, self.final, retries=3, sleep=sleep,
                                  rename=flaky(99, _transient))
        self.assertFalse(self.temp_dir.exists())
        self.assertFalse(self.final.exists())
        self.assertEqual(len(sleep.calls), 2)  # slept between the 3 attempts, not after the last

    def test_25_non_transient_errors_not_retried(self):
        sleep = SleepSpy()
        with self.assertRaises(OSError) as ctx:
            promote_run_directory(self.temp_dir, self.final, sleep=sleep,
                                  rename=flaky(99, _non_transient))
        self.assertNotIsInstance(ctx.exception, InitError)  # raw non-transient propagates
        self.assertEqual(len(sleep.calls), 0)               # never retried
        self.assertTrue(self.temp_dir.exists())             # left for the caller to clean

    def test_26_destination_created_race_fails_safely(self):
        self.final.mkdir()  # destination appears (race)
        with self.assertRaises(InitError):
            promote_run_directory(self.temp_dir, self.final)
        self.assertFalse(self.temp_dir.exists())            # temp cleaned
        self.assertTrue(self.final.exists())                # existing destination untouched

    def test_27_no_partial_final_run_on_exhaustion(self):
        with self.assertRaises(InitError):
            promote_run_directory(self.temp_dir, self.final, retries=2,
                                  sleep=lambda d: None, rename=flaky(99, _transient))
        self.assertFalse(self.final.exists())


if __name__ == "__main__":
    unittest.main()
