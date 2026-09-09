#!/usr/bin/env python3
"""Score one benchmark run and print the tables that the README and RESULTS.md carry.

A run directory holds up to three subdirectories written by /jianming-zhongwen:bench:

    docs/    <condition>__<scenario>.txt   scored with jm_lint.lint, type from scenarios.json
    reply1/  <condition>__<scenario>.txt   scored with jm_lint.reader_check
    reply2/  same, second run; reply1 and reply2 are pooled
    judge/   <scenario>.json               blind pairwise verdicts, both orders

    python3 evals/score_text_dir.py evals/results/run-2026-09-10
    python3 evals/score_text_dir.py evals/results/run-2026-09-10 --json

Conditions are the file-name prefixes. "baseline" is the reference for the
reduction columns. Sentence-length percentiles of the baseline documents are
printed for the calibration protocol in docs/design.md section 2.7.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jm_lint  # noqa: E402

SCEN = {s["id"]: s for s in json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))}


def read(path):
    text = path.read_text(encoding="utf-8")
    return text if text.strip() else None


def percentile(values, p):
    if not values:
        return 0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1)))))
    return ordered[k]


def score_docs(run):
    """Per condition: n, chars, violations, per 1000, and sentence lengths by type."""
    out = {}
    for f in sorted((run / "docs").glob("*.txt")) if (run / "docs").is_dir() else []:
        cond, sid = f.stem.split("__", 1)
        text = read(f)
        if text is None or sid not in SCEN:
            continue
        r = jm_lint.lint(text, SCEN[sid]["type"])
        d = out.setdefault(cond, {"n": 0, "chars": 0, "viol": 0, "lengths": {"procedural": [], "descriptive": []}})
        d["n"] += 1
        d["chars"] += r["chars"]
        d["viol"] += r["violations_total"]
        d["lengths"][SCEN[sid]["type"]].extend(r["lengths"])
    for d in out.values():
        d["per_1000"] = round(1000.0 * d["viol"] / max(1, d["chars"]), 2)
    return out


def score_replies(run):
    """Per condition, pooled over reply1 and reply2: the reader-visible counts."""
    out = {}
    for sub in ("reply1", "reply2"):
        if not (run / sub).is_dir():
            continue
        for f in sorted((run / sub).glob("*.txt")):
            cond = f.stem.split("__", 1)[0]
            text = read(f)
            if text is None:
                continue
            r = jm_lint.reader_check(text)
            c = r["counts"]
            d = out.setdefault(cond, {"n": 0, "chars": 0, "sentences": 0, "under_cap": 0, "em_dash": 0,
                                      "bold": 0, "headers": 0, "bullets": 0, "openers": 0, "closers": 0, "visible": 0})
            d["n"] += 1
            d["chars"] += r["chars"]
            d["sentences"] += c["sentences"]
            d["under_cap"] += int(r["under_cap"])
            d["em_dash"] += c["em_dash"]
            d["bold"] += c["bold_spans"]
            d["headers"] += c["headers"]
            d["bullets"] += c["bullets"]
            d["openers"] += c["opener"]
            d["closers"] += c["closer"]
            d["visible"] += r["visible_total"]
    return out


def score_judge(run):
    """Votes for the skill condition over both orders: wins, ties, losses."""
    wins = ties = losses = 0
    if not (run / "judge").is_dir():
        return None
    for f in sorted((run / "judge").glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for order in ("order1", "order2"):
            o = data.get(order) or {}
            w = o.get("winner")
            if w == "tie":
                ties += 1
            elif w in ("A", "B") and o.get(w) == "skill":
                wins += 1
            elif w in ("A", "B"):
                losses += 1
    return {"wins": wins, "ties": ties, "losses": losses}


def reduction(base, value):
    return round(100 * (base - value) / base) if base else 0


def summary(run):
    return {"docs": score_docs(run), "replies": score_replies(run), "judge": score_judge(run)}


def render(s):
    lines = []
    replies = s["replies"]
    if replies:
        lines.append("| 条件 | n | 字数 | 句数 | 5 句以内 | 破折号 | 加粗 | 标题 | 列表项 | 开场白 | 结束语 | 可见缺陷 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for cond, d in replies.items():
            n = max(1, d["n"])
            lines.append(f"| {cond} | {d['n']} | {round(d['chars'] / n)} | {d['sentences'] / n:.1f} | {d['under_cap']}/{d['n']} | "
                         f"{d['em_dash']} | {d['bold']} | {d['headers']} | {d['bullets']} | {d['openers']} | {d['closers']} | {d['visible']} |")
        base = replies.get("baseline")
        if base:
            for cond, d in replies.items():
                if cond != "baseline":
                    lines.append(f"\n{cond} 的可见缺陷比 baseline 少 {reduction(base['visible'], d['visible'])}%（{base['visible']} → {d['visible']}）。")
    docs = s["docs"]
    if docs:
        lines.append("\n| 条件 | n | 字数 | 违规 | 每千字违规 | 比 baseline 少 |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        base = docs.get("baseline")
        for cond, d in docs.items():
            red = "" if cond == "baseline" or not base else f"{reduction(base['per_1000'], d['per_1000'])}%"
            lines.append(f"| {cond} | {d['n']} | {d['chars']} | {d['viol']} | {d['per_1000']:.2f} | {red} |")
        if base:
            lines.append("\n基线句长分布（校准用，单位字）：")
            lines.append("\n| 类型 | 句数 | P50 | P70 | P90 | 最长 |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for t in ("procedural", "descriptive"):
                v = base["lengths"][t]
                lines.append(f"| {t} | {len(v)} | {percentile(v, 50)} | {percentile(v, 70)} | {percentile(v, 90)} | {max(v, default=0)} |")
    if s["judge"]:
        j = s["judge"]
        lines.append(f"\n评委盲测（两种顺序各一票）：skill 胜 {j['wins']}，平 {j['ties']}，负 {j['losses']}。")
    if not lines:
        lines.append("目录里没有可打分的文件。")
    return "\n".join(lines)


def main(argv):
    if not argv:
        sys.exit("usage: score_text_dir.py RUN_DIR [--json]")
    run = pathlib.Path(argv[0])
    s = summary(run)
    if "--json" in argv:
        for d in s["docs"].values():
            d.pop("lengths", None)
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        print(render(s))


if __name__ == "__main__":
    main(sys.argv[1:])
