#!/usr/bin/env python3
"""Tests for activate.py: the rule-block extraction and the hook as a subprocess."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import activate  # noqa: E402


class ActivateTest(unittest.TestCase):
    def test_rule_block_returns_the_text_between_the_first_two_fences(self):
        page = "# 标题\n\n说明段落。\n\n---\n\n规则一。\n规则二。\n\n---\n\n## 短版本\n\n短。\n"
        self.assertEqual(activate.rule_block(page).strip(), "规则一。\n规则二。")

    def test_rule_block_returns_everything_without_a_fence(self):
        self.assertEqual(activate.rule_block("只有规则。"), "只有规则。")

    def test_strip_frontmatter_removes_a_yaml_block_at_the_top(self):
        self.assertEqual(activate.strip_frontmatter("---\nname: x\n---\n正文"), "正文")
        self.assertEqual(activate.strip_frontmatter("正文"), "正文")

    def test_the_real_prompt_file_builds_a_payload_under_the_cap(self):
        text = activate.read_first_file(activate.prompt_candidates(None))
        self.assertTrue(text, "prompts/system-prompt.md not found")
        out = activate.build_context(text)
        for phrase in ("最多 5 句", "必须", "不超过 30 字"):
            self.assertIn(phrase, out)
        self.assertNotIn("短版本", out, "the short variant must stay out of the payload")
        self.assertLessEqual(len(out), activate.MAX_CHARS)

    def test_an_empty_prompt_file_gives_the_fallback(self):
        self.assertEqual(activate.build_context(""), activate.FALLBACK_CONTEXT)

    def test_an_oversized_payload_gives_the_fallback(self):
        # A title line first, so the fences read as the rule block and not as YAML frontmatter.
        big = "# 标题\n\n---\n" + "字" * (activate.MAX_CHARS + 10) + "\n---\n"
        self.assertEqual(activate.build_context(big), activate.FALLBACK_CONTEXT)

    def test_read_first_file_skips_missing_candidates(self):
        self.assertEqual(activate.read_first_file(["/nonexistent/a.md", "/nonexistent/b.md"]), "")

    def test_the_hook_prints_the_header_and_the_rules(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(HERE.parent.parent))
        r = subprocess.run([sys.executable, str(HERE / "activate.py")], capture_output=True, env=env, timeout=30)
        out = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.startswith(activate.HEADER))
        self.assertIn("最多 5 句", out)


if __name__ == "__main__":
    unittest.main()
