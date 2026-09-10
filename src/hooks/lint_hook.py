#!/usr/bin/env python3
"""Advisory writing checks for Claude Code hooks. Never blocks.

PostToolUse (Write|Edit on a .md file): lint the file with evals/jm_lint.py
and, when it has violations, print a short summary to stderr and exit 2 so
the model sees it. Exit 2 on PostToolUse is advisory: the tool already ran.
Agent-internal Markdown, such as memory files under the Claude configuration
directory, is skipped. Set JIANMING_ZHONGWEN_LINT_EXCLUDE to skip more paths.

Stop: read `last_assistant_message`, skip it when under 30% of its counted
characters are Chinese, otherwise check the reply register (five sentences
or fewer with list items counted, no headers, bullets, bold, or dashes, no
opener or closer), and return a systemMessage only when the reply breaks it.
Always exit 0, so the session never loops.
"""
from __future__ import annotations

import fnmatch
import json
import os
import pathlib
import re
import sys

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")  # Chinese output on Windows without a shell variable

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "evals"))

CLAUDE_DIR = ".claude"
EXCLUDE_VAR = "JIANMING_ZHONGWEN_LINT_EXCLUDE"
LABELS = {
    "sentence_over_limit": "句子超长",
    "clause_over_limit": "分句超长",
    "weak_verb": "弱动词",
    "passive_marked": "被字句",
    "banned_modal": "禁用情态词",
    "semicolon": "分号",
    "dash_join": "破折号",
    "ordinal_chain": "首先其次链",
    "not_x_but_y": "不是而是",
    "de_chain": "的字链",
    "slop_word": "空洞词",
    "synonym_rotation": "同义词轮换",
}


def load_linter():
    try:
        import jm_lint  # noqa: WPS433
        return jm_lint
    except Exception:  # noqa: BLE001
        return None


def absolute(path, cwd=None):
    """Make the path absolute. The harness can send it relative to the session directory."""
    return pathlib.Path(cwd or ".", pathlib.Path(path).expanduser()).absolute()


def variants(path):
    """The path as written and the path with symlinks resolved. An exclusion matches either form."""
    return {pathlib.Path(os.path.normpath(path)), path.resolve()}


def excluded(target):
    """True for agent-internal Markdown and for the paths the user excludes."""
    config_dirs = variants(absolute(os.environ.get("CLAUDE_CONFIG_DIR") or f"~/{CLAUDE_DIR}"))
    raw = os.environ.get(EXCLUDE_VAR, "").split(os.pathsep)
    patterns = [os.path.expanduser(p) for p in raw if p]
    for form in variants(target):
        if CLAUDE_DIR in form.parts or any(form.is_relative_to(d) for d in config_dirs):
            return True
        if any(fnmatch.fnmatch(str(form), p) for p in patterns):
            return True
    return False


def is_chinese(lint, text):
    """True when at least 30% of the counted characters are Chinese."""
    counted = lint.CJK_ALNUM.findall(lint.strip_code(text))
    cjk = sum(1 for ch in counted if ord(ch) > 0x2E7F)
    return bool(counted) and cjk >= 0.3 * len(counted)


def chinese_paragraphs(lint, text):
    """Keep the paragraphs that are mostly Chinese. A bilingual README keeps its Chinese half."""
    return "\n\n".join(p for p in re.split(r"\n\s*\n", text) if is_chinese(lint, p))


def post_tool_use(event):
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".md"):
        return 0
    target = absolute(path, event.get("cwd"))
    if excluded(target):
        return 0
    lint = load_linter()
    if lint is None:
        return 0
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return 0
    text = chinese_paragraphs(lint, text)
    if not text:
        return 0  # an English file: the rules do not apply
    report = lint.lint(text, "descriptive")
    hits = {k: v for k, v in report["violations"].items() if v}
    if not hits:
        return 0
    summary = "，".join(f"{LABELS.get(k, k)} {v}" for k, v in hits.items())
    sys.stderr.write(
        f"简明技术中文：{target.name} 有 {report['violations_total']} 处违规（{summary}）。"
        f"改掉刚写的文件里的这些地方，再继续。\n"
    )
    return 2


def stop(event):
    reply = event.get("last_assistant_message") or ""
    lint = load_linter()
    if lint is None or not is_chinese(lint, reply):
        return 0
    c = lint.reader_check(reply)["counts"]
    problems = []
    if c["over_cap"]:
        problems.append(f"{c['sentences']} 句，列表项计入（上限 {lint.REPLY_CAP} 句）")
    for key, label in (("em_dash", "破折号"), ("bold_spans", "加粗"), ("headers", "标题"), ("bullets", "列表项")):
        if c[key]:
            problems.append(f"{c[key]} 处{label}")
    if c["opener"]:
        problems.append("开场白")
    if c["closer"]:
        problems.append("结束语")
    if problems:
        print(json.dumps({"systemMessage": "简明技术中文回复检查：" + "；".join(problems) + "。只用散文，最多 5 句，第一句给答案。"}, ensure_ascii=False))
    return 0


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    try:
        name = event.get("hook_event_name", "")
        if name == "PostToolUse":
            return post_tool_use(event)
        if name == "Stop":
            return stop(event)
    except Exception:  # noqa: BLE001  advisory hook: a crash must never block or loop the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
