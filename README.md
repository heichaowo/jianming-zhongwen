# 简明技术中文 jianming-zhongwen

<p>
  <a href="skills/jianming-zhongwen/SKILL.md"><img src="https://img.shields.io/badge/version-1.0.3-blue?style=flat" alt="version 1.0.3"></a>
  <a href="https://github.com/heichaowo/jianming-zhongwen/actions/workflows/check.yml"><img src="https://github.com/heichaowo/jianming-zhongwen/actions/workflows/check.yml/badge.svg" alt="check"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat" alt="MIT"></a>
</p>

一个 Agent Skill，让模型用一遍就能读懂的中文写技术文档和回复。规则可数，能用正则查：程序性句子不超过 30 字，情态词只用五组，不用 进行 / 作出 加名词，回复最多 5 句。

规则来自中文自己的规范：余光中对欧化中文的批评，阮一峰的《中文技术文档的写作规范》。情态词的分工来自 GB/T 1.1-2020 附录 C，标点用法来自 GB/T 15834-2011。AI 味只是第二层守卫，依据是 lieflat 语料和 CCL 2023 的实测数据。研究过程和每条决定的理由在 [docs/design.md](docs/design.md)。

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

不支持 SKILL.md 的工具：把规则块粘贴进系统提示、`AGENTS.md` 或 `.cursorrules`。规则块在 [prompts/system-prompt.md](prompts/system-prompt.md) 两条分隔线之间，页尾有一个 60 token 的短版本。

## 规则

文档，写或改写 README、操作手册、故障排查、报错文本、发布说明、事故报告时：

| 规则 | 它删掉什么 |
|---|---|
| 程序性每句不超过 30 字，描述性不超过 50 字，逗号分句不超过 40 字 | 一口气读不完的句子 |
| 用实义动词，不用 进行 / 作出 / 予以 / 加以 加名词 | 「对配置进行修改」 |
| 情态词按阶梯：必须 / 建议 / 可以 / 能 / 可能，各管一件事 | 「应该」到底是要求还是猜测 |
| 条件在前，动作在后 | 读者做完了才看到的「如果」 |
| 主动为主，被字句只在施事未知时用 | 「已经被处理了」 |
| 不用分号，不用破折号连接两个陈述，三个以上分句就拆句 | 流水句 |
| 一词一义，全文一致 | 配置、设置、参数轮着用 |
| 只说事实，不说重要性 | 值得注意的是、至关重要、赋能、闭环、「不是 X 而是 Y」 |
| 「的」字链不超过两层，名词化改回动词 | 「服务器端的连接池的超时时间的默认值」「可读性高」 |
| 格式为读者服务 | 加粗导语、emoji、两句话的标题、两项的列表 |

回复，每一条中文回复：

| 规则 | 它删掉什么 |
|---|---|
| 只用散文，不用标题、列表、加粗、表格 | 围着一句答案的一堆格式 |
| 最多 5 句，列表项也算句 | 回答「严重吗」的 300 字 |
| 第一句给答案 | 「关于您的问题」 |
| 不用破折号 | 藏起逻辑关系的那一横 |
| 术语第一次出现时用几个字解释 | 读者要去查的词 |
| 不用开场白和结束语 | 「好的」「希望对你有帮助」 |

完整规则在 [SKILL.md](skills/jianming-zhongwen/SKILL.md)。编号目录和各类文档的结构在 [rule-catalog.md](skills/jianming-zhongwen/references/rule-catalog.md)，替换表在 [word-swaps.md](skills/jianming-zhongwen/references/word-swaps.md)。

三个字数上限经 2026-09-09 的基线校准，样本是 8 篇文档的 27 个中文句子。校准协议和结果在 [docs/design.md](docs/design.md) 第 2.7 节和第 5 节。

## 实测

<!-- numbers-from: evals/results/run-2026-09-09 -->

数字来自 `evals/results/run-2026-09-09`，`evals/check_numbers.py` 每次推送都从入库的原始文件重算。生成在 Claude Code 桌面 App 里用 Workflow 工具完成。模型 sonnet，effort low。本插件和 simple-english 都已卸载或禁用，用户自己的 CLAUDE.md 在场。每格一次生成，回复两轮。头条指标是回复的读者可见缺陷，不是 linter 的违规数。

回复，8 个问题各两轮，共 16 条。可见缺陷（超过 5 句的句子、破折号、加粗、标题、列表项）从 322 降到 2，少 99%。5 句以内的回复 0/16 对 14/16。

| 条件 | 字数 | 句数 | 破折号 | 加粗 | 标题 | 列表项 |
|---|---:|---:|---:|---:|---:|---:|
| 无 skill | 510 | 13.8 | 16 | 54 | 3 | 109 |
| skill | 177 | 4.2 | 0 | 0 | 0 | 0 |

文档，8 个场景：每千字违规数 12.94 对 7.36，少 43%。skill 剩下的 5 处违规分布在 4 篇文档，都是句子超出上限几个字。

评委盲测（sonnet，两种顺序各一票）：skill 胜 7，平 0，负 9。两种顺序在 8 个场景里有 5 个给出相反结论，评委偏向排在后面的那份。位置偏好盖过了内容差异，这个数字不是结论。下一版改成两种顺序各打分再取平均。

短回复的代价：5 句上限会把「视情况」压成断言。消费积压那题，基线说严重程度取决于吞吐量和业务类型，skill 版直接说「需要立即处理」。规则删掉了铺垫，也删掉了一个正确的保留。

## linter

```bash
python3 evals/jm_lint.py --type procedural 文档.md
python3 evals/jm_lint.py --type reply 回复.txt
python3 evals/jm_lint.py --self-test
```

纯标准库，Python 3.9。它只数正则能数的东西：句长、弱动词、被字句、禁用情态词、分号、破折号、首先其次链、不是而是、的字链、空洞词、同义词轮换。它看不懂意思，施事未知的被字句它也照数。

插件里的两个 hook 用它：写完一个 .md 文件后报一次违规摘要，中文回复超过 5 句或带格式时提醒一次。英文回复不检查。两个都只提示，不阻塞。设置 `JIANMING_ZHONGWEN_LINT_EXCLUDE` 可以跳过路径，用系统的路径分隔符隔开的 glob 列表。

## 它不做什么

营销文案、品牌文字、有个人声音的写作，规则会把说服性的内容删掉。繁体中文，第一版只做简体和大陆术语。去 AI 味改写，弱动词、被字句、名词化是欧化中文问题，不是 AI 特有问题。

## 参与

开 issue 提问题和报错。欢迎 PR。改动了任何已发布数字的 PR 要带上原始文件，`python3 evals/check_numbers.py` 必须通过。推送前跑 `python3 evals/jm_lint.py --self-test`。

## 许可证

本项目基于 [MIT](LICENSE) 协议开源。GB/T 条文只转述，不复制，附上链接。不含 ASD-STE100 词典内容。

---

# jianming-zhongwen (Plain Technical Chinese)

An agent skill that makes a model write technical documents and replies in Chinese that a reader understands on one read. The rules are countable and a regex can find them: a procedural sentence has 30 characters at most, a descriptive one 50, modals come from five pairs only, no 进行 / 作出 plus a noun, a reply has five sentences at most.

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

The document register covers README files, runbooks, troubleshooting, error text, release notes, and incident reports. The reply register covers every Chinese reply: prose only, five sentences at most with list items counted, the answer in the first sentence, no dashes, terms explained at first use, no openers or closers.

The full rules are in [SKILL.md](skills/jianming-zhongwen/SKILL.md). The numbered catalog with the structure of each document type is in [rule-catalog.md](skills/jianming-zhongwen/references/rule-catalog.md). The swap table is in [word-swaps.md](skills/jianming-zhongwen/references/word-swaps.md).

The three character caps were calibrated on 2026-09-09 against a baseline of 8 documents, 27 Chinese sentences. The protocol and the results are in [docs/design.md](docs/design.md), sections 2.7 and 5.

## Measurements

The numbers come from `evals/results/run-2026-09-09`, and `evals/check_numbers.py` recomputes them from the committed raw files on every push. Generation ran inside the Claude Code desktop app with the Workflow tool: sonnet, effort low, this plugin and simple-english removed or disabled, the user's own CLAUDE.md present. One generation per cell, two runs for replies. The headline metric is reader-visible reply defects, not linter violations.

Replies, 8 questions in two runs, 16 in total. Visible defects (sentences over five, dashes, bold, headers, list items) went from 322 to 2, 99% fewer. Replies within five sentences: 0 of 16 without the skill, 14 of 16 with it.

| Condition | chars | sentences | dashes | bold | headers | list items |
|---|---:|---:|---:|---:|---:|---:|
| no skill | 510 | 13.8 | 16 | 54 | 3 | 109 |
| skill | 177 | 4.2 | 0 | 0 | 0 | 0 |

Documents, 8 scenarios: 12.94 violations per 1000 characters without the skill, 7.36 with it, 43% fewer. The remaining 5 violations, in 4 of the documents, are sentences a few characters over the cap.

Blind judge (sonnet, one vote per order): the skill won 7, tied 0, lost 9. The two orders disagreed on 5 of 8 scenarios, and the judge leaned toward whichever text came second. Position bias outweighed the content, so this number is not a conclusion. The next version scores both orders and averages.

The cost of short replies: the five-sentence cap can turn "it depends" into an assertion. On the consumer-lag question the baseline said severity depends on throughput and the business path; the skill version said "handle it now". The rules removed the preamble and also removed a correct hedge.

## Linter

```bash
python3 evals/jm_lint.py --type procedural doc.md
python3 evals/jm_lint.py --type reply reply.txt
python3 evals/jm_lint.py --self-test
```

Standard library only, Python 3.9. It counts only what a regex can count: sentence length, weak verbs, marked passives, banned modals, semicolons, dashes, ordinal chains, "不是 X 而是 Y", 的 chains, slop words, synonym rotation. It cannot see meaning. A 被 passive with an unknown agent is counted too.

The two plugin hooks use it: a violation summary after each .md file is written, and one reminder when a Chinese reply is over five sentences or carries formatting. English replies are not checked. Both are advisory. Set `JIANMING_ZHONGWEN_LINT_EXCLUDE` to skip paths, a glob list separated by the platform path separator.

## What it does not do

Marketing copy, brand writing, and writing with a personal voice: the rules delete persuasion. Traditional Chinese: the first version covers Simplified Chinese and mainland terms only. De-AI rewriting: weak verbs, 被 passives, and nominalization are Europeanized-Chinese problems, not AI-specific ones.

## Contributing

Open an issue for questions and bug reports. Pull requests are welcome. A change that moves a published number ships the raw files with it, and `python3 evals/check_numbers.py` must pass. Run `python3 evals/jm_lint.py --self-test` before you push.

## License

This project is released under the [MIT](LICENSE) license. GB/T text is paraphrased, never copied, with links to the source. No ASD-STE100 dictionary content.
