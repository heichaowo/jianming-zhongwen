#!/usr/bin/env python3
"""Recompute every published number from the raw files and compare it with the README.

Run it before you push. CI runs it on every push and pull request.

    python3 evals/check_numbers.py            # exit 1 on the first mismatch
    python3 evals/check_numbers.py --print    # show the recomputed values

Checks:
- The version string in SKILL.md, the two manifests, and the README badge.
- The rule block: prompts/system-prompt.md and output-styles/jianming-zhongwen.md
  carry the same text, and SKILL.md carries the same reply rules.
- README benchmark numbers against the run named by the README marker
  `<!-- numbers-from: evals/results/<run> -->`. Without the marker, or with an
  empty run directory, the number check is skipped and says so. That is a
  bootstrap guard for the first releases, not permanent logic.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import score_text_dir  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")
problems = []


def expect(label, text, pattern, value):
    """The number in the text must equal the recomputed value."""
    m = re.search(pattern, text)
    found = m.group(1) if m else None
    if found != str(value):
        problems.append(f"{label}: text says {found!r}, raw files give {value!r}")


def rule_block(text):
    """The text between the first two --- lines, or the body after the frontmatter."""
    parts = re.split(r"^---[ \t]*$", text, flags=re.M)
    return parts[1].strip() if len(parts) >= 3 else text.strip()


def sync():
    prompt = rule_block((ROOT / "prompts" / "system-prompt.md").read_text(encoding="utf-8"))
    style = (ROOT / "output-styles" / "jianming-zhongwen.md").read_text(encoding="utf-8")
    style = re.sub(r"^---\n.*?\n---\n", "", style, count=1, flags=re.S).strip()
    if prompt != style:
        problems.append("rule block differs between prompts/system-prompt.md and output-styles/jianming-zhongwen.md")
    skill = (ROOT / "skills" / "jianming-zhongwen" / "SKILL.md").read_text(encoding="utf-8")
    for phrase in ("最多 5 句", "第一句给答案", "不用破折号", "条件在前", "一词一义", "不动", "必须 / 不得", "不超过 30 字", "不超过 50 字"):
        for name, text in (("SKILL.md", skill), ("prompts/system-prompt.md", prompt)):
            if phrase not in text:
                problems.append(f"{name} lacks the rule phrase {phrase!r}")


def versions():
    v = {}
    skill = (ROOT / "skills" / "jianming-zhongwen" / "SKILL.md").read_text(encoding="utf-8")
    v["SKILL.md"] = re.search(r'version: "([^"]+)"', skill).group(1)
    v[".claude-plugin/plugin.json"] = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    v[".claude-plugin/marketplace.json"] = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][0]["version"]
    badge = re.search(r"badge/version-([0-9.]+)-", README)
    v["README badge"] = badge.group(1) if badge else None
    if len(set(v.values())) != 1:
        problems.append(f"version strings differ: {v}")
    return v


def numbers(show):
    marker = re.search(r"<!--\s*numbers-from:\s*(\S+)\s*-->", README)
    if not marker:
        print("数字校验跳过：README 没有 numbers-from 标记（引导期）")
        return
    run = ROOT / marker.group(1)
    s = score_text_dir.summary(run)
    if not s["replies"] and not s["docs"]:
        print(f"数字校验跳过：{run} 没有 raw 文件（引导期）")
        return
    if show:
        print(score_text_dir.render(s))
    r = s["replies"]
    if "baseline" in r and "skill" in r:
        base, skill = r["baseline"], r["skill"]
        pct = score_text_dir.reduction(base["visible"], skill["visible"])
        expect("README reply visible", README, r"从 (\d+ 降到 \d+)", f"{base['visible']} 降到 {skill['visible']}")
        expect("README reply pct", README, r"降到 \d+，少 (\d+)%", pct)
        expect("README under cap", README, r"5 句以内的回复 (\d+/\d+ 对 \d+/\d+)",
               f"{base['under_cap']}/{base['n']} 对 {skill['under_cap']}/{skill['n']}")
        for cond, label in (("baseline", "无 skill"), ("skill", "skill")):
            d = r[cond]
            n = max(1, d["n"])
            expect(f"README reply row {cond}", README,
                   rf"\| {label} \| (\d+ \| [\d.]+ \| \d+ \| \d+ \| \d+ \| \d+) \|",
                   f"{round(d['chars'] / n)} | {d['sentences'] / n:.1f} | {d['em_dash']} | {d['bold']} | {d['headers']} | {d['bullets']}")
    d = s["docs"]
    if "baseline" in d and "skill" in d:
        pct = score_text_dir.reduction(d["baseline"]["per_1000"], d["skill"]["per_1000"])
        expect("README docs", README, r"每千字违规数 ([\d.]+ 对 [\d.]+)", f"{d['baseline']['per_1000']:.2f} 对 {d['skill']['per_1000']:.2f}")
        expect("README docs pct", README, r"每千字违规数 [\d.]+ 对 [\d.]+，少 (\d+)%", pct)
    if s["judge"]:
        j = s["judge"]
        expect("README judge", README, r"skill 胜 (\d+，平 \d+，负 \d+)", f"{j['wins']}，平 {j['ties']}，负 {j['losses']}")


def main():
    show = "--print" in sys.argv
    v = versions()
    if show:
        print("versions:", v)
    sync()
    numbers(show)
    if problems:
        print("MISMATCH")
        for p in problems:
            print(" -", p)
        return 1
    print("check_numbers OK: versions and rule blocks agree, published numbers match the raw files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
