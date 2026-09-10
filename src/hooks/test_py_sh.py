#!/usr/bin/env python3
"""Tests for py.sh: it finds a Python 3, skips a broken python3, and stays quiet without one."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SHIM = HERE / "py.sh"
ACTIVATE = HERE / "activate.py"


def run(path_dir):
    env = dict(os.environ, PATH=str(path_dir), CLAUDE_PLUGIN_ROOT=str(HERE.parent.parent))
    return subprocess.run(["/bin/sh", str(SHIM), str(ACTIVATE)], capture_output=True, env=env, timeout=30)


class PyShimTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, name, body):
        p = self.bin / name
        p.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        p.chmod(0o755)

    def test_the_shim_runs_the_hook_with_the_same_output(self):
        self.fake("python3", f'exec "{sys.executable}" "$@"')
        direct = subprocess.run([sys.executable, str(ACTIVATE)], capture_output=True, timeout=30).stdout
        r = run(self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, direct)

    def test_a_store_stub_python3_falls_through_to_python(self):
        self.fake("python3", "exit 49")  # the Microsoft Store stub exits 49 in a non-TTY subprocess
        self.fake("python", f'exec "{sys.executable}" "$@"')
        r = run(self.bin)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("最多 5 句".encode("utf-8"), r.stdout)

    def test_no_interpreter_exits_0_with_one_line_on_stderr(self):
        self.fake("python3", "exit 49")
        r = run(self.bin)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b"")
        self.assertIn(b"no Python 3 found", r.stderr)


if __name__ == "__main__":
    unittest.main()
