# 简明技术中文 jianming-zhongwen

<p>
  <a href="skills/jianming-zhongwen/SKILL.md"><img src="https://img.shields.io/badge/version-0.1.0-blue?style=flat" alt="version 0.1.0"></a>
  <a href="https://github.com/heichaowo/jianming-zhongwen/actions/workflows/check.yml"><img src="https://github.com/heichaowo/jianming-zhongwen/actions/workflows/check.yml/badge.svg" alt="check"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat" alt="MIT"></a>
</p>

一个 Agent Skill，让模型用一遍就能读懂的中文写技术文档和回复。规则可数，能用正则查：程序性句子不超过 30 字，情态词只用五组，不用 进行 / 作出 加名词，回复最多 5 句。

规则来自中文自己的规范：余光中对欧化中文的批评，阮一峰的《中文技术文档的写作规范》，GB/T 1.1-2020 附录 C 的能愿动词分工，GB/T 15834-2011 的标点用法。AI 味只是第二层守卫，依据是 lieflat 语料和 CCL 2023 的实测数据。研究过程和每条决定的理由在 [docs/design.md](docs/design.md)。

工程结构仿照 [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)：自测、数字门、版本门、hook、marketplace。

## 安装

Claude Code 插件，带 hook 和输出样式：

```
/plugin marketplace add heichaowo/jianming-zhongwen
/plugin install jianming-zhongwen@jianming-zhongwen
```

更新：`/plugin` 界面里点更新，或者 `claude plugin update jianming-zhongwen@jianming-zhongwen`。

输出样式的名字是 `jianming-zhongwen:jianming-zhongwen`，在 `/config` 的 Output style 里选。

任何支持 SKILL.md 的工具：

```bash
npx skills add heichaowo/jianming-zhongwen
```

不支持 SKILL.md 的工具：把 [prompts/system-prompt.md](prompts/system-prompt.md) 里两条分隔线之间的规则块粘贴进系统提示、`AGENTS.md` 或 `.cursorrules`。页尾有一个 60 token 的短版本。

## 规则

文档，写或改写 README、操作手册、故障排查、报错文本、发布说明、事故报告时：

| 规则 | 它删掉什么 |
|---|---|
| 程序性每句不超过 30 字，描述性不超过 45 字，逗号分句不超过 40 字 | 一口气读不完的句子 |
| 用实义动词，不用 进行 / 作出 / 予以 / 加以 加名词 | 「对配置进行修改」 |
| 情态词按阶梯：必须 / 建议 / 可以 / 能 / 可能，各管一件事 | 「应该」到底是要求还是猜测 |
| 条件在前，动作在后 | 读者做完了才看到的「如果」 |
| 主动为主，被字句只在施事未知时用 | 「已经被处理了」 |
| 不用分号，不用破折号连接两个陈述，三个以上分句就拆句 | 流水句 |
| 一词一义，全文一致 | 配置、设置、参数轮着用 |
| 只说事实，不说重要性 | 值得注意的是、至关重要、赋能、闭环、「不是 X 而是 Y」 |
| 「的」字链不超过两层，名词化改回动词 | 「服务器端的连接池的超时时间的默认值」「可读性高」 |
| 格式为读者服务 | 加粗导语、emoji、两句话的标题、两项的列表 |

回复，每一条聊天回复：

| 规则 | 它删掉什么 |
|---|---|
| 只用散文，不用标题、列表、加粗、表格 | 围着一句答案的一堆格式 |
| 最多 5 句，列表项也算句 | 回答「严重吗」的 300 字 |
| 第一句给答案 | 「关于您的问题」 |
| 不用破折号 | 藏起逻辑关系的那一横 |
| 术语第一次出现时用几个字解释 | 读者要去查的词 |
| 不用开场白和结束语 | 「好的」「希望对你有帮助」 |

完整规则在 [SKILL.md](skills/jianming-zhongwen/SKILL.md)，编号目录和各类文档的结构在 [rule-catalog.md](skills/jianming-zhongwen/references/rule-catalog.md)，替换表在 [word-swaps.md](skills/jianming-zhongwen/references/word-swaps.md)。

三个字数上限是暂定值。校准协议和结果在 [docs/design.md](docs/design.md) 第 2.7 节和第 5 节。

## 实测

还没有数字。README 里每个数字都必须能由 `evals/check_numbers.py` 从入库的原始文件重算，CI 每次推送都跑。生成在 Claude Code 里用 `/jianming-zhongwen:bench` 完成，打分用 `evals/score_text_dir.py`。头条指标是回复的读者可见缺陷（超过 5 句的句子、破折号、加粗、标题、列表项），不是 linter 的违规数。

## linter

```bash
python3 evals/jm_lint.py --type procedural 文档.md
python3 evals/jm_lint.py --type reply 回复.txt
python3 evals/jm_lint.py --self-test
```

纯标准库，Python 3.9。它只数正则能数的东西：句长、弱动词、被字句、禁用情态词、分号、破折号、首先其次链、不是而是、的字链、空洞词、同义词轮换。它看不懂意思，一个施事未知的被字句也会被数进去。

插件里的两个 hook 用它：写完一个 .md 文件后报一次违规摘要，回复超过 5 句或带格式时提醒一次。两个都只提示，不阻塞。设置 `JIANMING_ZHONGWEN_LINT_EXCLUDE` 可以跳过路径，用系统的路径分隔符隔开的 glob 列表。

## 它不做什么

营销文案、品牌文字、有个人声音的写作，规则会把说服性的内容删掉。繁体中文，第一版只做简体和大陆术语。去 AI 味改写，弱动词、被字句、名词化是欧化中文问题，不是 AI 特有问题。

## 参与

开 issue 提问题和报错。欢迎 PR。改动了任何已发布数字的 PR 要带上原始文件，`python3 evals/check_numbers.py` 必须通过。推送前跑 `python3 evals/jm_lint.py --self-test`。

## 许可

MIT。GB/T 条文只转述不复制。不含任何 ASD-STE100 词典内容。

---

# jianming-zhongwen (Plain Technical Chinese)

An agent skill that makes a model write technical documents and replies in Chinese that a reader understands on one read. The rules are countable and a regex can find them: a procedural sentence has 30 characters at most, modals come from five pairs only, no 进行 / 作出 plus a noun, a reply has five sentences at most.

The rules come from Chinese sources: 余光中's critique of Europeanized Chinese, 阮一峰's technical-writing guide, the modal-verb table in GB/T 1.1-2020 Annex C, and the punctuation rules in GB/T 15834-2011. AI tells are a second guard layer, based on the lieflat corpus and the CCL 2023 measurements. The research and the reason for each decision are in [docs/design.md](docs/design.md).

The engineering follows [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish): self-tests, a numbers gate, a version gate, hooks, a marketplace.

## Install

Claude Code plugin, with hooks and an output style:

```
/plugin marketplace add heichaowo/jianming-zhongwen
/plugin install jianming-zhongwen@jianming-zhongwen
```

Update from the `/plugin` screen, or with `claude plugin update jianming-zhongwen@jianming-zhongwen`.

The output style is named `jianming-zhongwen:jianming-zhongwen`. Select it under Output style in `/config`.

Any tool that reads SKILL.md:

```bash
npx skills add heichaowo/jianming-zhongwen
```

Tools without SKILL.md support: paste the rule block between the two separators in [prompts/system-prompt.md](prompts/system-prompt.md) into the system prompt, `AGENTS.md`, or `.cursorrules`. The page ends with a 60-token version.

## Rules

The document register covers README files, runbooks, troubleshooting, error text, release notes, and incident reports. The reply register covers every chat reply: prose only, five sentences at most with list items counted, the answer in the first sentence, no dashes, terms explained at first use, no openers or closers.

The full rules are in [SKILL.md](skills/jianming-zhongwen/SKILL.md). The numbered catalog with the structure of each document type is in [rule-catalog.md](skills/jianming-zhongwen/references/rule-catalog.md). The swap table is in [word-swaps.md](skills/jianming-zhongwen/references/word-swaps.md).

The three character caps are provisional. The calibration protocol and its results are in [docs/design.md](docs/design.md), sections 2.7 and 5.

## Measurements

No numbers yet. Every number in this README must be recomputed by `evals/check_numbers.py` from the committed raw files, and CI runs it on every push. Generation happens inside Claude Code with `/jianming-zhongwen:bench`. Scoring uses `evals/score_text_dir.py`. The headline metric is reader-visible reply defects (sentences over the cap, dashes, bold, headers, list items), not linter violations.

## Linter

```bash
python3 evals/jm_lint.py --type procedural doc.md
python3 evals/jm_lint.py --type reply reply.txt
python3 evals/jm_lint.py --self-test
```

Standard library only, Python 3.9. It counts only what a regex can count: sentence length, weak verbs, marked passives, banned modals, semicolons, dashes, ordinal chains, "不是 X 而是 Y", 的 chains, slop words, synonym rotation. It cannot see meaning. A 被 passive with an unknown agent is counted too.

The two plugin hooks use it: a violation summary after each .md file is written, and one reminder when a reply is over five sentences or carries formatting. Both are advisory. Set `JIANMING_ZHONGWEN_LINT_EXCLUDE` to skip paths, a glob list separated by the platform path separator.

## What it does not do

Marketing copy, brand writing, and writing with a personal voice: the rules delete persuasion. Traditional Chinese: the first version covers Simplified Chinese and mainland terms only. De-AI rewriting: weak verbs, 被 passives, and nominalization are Europeanized-Chinese problems, not AI-specific ones.

## Contributing

Open an issue for questions and bug reports. Pull requests are welcome. A change that moves a published number ships the raw files with it, and `python3 evals/check_numbers.py` must pass. Run `python3 evals/jm_lint.py --self-test` before you push.

## License

MIT. GB/T text is paraphrased, never copied. No ASD-STE100 dictionary content.
