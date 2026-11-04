import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STARTUP = """
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import panel
panel.HOME = Path(sys.argv[2])
panel.PIDFILE = panel.HOME / "panel.pid"

class StartupReached(Exception):
    pass

class Application:
    @staticmethod
    def sharedApplication():
        raise StartupReached()

panel.NSApplication = Application
try:
    panel.main()
except StartupReached:
    print("STARTED")
"""


class SingleInstanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name)
        self.pidfile = self.state / "panel.pid"

    def start_panel(self):
        result = subprocess.run(
            [sys.executable, "-c", STARTUP, str(ROOT / "app"), str(self.state)],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_reused_pid_does_not_block_startup(self):
        self.pidfile.write_text(str(os.getpid()))
        self.assertEqual(self.start_panel(), "STARTED")
        self.assertNotEqual(self.pidfile.read_text(), str(os.getpid()))

    def test_lock_blocks_duplicates_and_is_released_on_exit(self):
        self.pidfile.write_text("stale")
        with self.pidfile.open("a+") as owner:
            fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.start_panel(), "")
            self.assertEqual(self.pidfile.read_text(), "stale")
        self.assertEqual(self.start_panel(), "STARTED")
        self.assertEqual(self.start_panel(), "STARTED")


if __name__ == "__main__":
    unittest.main()
