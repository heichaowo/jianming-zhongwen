#!/usr/bin/env python3
"""Deterministic violation counter for 简明技术中文 (jianming-zhongwen).

Counts the mechanical violations a regex can find in Chinese technical text:
sentence and clause length, weak verbs, marked passives, banned modals,
semicolons, dashes, ordinal chains, "不是 X 而是 Y", 的 chains, slop words,
synonym rotation. reader_check() counts what a reader sees in a chat reply.

Known ceiling: a regex pass, not a parser. It cannot see meaning. A 被 passive
with an unknown agent is legal and still counted. Numbers are comparable
between two texts run through the same version. They are not a verdict.

Usage:
  python3 jm_lint.py --type procedural file.md
  cat text.md | python3 jm_lint.py --type descriptive -
  python3 jm_lint.py --type reply reply.txt
  python3 jm_lint.py --type descriptive --lengths file.md   # sentence lengths, for calibration
  python3 jm_lint.py --self-test
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SLOP_TSV = ROOT / "skills" / "jianming-zhongwen" / "references" / "slop-zh.tsv"

CJK_ALNUM = re.compile(r"[㐀-䶿一-鿿豈-﫿A-Za-z0-9]")
LIMITS = {"procedural": 30, "descriptive": 45}
CLAUSE_LIMIT = 40
REPLY_CAP = 5

# A weak verb counts only when a verbal noun follows it. 进行中, 进行到, 进行的 do not count.
VERBAL_NOUNS = (
    "处理|分析|检查|配置|调整|修改|验证|校验|测试|部署|更新|升级|设置|优化|评估|研究|改进|"
    "操作|管理|讨论|说明|解决|排查|清理|备份|迁移|同步|监控|审核|统计|计算|比较|确认|判断|"
    "梳理|整理|开发|设计|重构|安装|卸载|编译|构建|发布|回滚|扩容|缩容|加密|解密|压缩|解压|"
    "导入|导出|转换|复制|删除|创建|读取|写入|扫描|过滤|排序|拆分|合并|替换|标记|记录|输出|"
    "输入|加载|存储|缓存|调用|封装|拦截|注册|绑定|解析|渲染|匹配|校对|核对|审查|评审|沟通|"
    "协调|规划|培训|考核|巡检|维护|修复|排除|响应|反馈|上报|采集|抽样|建模|训练|推理"
)
WEAK_VERB = re.compile(
    r"(?:进行|作出|做出|予以|加以|开展|实施)(?!中|时|到|的|得)[^，。！？；：\n]{0,10}?(?:" + VERBAL_NOUNS + r")"
    r"|开展[^，。！？；：\n]{0,10}?工作"
)
PASSIVE = re.compile(r"被(?!动|告|子|褥|迫|选|除|乘)[一-鿿]{1,6}")
BANNED_MODAL = re.compile(r"应该|应当|最好|尽量|务必|不宜|(?<![便适事权相时合得])宜(?=[采用先按避在选择于])")
SEMICOLON = re.compile(r"[;；]")
DASH = re.compile(r"—+|(?<= )--(?= )")
ORDINAL = re.compile(r"首先|其次|再次|再者|最后|第一[，,、]|第二[，,、]|第三[，,、]")
NOT_X_BUT_Y = re.compile(r"不是[^，。！？；\n]{1,20}[，,]?\s*而是|不仅(?:仅)?[^，。！？；\n]{1,20}[，,]?\s*(?:更|还)")
DE_CHAIN = re.compile(r"的[^的，。！？；：\n]{1,12}的[^的，。！？；：\n]{1,12}的")
ROTATION_SETS = [
    ("配置-设置", re.compile(r"配置|设置")),
    ("目录-文件夹", re.compile(r"目录|文件夹")),
    ("点击-单击", re.compile(r"点击|单击")),
    ("登录-登陆", re.compile(r"登录|登陆")),
]
# Patterns that a literal word list cannot hold. slop-zh.tsv holds the literal terms.
SLOP_PATTERNS = [
    r"随着[^，。！？；\n]{1,12}的(?:不断|快速|迅速)?发展",
    r"在(?:当今|这个|如今)[^，。！？；\n]{0,10}(?:时代|社会|背景下)",
]
SLOP_CORE = [
    "值得注意的是", "需要指出的是", "值得一提的是", "不难发现", "众所周知", "毋庸置疑", "综上所述",
    "总的来说", "总而言之", "至关重要", "举足轻重", "深远影响", "不可磨灭", "前所未有", "赋能", "抓手",
    "闭环", "一站式", "全链路", "底层逻辑", "颗粒度", "降本增效", "助力", "打造", "无缝", "颠覆性",
    "沉淀", "拥抱变化", "让我们一起",
]


def slop_pattern() -> re.Pattern[str]:
    """Alternation of the TSV terms (term TAB source TAB swap) plus the core list and the regex patterns."""
    terms = list(SLOP_CORE)
    if SLOP_TSV.exists():
        for line in SLOP_TSV.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            term = line.split("\t")[0].strip()
            if term:
                terms.append(term)
    seen: dict[str, None] = {}
    for t in terms:
        seen.setdefault(t, None)
    alts = sorted((re.escape(t) for t in seen), key=len, reverse=True)
    return re.compile("|".join(alts + SLOP_PATTERNS))


SLOP = slop_pattern()

OPEN = {"（": "）", "(": ")", "「": "」", "『": "』", "“": "”", "《": "》", "【": "】", "[": "]"}
CLOSE = set(OPEN.values())
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)、]|[一二三四五六七八九十]+[、.．])[ \t]+(.*?)[ \t]*$", re.M)
TERMINAL = re.compile(r"[。！？!?：:]$")


def char_count(text: str) -> int:
    """汉字 and Latin letters and digits count 1 each. Punctuation and spaces count 0."""
    return len(CJK_ALNUM.findall(text))


def strip_code(text: str) -> str:
    text = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", " ", text, count=1, flags=re.S)  # YAML frontmatter is metadata, not prose
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", "X", text)  # one code span counts as one character
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"^#{1,6}\s.*$", " ", text, flags=re.M)  # headings are titles, exempt
    text = re.sub(r"https?://\S+", "U", text)
    text = re.sub(r"^\s*\|[\s:|-]+\|\s*$", " ", text, flags=re.M)  # table separator rows
    text = re.sub(
        r"^\s*\|(.*)\|\s*$",
        lambda m: "。".join(c.strip() for c in m.group(1).split("|") if c.strip()) + "。",
        text,
        flags=re.M,
    )  # each cell is its own unit, still linted
    return text


def sentences(text: str, min_chars: int = 2) -> list[str]:
    """Split at 。！？ outside brackets and quotes, and at line ends. List items are their own units."""
    text = LIST_ITEM.sub(lambda m: m.group(1) + ("" if TERMINAL.search(m.group(1)) else "。"), text)
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in text:
        after_terminal = bool(buf) and buf[-1] in "。！？!?"
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth = max(0, depth - 1)
        buf.append(ch)
        # A closing quote or bracket right after 。 ends the outer sentence too (GB/T 15834: 句末点号在引号内).
        if (ch in "。！？!?" and depth == 0) or ch == "\n" or (ch in CLOSE and depth == 0 and after_terminal):
            out.append("".join(buf))
            buf = []
    if buf:
        out.append("".join(buf))
    return [s.strip() for s in out if char_count(s) >= min_chars]


def clauses(sentence: str) -> list[str]:
    return [c for c in re.split(r"[，,；;：:]", sentence) if char_count(c) >= 2]


def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def lint(text: str, text_type: str) -> dict:
    body = strip_code(text)
    sents = sentences(body)
    lengths = [char_count(s) for s in sents]
    limit = LIMITS[text_type]
    counts: dict[str, int] = {}
    counts["sentence_over_limit"] = sum(1 for n in lengths if n > limit)
    counts["clause_over_limit"] = sum(1 for s in sents for c in clauses(s) if char_count(c) > CLAUSE_LIMIT)
    counts["weak_verb"] = len(WEAK_VERB.findall(body))
    counts["passive_marked"] = len(PASSIVE.findall(body))
    counts["banned_modal"] = len(BANNED_MODAL.findall(body))
    counts["semicolon"] = len(SEMICOLON.findall(body))
    counts["dash_join"] = len(DASH.findall(body))
    counts["ordinal_chain"] = sum(1 for p in paragraphs(body) if len(ORDINAL.findall(p)) >= 2)
    counts["not_x_but_y"] = len(NOT_X_BUT_Y.findall(body))
    counts["de_chain"] = sum(len(DE_CHAIN.findall(s)) for s in sents)
    counts["slop_word"] = len(SLOP.findall(body))
    rotation = 0
    for _, rx in ROTATION_SETS:
        members = set(rx.findall(body))
        if len(members) > 1:
            rotation += len(members) - 1
    counts["synonym_rotation"] = rotation
    chars = max(1, char_count(body))
    total = sum(counts.values())
    return {
        "type": text_type,
        "chars": chars,
        "sentences": len(sents),
        "mean_sentence_chars": round(sum(lengths) / max(1, len(lengths)), 1),
        "longest_sentence_chars": max(lengths, default=0),
        "lengths": lengths,
        "violations": counts,
        "violations_total": total,
        "violations_per_1000": round(1000.0 * total / chars, 2),
    }


BOLD = re.compile(r"\*\*[^*\n]+\*\*")
HEADER = re.compile(r"^#{1,6}\s", re.M)
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)、])\s", re.M)
OPENER = re.compile(
    r"^\s*[*_]*(?:好的|当然|没问题|您好|你好|感谢(?:您|你)?(?:的)?提问|很高兴|这是(?:一)?个(?:很|非常)?好的问题|"
    r"关于(?:您|你)(?:的|提到的|提出的)?问题)"
)
CLOSER = re.compile(
    r"希望(?:这|以上|这些|本|这个)?(?:回答|解释|信息|内容|说明)?(?:对|能)(?:你|您)?(?:有(?:所)?)?帮助|"
    r"如(?:果)?(?:有|还有)(?:其他|任何|别的|更多)?(?:问题|疑问)|请随时|欢迎(?:继续|随时)|祝(?:你|您)"
)


def reader_check(text: str) -> dict:
    """What a reader sees in a chat reply. Every sentence counts, list items and table rows included."""
    text = text.replace("\r\n", "\n")
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    prose = re.sub(r"`[^`\n]+`", "X", prose)
    prose_no_md = re.sub(r"^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)、]\s|\|)", "", prose, flags=re.M)
    prose_no_md = re.sub(r"^\s*[\s:|-]+$", "", prose_no_md, flags=re.M)  # table separator rows
    sents = sentences(prose_no_md, min_chars=4)
    counts = {
        "sentences": len(sents),
        "over_cap": max(0, len(sents) - REPLY_CAP),
        "em_dash": len(DASH.findall(prose)),
        "bold_spans": len(BOLD.findall(prose)),
        "headers": len(HEADER.findall(prose)),
        "bullets": len(BULLET.findall(prose)),
        "opener": int(bool(OPENER.search(prose))),
        "closer": int(bool(CLOSER.search(prose))),
    }
    visible = counts["over_cap"] + counts["em_dash"] + counts["bold_spans"] + counts["headers"] + counts["bullets"]
    return {
        "type": "reply",
        "chars": max(1, char_count(prose_no_md)),
        "counts": counts,
        "visible_total": visible,
        "under_cap": counts["over_cap"] == 0,
    }


SLOP_FIXTURE = """首先，我们需要对系统架构进行全面的性能分析，以便对当前存在的各类瓶颈问题作出准确的评估，从而确定下一步的优化方向；这一步至关重要。值得注意的是，相关的配置应该尽量在部署前予以处理，否则会对用户体验产生深远影响——尤其是高并发场景。其次，请求被网关拒绝了之后，系统会自动重试。最后，综上所述，建议通过赋能各团队打造一站式的整体解决方案，实现从检查到保存的闭环。这个方案不是简单的修补，而是架构层面的重构。用户的配置文件的默认设置的路径也要更新。"""

CLEAN_FIXTURE = """运行 `datasync run --config datasync.yaml` 启动同步。
如果同步失败，查看日志文件。
必须在部署前备份数据库。备份完成后，系统自动重连。

同步过程分三步：

- 读取 MySQL 表
- 转换为 Parquet
- 上传到 OSS
"""

REPLY_FIXTURE = """好的，这是个很好的问题——让我来解释。

## 原因分析
- 连接超时说明网络有问题。
- **检查**防火墙配置。

先看日志。然后重试。如果还不行，重启服务。综上所述，问题出在网络层，希望对你有帮助！"""

CLEAN_REPLY_FIXTURE = """Pod 因为内存超过容器限制被终止（OOMKilled，即内存溢出被杀）。把 `resources.limits.memory` 调高，或者用 `kubectl top pod` 找出内存峰值。"""

TABLE_FIXTURE = """| 列 A | 列 B |
|---|---|
| 你应该重启服务 | 正常 |
"""


def self_test() -> None:
    slop = lint(SLOP_FIXTURE, "descriptive")
    v = slop["violations"]
    assert v["sentence_over_limit"] >= 1, slop
    assert v["weak_verb"] >= 3, slop
    assert v["banned_modal"] >= 2, slop
    assert v["semicolon"] == 1, slop
    assert v["dash_join"] == 1, slop
    assert v["ordinal_chain"] == 1, slop
    assert v["not_x_but_y"] == 1, slop
    assert v["passive_marked"] == 1, slop
    assert v["slop_word"] >= 6, slop
    assert v["de_chain"] == 1, slop
    assert v["synonym_rotation"] == 1, slop

    clean = lint(CLEAN_FIXTURE, "procedural")
    assert clean["violations_total"] == 0, clean

    # Sentence boundaries: brackets, list items, code spans, table cells.
    assert sentences("请看说明（如图 1）。然后继续。") == ["请看说明（如图 1）。", "然后继续。"]
    assert len(sentences("注意（例如：先备份。再部署。）。然后继续。")) == 2  # 。 inside brackets does not split
    assert sentences("他说：“重启。”然后继续。") == ["他说：“重启。”", "然后继续。"]
    assert sentences("- 第一项\n- 第二项") == ["第一项。", "第二项。"]
    assert char_count(strip_code("运行 `datasync run` 命令")) == 5
    cell = lint(TABLE_FIXTURE, "descriptive")["violations"]
    assert cell["banned_modal"] == 1 and cell["sentence_over_limit"] == 0, cell
    assert lint("一" * 50 + "。", "descriptive")["violations"]["sentence_over_limit"] == 1
    assert lint("一" * 45 + "，好。", "descriptive")["violations"]["clause_over_limit"] == 1
    assert lint("# 这是一个很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长的标题\n", "procedural")["violations"]["sentence_over_limit"] == 0
    front = "---\ndescription: " + "长" * 60 + "\n---\n\n运行命令。\n"
    assert lint(front, "procedural")["violations"]["sentence_over_limit"] == 0  # frontmatter exempt

    # Weak verbs: verbal noun required. 进行中 is not a hit.
    assert WEAK_VERB.search("进行部署") and WEAK_VERB.search("对日志进行全面的分析") and WEAK_VERB.search("开展相关工作")
    assert not WEAK_VERB.search("进行中的任务") and not WEAK_VERB.search("正在进行的会议")

    # Modals: 便宜 and 事宜 are not the modal 宜.
    assert not BANNED_MODAL.search("价格便宜，相关事宜另议")
    assert BANNED_MODAL.search("宜采用短句") and BANNED_MODAL.search("不宜过长") and BANNED_MODAL.search("你应该重启")

    # Passives: 被动 is a noun, 被删除 is a marked passive.
    assert not PASSIVE.search("被动模式") and PASSIVE.search("文件被删除了")

    # 的 chains: three 的 in a row is a hit, two is not.
    assert DE_CHAIN.search("服务器端的连接池的超时时间的默认值") and not DE_CHAIN.search("用于管理用户权限的配置文件")

    # Ordinal chains are per paragraph.
    assert lint("首先备份。其次部署。", "procedural")["violations"]["ordinal_chain"] == 1
    assert lint("首先备份。\n\n其次部署。", "procedural")["violations"]["ordinal_chain"] == 0

    # Reply register.
    r = reader_check(REPLY_FIXTURE)
    c = r["counts"]
    assert c["opener"] == 1 and c["closer"] == 1, c
    assert c["em_dash"] == 1 and c["headers"] == 1 and c["bullets"] == 2 and c["bold_spans"] == 1, c
    assert c["sentences"] >= 7 and c["over_cap"] >= 2, c
    assert r["visible_total"] >= 7, r
    ok = reader_check(CLEAN_REPLY_FIXTURE)
    assert ok["visible_total"] == 0 and ok["under_cap"] and ok["counts"]["sentences"] == 2, ok
    tricky = "他说“重启。”然后（它坏了。）都好了。\n\n```\n# 不是标题\n**不是加粗**\n- 不是列表\n```\n"
    t = reader_check(tricky)["counts"]
    assert (t["sentences"], t["headers"], t["bold_spans"], t["bullets"]) == (2, 0, 0, 0), t
    print("self-test OK:", slop["violations_total"], "violations in slop fixture, 0 in clean")


USAGE = "usage: jm_lint.py [--type procedural|descriptive|reply] [--gate] [--lengths] (FILE|-) | --self-test"


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        self_test()
        return 0
    gate = "--gate" in args
    if gate:
        args.remove("--gate")
    lengths = "--lengths" in args
    if lengths:
        args.remove("--lengths")
    text_type = "descriptive"
    if "--type" in args:
        i = args.index("--type")
        if i + 1 >= len(args):
            sys.exit("missing value after --type\n" + USAGE)
        text_type = args[i + 1]
        del args[i:i + 2]
    if text_type != "reply" and text_type not in LIMITS:
        sys.exit("unknown --type %r (expected procedural, descriptive or reply)\n%s" % (text_type, USAGE))
    if len(args) != 1:
        sys.exit(USAGE)
    src = args[0]
    if src == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(src, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as err:
            sys.exit(str(err))
    report = reader_check(text) if text_type == "reply" else lint(text, text_type)
    if not lengths and "lengths" in report:
        del report["lengths"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    total = report["visible_total"] if text_type == "reply" else report["violations_total"]
    return 1 if gate and total else 0


if __name__ == "__main__":
    sys.exit(main())
