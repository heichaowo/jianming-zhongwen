#!/usr/bin/env python3
"""Tests for lint_hook.py. Runs the hook as a subprocess with a hook event on stdin."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
HOOK = HERE / "lint_hook.py"
SLOP = "值得注意的是，我们应该对配置进行全面的分析；这一步至关重要——尤其是在生产环境。\n"
CLEAN = "运行迁移脚本。如果迁移失败，查看日志。\n"
BAD_REPLY = "好的，这是个好问题——先看日志。\n\n- 第一步检查网络。\n- 第二步检查防火墙。\n\n然后重启服务。再重试一次。最后看结果。希望对你有帮助！"
CLEAN_REPLY = "连接超时通常是防火墙拦住了 5432 端口。先检查安全组规则，再从应用所在机器测试端口。"


def run(event, env=None):
    merged = dict(os.environ)
    merged.pop("JIANMING_ZHONGWEN_LINT_EXCLUDE", None)
    merged.pop("CLAUDE_CONFIG_DIR", None)
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True, env=merged, timeout=30
    )


def post_event(path):
    return {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(path)}}


class LintHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_violating_markdown_is_reported_with_exit_2(self):
        r = run(post_event(self.write("doc.md", SLOP)))
        self.assertEqual(r.returncode, 2, r)
        self.assertIn("简明技术中文", r.stderr)
        self.assertIn("弱动词", r.stderr)

    def test_clean_markdown_exits_0(self):
        r = run(post_event(self.write("doc.md", CLEAN)))
        self.assertEqual(r.returncode, 0, r)
        self.assertEqual(r.stderr, "")

    def test_english_markdown_is_ignored(self):
        english = "## 0.1.0, 2026-09-09\n\n- First version with a document register and a reply register, a linter, hooks, and a benchmark command that runs inside Claude Code.\n"
        r = run(post_event(self.write("CHANGELOG.md", english)))
        self.assertEqual(r.returncode, 0, r)

    def test_non_markdown_is_ignored(self):
        r = run(post_event(self.write("doc.py", SLOP)))
        self.assertEqual(r.returncode, 0, r)

    def test_claude_config_dir_is_skipped(self):
        p = self.write("cfg/memory.md", SLOP)
        r = run(post_event(p), env={"CLAUDE_CONFIG_DIR": str(self.dir / "cfg")})
        self.assertEqual(r.returncode, 0, r)

    def test_dot_claude_component_is_skipped(self):
        p = self.write(".claude/agent-memory/MEMORY.md", SLOP)
        r = run(post_event(p))
        self.assertEqual(r.returncode, 0, r)

    def test_exclude_glob_is_honored(self):
        p = self.write("notes/todo.md", SLOP)
        r = run(post_event(p), env={"JIANMING_ZHONGWEN_LINT_EXCLUDE": str(self.dir / "notes" / "*")})
        self.assertEqual(r.returncode, 0, r)

    def test_stop_reports_a_bad_reply(self):
        r = run({"hook_event_name": "Stop", "last_assistant_message": BAD_REPLY})
        self.assertEqual(r.returncode, 0, r)
        out = json.loads(r.stdout)
        self.assertIn("systemMessage", out)
        for word in ("破折号", "列表项", "开场白", "结束语"):
            self.assertIn(word, out["systemMessage"])

    def test_stop_stays_silent_on_a_clean_reply(self):
        r = run({"hook_event_name": "Stop", "last_assistant_message": CLEAN_REPLY})
        self.assertEqual(r.returncode, 0, r)
        self.assertEqual(r.stdout, "")

    def test_garbage_stdin_exits_0(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r)


if __name__ == "__main__":
    unittest.main()
