#!/usr/bin/env python3
"""SessionStart hook: write the document rules from prompts/system-prompt.md to stdout as plain text.

The reply register (the paragraphs that start with 回复（) is left out: it applies
only through the jianming-zhongwen output style or the skill.

Claude Code caps hook stdout at about 10,000 characters. Above that the output
is written to a file and replaced by a preview, which defeats the hook, so the
payload is capped at MAX_CHARS and a fixed short rule set is the fallback.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")  # Chinese output on Windows without a shell variable

MAX_CHARS = 9500

FALLBACK_CONTEXT = """简明技术中文规则已自动加载

技术写作按简明技术中文的规则：短句，实义动词，条件在前，情态词只用 必须 / 建议 / 可以 / 能 / 可能，一词一义，不动代码、命令和报错原文。"""

HEADER = "\n".join(
    [
        "简明技术中文规则已自动加载",
        "",
        "不用等用户点名，写文档时直接按下面的规则写。完整规则和检查模式在本插件的 skills/jianming-zhongwen/SKILL.md，做检查时读它。",
        "下面只有文档规则。回复规则只在选了输出样式 jianming-zhongwen 或点名这个 skill 时生效，平时的回复不受它约束。",
        "",
    ]
)

FENCE = re.compile(r"^---[ \t]*\r?$", re.MULTILINE)
FRONTMATTER = re.compile(r"^---\r?\n[\s\S]*?\r?\n---\r?\n?")

HERE = pathlib.Path(__file__).resolve().parent


def prompt_candidates(plugin_root, hook_directory=HERE):
    roots = [pathlib.Path(plugin_root)] if plugin_root else []
    roots += [hook_directory.parent.parent, hook_directory.parent]
    return [root / "prompts" / "system-prompt.md" for root in roots]


def read_first_file(candidates):
    for candidate in candidates:
        try:
            return pathlib.Path(candidate).read_text(encoding="utf-8")
        except OSError:  # missing, unreadable, or a directory: try the next one
            continue
    return ""


def strip_frontmatter(content):
    return FRONTMATTER.sub("", content, count=1)


# prompts/system-prompt.md is a page for people: a title, a paragraph that says
# where to paste the block, the rule block between two "---" lines, then a
# short variant. The model gets the fenced block only.
def rule_block(content):
    fences = list(FENCE.finditer(content))
    if not fences:
        return content
    start = fences[0].end()
    end = fences[1].start() if len(fences) > 1 else len(content)
    return content[start:end]


def document_rules(block):
    """Drop the reply register: it applies only through the output style or the skill."""
    return "\n\n".join(p for p in block.strip().split("\n\n") if not p.startswith("回复（"))


def build_context(prompt_text):
    if not prompt_text:
        return FALLBACK_CONTEXT
    out = HEADER + document_rules(rule_block(strip_frontmatter(prompt_text)))
    if len(out) > MAX_CHARS:
        print(
            f"jianming-zhongwen hook: payload is {len(out)} characters, over the {MAX_CHARS} cap; sending the fallback rules",
            file=sys.stderr,
        )
        return FALLBACK_CONTEXT
    return out


def main():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("PLUGIN_ROOT")
    sys.stdout.write(build_context(read_first_file(prompt_candidates(plugin_root))))


if __name__ == "__main__":
    main()
