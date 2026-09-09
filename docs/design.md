# jianming-zhongwen（简明技术中文）设计

中文在前，English below。英文是源文本，中文是译文。改英文，再重译中文。

## 1. 目标与边界

jianming-zhongwen 是一个 Agent Skill，让模型用简明技术中文写作和回复。它由四件东西组成：一份 SKILL.md、一个 linter、一套 benchmark、一个 Claude Code 插件。

工程结构模仿 AminBlg/SimpleEnglish：自测、数字门、版本门、hook、marketplace。内容不模仿。规则来自余光中、阮一峰、GB/T 1.1-2020 附录 C 和 GB/T 15834-2011，指标来自 lieflat 语料和 CCL 2023 的中文 AI 写作数据，场景为中文开发者的环境编写。这些都记录在 2026-09-09 的研究报告里。

它做：技术文档（README、操作手册、故障排查、报错文本、发布说明、事故报告、接口说明）和聊天回复。

它不做：营销文案、品牌文字、有个人声音的写作、繁体中文、去 AI 味改写。弱动词、被字句、名词化是欧化中文问题，不是 AI 特有问题（lieflat 语料实测），所以本项目不叫「去 AI 味」，AI 味只是第二层守卫。

## 2. 决定

每条记录判断、被拒绝的选项和原因。代码里能看出来的东西不写。

### 2.1 名称

slug `jianming-zhongwen`，显示名「简明技术中文」，仓库 `heichaowo/jianming-zhongwen`。marketplace、plugin、skill、output style 全部用同一个 slug，和 SimpleEnglish 一样。

拒绝 `shuorenhua`：MrGeDiao/shuorenhua（1491 stars）的 marketplace 名和 plugin 名都是它，1-SKILL 和 tentenco 也用它，社区里「说人话」已经等于「去 AI 味改写」。拒绝 `cste-zh`：RinStel 已占用。拒绝 `simple-chinese`：会被读成「简体中文」。拒绝 `jianming`：GitHub 上有一批以人名命名的同名仓库，搜索时混在一起。

本地目录仍叫 `shuorenhua`。仓库建好后把目录改名为 `jianming-zhongwen`。

### 2.2 硬规则，不是提示

现有的中文受控写作 skill（Fenng、EsserZ、capric98、bjo4）都拒绝硬句长上限和一刀切禁令。本项目反过来：规则可数，可以用正则查。理由是 SimpleEnglish 自己的审计（WHY-USELESS）：真正改变输出的是 5 条可数的回复规则，53 条软规则反而稀释它们。

代价：任何写进 SKILL.md 的数字必须先在中文 benchmark 上验证。没有数据的上限只能标「暂定」。

### 2.3 两个寄存器

文档（写或改写的内容）和回复（聊天里打出的内容），各一套规则。回复规则在任何模式下优先。这是中文项目里唯一空着的位置。

### 2.4 文档规则（16 条）

1. 先分类。程序性文本用祈使句，一句一个动作，每句不超过 30 字。描述性文本用陈述句，每句不超过 45 字，一段一个主题，一段不超过 6 句。逗号分句不超过 40 字。
2. 不动代码、命令、路径、报错原文、产品名和事实。原文没有的数字和原因不补。
3. 条件在前，动作在后，逗号分隔。
4. 用实义动词。不用 进行 / 作出 / 予以 / 加以 / 开展 / 实施 加名词。
5. 情态词按阶梯用，各管一件事，不互换。见 2.5。
6. 主动为主。被字句只在施事真正未知时用。不叠套。无标记被动合法。
7. 不用分号。不用破折号连接两个陈述。逗号串起三个以上分句就拆句。
8. 一词一义，全文一致。大陆简体术语。
9. 概念术语首次出现时定义，不超过 20 字，一句一个。产品名、标准名不定义。
10. 只说事实，不说重要性。删空洞词、黑话和「不是 X 而是 Y」。
11. 格式为读者服务。不用加粗导语、装饰性加粗、emoji、只管两句话的标题。三项以上才用列表。
12. 警告先写命令或条件，再写风险。
13. 「的」字链不超过两层。
14. -性 / -化 / -度 名词化，有更短写法就改回动词或形容词。容器化、序列化这类技术术语保留。
15. 一段内四字格不连用三个以上。
16. 中英文之间留空格。

规则的来源：1 和 7 的字数与拆句来自阮一峰《中文技术文档的写作规范》，4、6、13、14 来自余光中《怎样改进英式中文》，5 来自 GB/T 1.1-2020 附录 C，7 的标点来自 GB/T 15834-2011，10 和 11 来自 lieflat 语料里倍率最高的中文 AI 特征（冒号空转引列表 9.4 倍、翻案腔 3.4 倍、破折号 3.0 倍）。规则 16 属于排版层，linter 不测。

字数计法：汉字和字母数字各计 1，标点不计，一个行内代码段计 1，句子以 。！？ 为界，括号和引号内的句末标点不断句。

### 2.5 情态阶梯

| 类型 | 用词 |
|---|---|
| 要求 | 必须 / 不得 |
| 推荐 | 建议 / 不建议 |
| 允许 | 可以 / 不必 |
| 能力 | 能 / 不能 |
| 可能性 | 可能 / 不可能 |

禁用：应该、应当、最好、尽量、务必、宜、需要（作情态时）。可 / 能 / 可能 三词不互换。

五类分法来自 GB/T 1.1-2020 第 9.1 条和附录 C。用词有意偏离附录 C：附录 C 用 应 / 不应 表示要求，并明确不用 必须 / 不得 / 禁止，理由是标准文件要把自身要求和法律等外部约束分开。技术文档的读者不是标准审查员，「应」在他们眼里是弱建议。所以要求级用 必须 / 不得。附录 C 那条「可 是允许，能 是能力，可能 是可能性，不得互换」原样保留。文档里只转述附录 C，不复制条文。

### 2.6 回复规则（7 条）

1. 只用散文。不用标题、列表、加粗、表格。读者要复制的内容才用代码块。
2. 最多 5 句。列表项和冒号引出的分点都算句。
3. 第一句给答案。不复述问题。
4. 不用破折号。
5. 概念术语第一次出现时用几个字解释。产品名不解释。
6. 不用开场白（好的、当然、您好、感谢提问）和结束语（希望对你有帮助、如有问题欢迎继续）。
7. 报错原文、安全警告、破坏性操作前的确认，不缩短。

模式只有两种：标准（默认，以上全部规则）和检查（用户要求检查文本时，按 `references/rule-catalog.md` 的编号逐条报告，不凭记忆引用编号）。拒绝严格模式：SimpleEnglish 的严格模式建立在 STE 词典上，中文没有对应词典，一个更小的字数上限不构成模式。

### 2.7 句长上限是暂定值

30 / 45 / 40 三个数字没有实验依据。它们同时落在翻译换算区间内（20 词约 26 到 36 字，25 词约 33 到 45 字），和 RinStel/cste-zh 独立得出的 30 / 45 一致，40 字分句线来自阮一峰和华为 2004 年规范。

校准协议：先跑无 skill 的基线（8 个文档场景，sonnet），用 linter 取所有句子的字数分布。程序性和描述性分开算 P70，向上取整到 5 的倍数。程序性落在 25 到 35 之间、描述性落在 40 到 50 之间就用校准值，否则保留暂定值并写明。分句线 40 字不校准，只报告 P90 是否超过。结果记在本文件第 5 节，不进 README。校准前 README 不发布任何上限有效性的数字。

拒绝：从「1 英文词等于 1.5 汉字」推导上限。核查发现这个换算引的是语音信息率研究，用在书面字数上是类别错误。

### 2.8 测量

linter `evals/jm_lint.py`：纯标准库，Python 3.9。文档指标：句超限、分句超限、弱动词、有标记被字句、禁用情态词、分号、破折号连接、排比链（首先 / 其次 / 最后 同段出现两个以上）、翻案腔、「的」字链、slop 词、同义词轮换。冒号空转引列表不单独测：正则分不开它和合法的列表导语（「运行以下命令：」），回复侧由句数和列表项计数覆盖。回复指标（reader_check）：句数（列表项计入）、超上限句数、破折号、加粗、标题、列表项、开场白、结束语。计量单位是每千字违规数，不是每百词。

弱动词只在后面跟着动名词（处理、分析、检查、配置、部署、验证等）时才算命中，「进行中」「进行到一半」不算。这是压低误报的代价：「进行深度学习」这类漏报可以接受，误报会让用户关掉 hook。

拒绝 jieba 进核心：450 毫秒冷启动会拖慢每次 PostToolUse hook，而且没有任何发布数字需要分词。留作以后的 `--segmented` 选项。拒绝 pkuseg、HanLP：要下载模型。

头条数字是回复的读者可见缺陷（超上限句 + 破折号 + 加粗 + 标题 + 列表项，16 条回复合计）的下降百分比，加上 5 句以内的回复数。文档的每千字违规数是次要数字。这个顺序是 WHY-USELESS 的直接结论：只报 linter 违规数，测的是对自家 linter 的服从，不是读者看到什么。

评委：盲测成对比较，两种顺序各判一次取平均，评分标准三条：非母语技术读者能否一遍读懂、指令能否照做、有没有废话和 AI 腔。评委是 Claude 模型，文本也是 Claude 输出，家族偏差可能存在，README 要写明。

### 2.9 benchmark

场景为中文开发者的环境编写，不翻译 SimpleEnglish 的场景。文档 8 个：README 简介、快速开始、故障排查、报错文本、事故报告、发布说明、一步改短、架构概述，围绕一个虚构的命令行工具 datasync（把 MySQL 表同步到阿里云 OSS 存为 Parquet）。回复 8 个：每个带一个要解释的术语（幂等、分库分表、证书链、消费积压、OOMKilled、令牌桶、回填、缓存失效）。

生成在 Claude Code 桌面 App 里完成，不装 CLI，不走 API。插件带一条命令 `/jianming-zhongwen:bench`（`commands/bench.md`）。它读两个场景文件，对每个场景用 Agent 工具起一个子代理：基线条件只给场景提示词；skill 条件在提示词前加 `prompts/system-prompt.md` 的规则块。子代理看不到主会话，所以基线不受插件注入影响。模型固定 sonnet。输出按 `<条件>__<场景>.txt` 存到 `evals/results/<批次>/`，附一个 manifest 记录模型、会话的 effort 设置、日期和规则块的 SHA256。回复场景跑两轮。评委也是子代理，成对盲测，两种顺序。打分、汇总、比对全部在 Python 里（`score_text_dir.py`、`check_numbers.py`）。

拒绝装 `claude` CLI：用户决定。拒绝 API 直连：要 API key，而且是第二套生成代码。代价：子代理的 effort 只能继承会话设置，不能像 `claude -p --effort low` 那样钉死，manifest 记录它，README 写明。别人重跑的数字可能不同，README 只发布能从入库 raw 文件重算的数字。

2026-09-09 实测的两个混杂因素。子代理看得到已安装的全部 skill，写 README 这类任务会触发本插件或 simple-english 的 skill。这份列表在会话开始时定下，会话中途 `plugin disable` 甚至 `plugin uninstall` 都不改变已开会话里子代理看到的列表，三次探测结果相同。所以先用 App 自带的 Claude Code 内核禁用这两个插件，再新开会话跑生成，生成后再 `enable`。子代理还继承用户的全局 `~/.claude/CLAUDE.md`，这个文件含短句和一词一义的写作要求，会把基线往 skill 的方向推，测出来的改善只会偏小，不会偏大。不动这个文件，manifest 记 `user_claude_md: present`，README 写明基线是「这台机器的 Claude Code，含用户自己的 CLAUDE.md」。有 Workflow 工具时用它生成，effort 钉为 low，和 SimpleEnglish 一致，manifest 的 `harness` 字段记录用了哪个工具。

### 2.10 插件、测试与更新

一个仓库同时是 marketplace 和 plugin，`marketplace.json` 的 `source` 是 `./`。安装两条命令，更新一条：`claude plugin update jianming-zhongwen@jianming-zhongwen`，App 里用 `/plugin` 界面。更新由 `plugin.json` 的 `version` 驱动，版本号不动的 commit 用户拿不到，所以发布流程把版本号提升当作硬步骤。

测试从 GitHub 安装，和用户的路径一样。桌面 App 的 Code 页没有 `/plugin` 命令，用 App 自带的 Claude Code 内核：`~/Library/Application Support/Claude/claude-code/<版本>/claude.app/Contents/MacOS/claude`，它写的是 App 读的同一份登记表 `~/.claude/plugins/`。命令：`plugin marketplace add heichaowo/jianming-zhongwen`，`plugin install jianming-zhongwen@jianming-zhongwen`；推送改动后 `plugin marketplace update jianming-zhongwen`，再 `plugin update jianming-zhongwen@jianming-zhongwen`。`plugin update` 只认版本号，测试中的改动也要提版本号，或者卸载重装。验证：开新会话看规则块有没有注入，写一条超过 5 句的回复看 Stop hook 有没有提示。

拒绝本地目录 marketplace。官方文档不允许插件源指向 marketplace 根目录本身，指向仓库的符号链接又会因为在 marketplace 之外被跳过，只能包一层拷贝加同步脚本。2026-09-09 试过一次，能用，但和「从 GitHub 更新测试」重复，删了。

三个 hook：SessionStart 用 Node 把 `prompts/system-prompt.md` 的规则块以纯文本写到 stdout，和 SimpleEnglish 2.0.2 实测一致，不包 JSON；上限 9500 字符，超限或读不到文件时输出一段固定的短规则。PostToolUse 在 Write 和 Edit 一个 .md 文件后跑 linter，退出码 2，只提示不阻塞，跳过 `.claude` 目录和 `JIANMING_ZHONGWEN_LINT_EXCLUDE` 列出的路径。Stop 对最后一条回复跑 reader_check，违规时返回一条 systemMessage，永远退出 0。Python hook 在启动时把 stdout 和 stderr 重设为 UTF-8，不靠 shell 环境变量，Windows 上也能输出中文。

输出样式 `output-styles/jianming-zhongwen.md` 的正文和 `prompts/system-prompt.md` 的规则块逐字相同，`check_numbers.py` 校验。选用名是 `jianming-zhongwen:jianming-zhongwen`。

版本号的唯一来源是 SKILL.md frontmatter，`check_numbers.py` 校验 `plugin.json`、`marketplace.json` 和 README 徽章与之一致。拒绝单独的 VERSION 文件：多一个文件，少不了任何校验。

兼容：Claude Code 插件和 skills CLI（`npx skills add heichaowo/jianming-zhongwen`）。Cursor 等不支持 SKILL.md 的工具粘贴 `prompts/system-prompt.md`。Codex 插件清单推迟：这里没法测。

### 2.11 CI 与发布

CI 不调用模型。四步：linter 自测、Node hook 测试、Python hook 测试、`check_numbers.py`。Python 固定 3.9，和本机一致。raw 文件为空时 `check_numbers.py` 只校验版本号和规则块同步，并打印「数字校验跳过」。这是引导期的保护，不是长期逻辑。

发布：改 SKILL.md 版本号，同步另外三处，写 CHANGELOG（英文），本地跑四步，App 里跑 `/plugin validate .`，提交 `release: vX.Y.Z`，打标签，推送，从 CHANGELOG 建 GitHub Release。改动了任何已发布数字的提交必须带上 raw 文件。

版本从 0.1.0 开始。校准过的上限和 benchmark 数字发布后才是 1.0.0。

### 2.12 版权边界

MIT。GB/T 条文只转述不复制，附上链接。不复制任何 STE 词典内容。引用 lieflat 的倍率时注明其语料不公开、第三方无法核验。规则的来源写在 SKILL.md frontmatter，不在正文里讲故事。README 自己写，不翻译 SimpleEnglish 的。

## 3. 目录

```
jianming-zhongwen/
├── LICENSE
├── README.md                      中文在前，英文在后
├── CHANGELOG.md                   英文
├── docs/design.md                 本文件
├── skills/jianming-zhongwen/
│   ├── SKILL.md                   两个寄存器、自检、模式、参考；版本号来源
│   └── references/
│       ├── rule-catalog.md        编号规则全目录，含 AI 腔一节，检查模式用
│       ├── word-swaps.md          欧化和黑话到简明写法的对照表
│       └── slop-zh.tsv            词、来源、替换建议；linter 读取
├── commands/bench.md              /jianming-zhongwen:bench，在 App 里生成 raw 文件
├── prompts/system-prompt.md       独立规则块，hook 注入，无 SKILL.md 支持时粘贴
├── output-styles/jianming-zhongwen.md   与规则块逐字相同
├── evals/
│   ├── jm_lint.py                 linter，含 --self-test
│   ├── score_text_dir.py          给一个批次目录打分，生成 RESULTS.md
│   ├── check_numbers.py           数字门和版本门
│   ├── scenarios.json             8 个文档场景
│   ├── reply_scenarios.json       8 个回复场景
│   └── results/                   raw 文件、manifest 和 RESULTS.md，入库
├── src/hooks/
│   ├── activate.js                SessionStart
│   ├── activate.test.js
│   ├── lint_hook.py               PostToolUse 和 Stop
│   ├── test_lint_hook.py
│   └── package.json               {"type": "commonjs"}
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
└── .github/workflows/check.yml
```

## 4. 计划

每个阶段有一条可观察的完成判据。

0. 前提。建 `heichaowo/jianming-zhongwen` 公开仓库（MIT）。本地目录改名。判据：`gh repo view heichaowo/jianming-zhongwen` 成功。
1. linter。写 `evals/jm_lint.py`、`slop-zh.tsv` 和自测固件（一段违规文本、一段干净文本、一条违规回复、一条干净回复，加边界用例）。判据：`python3 evals/jm_lint.py --self-test` 退出 0。
2. 规则文件。写 SKILL.md、三个参考文件、`prompts/system-prompt.md`、`output-styles/jianming-zhongwen.md`。判据：三个文件都含「最多 5 句」，规则块少于 9000 字符，SKILL.md 少于 2200 token。
3. 插件。写两个 hook、两个测试、两个清单、`commands/bench.md`。判据：两个测试通过；App 里从本地路径安装后，新会话能看到规则块，超 5 句的回复触发 Stop 提示，`/plugin validate .` 通过。
4. benchmark 脚本。写两个场景文件、`score_text_dir.py`、`check_numbers.py`。判据：`score_text_dir.py` 在空目录上不报错，`check_numbers.py` 在无 raw 文件时以跳过模式通过。
5. CI 与首次发布。写 `check.yml`、README、CHANGELOG，推送，打 v0.1.0。判据：GitHub Actions 全绿。
6. 校准与数字。在 App 里跑 `/jianming-zhongwen:bench` 生成基线，按 2.7 校准上限，跑 skill 条件和回复两轮，跑评委，把 raw 文件和数字入库，发布 v1.0.0。判据：`check_numbers.py` 在有数字的 README 上通过。

进度板：

- [x] 0 前提：仓库 heichaowo/jianming-zhongwen 已建（2026-09-09）；本地目录改名待用户
- [x] 1 linter（2026-09-09）
- [x] 2 规则文件（2026-09-09）
- [x] 3 插件（2026-09-09，App 内验证：新会话有规则注入，Stop hook 提示）
- [x] 4 benchmark 脚本（2026-09-09）
- [x] 5 CI 与 v0.1.0（2026-09-09，Actions 全绿，从 GitHub 安装验证通过）
- [ ] 6 校准与 v1.0.0

## 5. 测量

校准结果和 benchmark 原始分布记在这里。目前为空。

---

# jianming-zhongwen (Plain Technical Chinese) design

English is the source text. Chinese above is its translation.

## 1. Goal and boundary

jianming-zhongwen is an agent skill that makes a model write and reply in plain technical Chinese. It has four parts: one SKILL.md, one linter, one benchmark, one Claude Code plugin.

The engineering mirrors AminBlg/SimpleEnglish: self-tests, a numbers gate, a version gate, hooks, a marketplace. The content does not. The rules come from 余光中, 阮一峰, GB/T 1.1-2020 Annex C, and GB/T 15834-2011. The metrics come from the lieflat corpus and the CCL 2023 data on Chinese AI writing. The scenarios are written for Chinese developers' environments. All of this is recorded in the research report of 2026-09-09.

It covers technical documents (README, runbooks, troubleshooting, error text, release notes, incident reports, API notes) and chat replies.

It does not cover marketing copy, brand writing, writing with a personal voice, Traditional Chinese, or "de-AI" rewriting. Weak verbs, 被 passives, and nominalization are Europeanized-Chinese problems, not AI-specific ones (the lieflat corpus shows this). The project is therefore not a "去 AI 味" tool. AI tells are a second guard layer only.

## 2. Decisions

Each entry records the judgment, the rejected options, and why. Nothing that the code already states.

### 2.1 Name

Slug `jianming-zhongwen`, display name 简明技术中文, repository `heichaowo/jianming-zhongwen`. The marketplace, plugin, skill, and output style all use the same slug, as SimpleEnglish does.

Rejected `shuorenhua`: MrGeDiao/shuorenhua (1491 stars) uses it as marketplace and plugin name, 1-SKILL and tentenco use it too, and the community reads 说人话 as "de-AI rewrite". Rejected `cste-zh`: taken by RinStel. Rejected `simple-chinese`: reads as "Simplified Chinese". Rejected `jianming`: GitHub has a set of personal repositories with that given name, and searches mix them together.

The local directory is still `shuorenhua`. Rename it to `jianming-zhongwen` after the repository exists.

### 2.2 Hard rules, not advice

The existing controlled-Chinese skills (Fenng, EsserZ, capric98, bjo4) all reject hard sentence caps and blanket bans. This project does the opposite: rules are countable and a regex can find them. The reason is SimpleEnglish's own audit (WHY-USELESS): the 5 countable reply rules changed the output, and 53 soft rules diluted them.

The cost: every number in SKILL.md must be validated on a Chinese benchmark first. A cap without data is marked provisional.

### 2.3 Two registers

The document (what you write or rewrite) and the reply (what you type in chat) each have their own rules. Reply rules apply first in every mode. This is the one position no Chinese project has taken.

### 2.4 Document rules (16)

1. Classify first. Procedural text: imperative, one action per sentence, 30 characters per sentence. Descriptive text: declarative, 45 characters per sentence, one topic per paragraph, six sentences per paragraph. A comma clause has 40 characters at most.
2. Do not touch code, commands, paths, quoted errors, product names, or facts. Do not add numbers or causes the source did not give.
3. Condition first, then the action, with a comma.
4. Use full verbs. No 进行 / 作出 / 予以 / 加以 / 开展 / 实施 plus a noun.
5. Modals follow the ladder. One word, one job, no swaps. See 2.5.
6. Active by default. A 被 passive only when the agent is unknown. No stacking. Unmarked passives are legal.
7. No semicolons. No dash between two statements. Three or more comma clauses become separate sentences.
8. One word, one meaning, for the whole document. Mainland Simplified terms.
9. Define a concept term at first use in 20 characters or fewer, one per sentence. Do not define product or standard names.
10. State the fact, not its importance. Delete empty words, jargon, and "不是 X 而是 Y".
11. Format for the reader. No bold lead-ins, no decorative bold, no emoji, no heading over two sentences. A list needs three or more items.
12. Warnings: command or condition first, then the risk.
13. A 的 chain has two levels at most.
14. Turn -性 / -化 / -度 nominalizations back into verbs or adjectives when a shorter form exists. Technical terms such as 容器化 and 序列化 stay.
15. No three four-character phrases in a row within a paragraph.
16. Put a space between Chinese and Latin text.

Sources: the counts and sentence splitting in rules 1 and 7 come from 阮一峰's technical-writing guide; rules 4, 6, 13, and 14 from 余光中's essay on Europeanized Chinese; rule 5 from GB/T 1.1-2020 Annex C; the punctuation in rule 7 from GB/T 15834-2011; rules 10 and 11 from the highest-ratio Chinese AI tells in the lieflat corpus (a colon that introduces a list at 9.4×, "不是 X 而是 Y" at 3.4×, dashes at 3.0×). Rule 16 is typography. The linter does not measure it.

Counting: each CJK character and each Latin letter or digit counts 1, punctuation counts 0, an inline code span counts 1. A sentence ends at 。！？. A sentence-final mark inside brackets or quotes does not end a sentence.

### 2.5 Modal ladder

| Type | Words |
|---|---|
| Requirement | 必须 / 不得 |
| Recommendation | 建议 / 不建议 |
| Permission | 可以 / 不必 |
| Capability | 能 / 不能 |
| Possibility | 可能 / 不可能 |

Banned: 应该, 应当, 最好, 尽量, 务必, 宜, 需要 (as a modal). 可 / 能 / 可能 are never interchangeable.

The five types come from GB/T 1.1-2020 clause 9.1 and Annex C. The words deliberately deviate from Annex C. Annex C uses 应 / 不应 for requirements and says not to use 必须 / 不得 / 禁止, because a standard must separate its own requirements from external constraints such as law. Readers of technical documents are not standards auditors. To them 应 reads as weak advice. So the requirement level uses 必须 / 不得. The Annex C note that 可 is permission, 能 is capability, 可能 is possibility, and they do not swap, stays as written. The documents paraphrase Annex C and do not copy its text.

### 2.6 Reply rules (7)

1. Prose only. No headers, lists, bold, or tables. A code block only for text the reader copies.
2. Five sentences at most. List items and colon-led points count as sentences.
3. The first sentence gives the answer. Do not restate the question.
4. No dashes.
5. Explain a concept term in a few characters at first use. Do not explain product names.
6. No openers (好的, 当然, 您好, 感谢提问) and no closers (希望对你有帮助, 如有问题欢迎继续).
7. Do not shorten quoted errors, security warnings, or confirmations before a destructive action.

There are two modes only: standard (default, all rules above) and check (when the user asks for a check, report each violation by number from `references/rule-catalog.md`, never from memory). Rejected a strict mode: SimpleEnglish's strict mode rests on the STE dictionary, Chinese has no such dictionary, and a smaller character cap is not a mode.

### 2.7 The caps are provisional

30 / 45 / 40 have no experimental basis. They fall inside the translation-ratio band (20 words is about 26 to 36 characters, 25 words about 33 to 45), they match the 30 / 45 that RinStel/cste-zh reached independently, and the 40-character clause line comes from 阮一峰 and Huawei's 2004 guide.

Calibration protocol: run the no-skill baseline first (8 document scenarios, sonnet) and take the sentence-length distribution from the linter. Compute P70 for procedural and descriptive sentences separately and round up to a multiple of 5. Use the calibrated value when procedural lands in 25 to 35 and descriptive in 40 to 50. Otherwise keep the provisional value and say so. The 40-character clause line is not calibrated. Report only whether P90 exceeds it. Results go in section 5 of this file, not in the README. Before calibration the README publishes no number about cap effectiveness.

Rejected: deriving the caps from "one English word equals 1.5 characters". Verification found that this ratio cites speech information-rate research. Applied to written character counts it is a category error.

### 2.8 Measurement

Linter `evals/jm_lint.py`: standard library only, Python 3.9. Document metrics: sentence over cap, clause over cap, weak verb, marked 被 passive, banned modal, semicolon, dash join, ordinal chain (two or more of 首先 / 其次 / 最后 in one paragraph), "不是 X 而是 Y", 的 chain, slop word, synonym rotation. A colon that introduces a list is not measured on its own: a regex cannot tell it from a legal list lead-in such as 运行以下命令：, and on the reply side the sentence and list-item counts cover it. Reply metrics (reader_check): sentences with list items counted, sentences over cap, dashes, bold, headers, list items, opener, closer. The unit is violations per 1000 characters, not per 100 words.

A weak verb counts only when a verbal noun follows it (处理, 分析, 检查, 配置, 部署, 验证, and so on). 进行中 and 进行到一半 do not count. This trades missed hits such as 进行深度学习 for fewer false positives, because false positives make users turn the hook off.

Rejected jieba in the core: its 450 ms cold start slows every PostToolUse hook, and no published number needs segmentation. It stays a future `--segmented` option. Rejected pkuseg and HanLP: they download models.

The headline number is the reduction in reader-visible reply defects (sentences over cap + dashes + bold + headers + list items, pooled over 16 replies) plus the count of replies within five sentences. Document violations per 1000 characters is the secondary number. This order is the direct lesson of WHY-USELESS: a linter-violation headline measures obedience to your own linter, not what a reader sees.

Judge: blind pairwise, both orders, averaged. Three criteria: can a non-native technical reader understand each sentence on one read, can each instruction be followed as written, is there filler or AI tone. The judge is a Claude model and the texts are Claude output, so family bias is possible. The README says so.

### 2.9 Benchmark

The scenarios are written for Chinese developers' environments, not translated from SimpleEnglish. Eight documents: README intro, getting started, troubleshooting, error text, incident report, release notes, shorten one step, architecture overview, all about a fictional CLI tool datasync (it syncs MySQL tables to Alibaba Cloud OSS as Parquet). Eight replies, each with one term to explain (幂等, 分库分表, 证书链, 消费积压, OOMKilled, 令牌桶, 回填, 缓存失效).

Generation happens inside the Claude Code desktop app. No CLI, no API. The plugin ships one command, `/jianming-zhongwen:bench` (`commands/bench.md`). It reads the two scenario files and, for each scenario, spawns one subagent with the Agent tool. The baseline condition gets the scenario prompt only. The skill condition gets the rule block from `prompts/system-prompt.md` before the prompt. A subagent does not see the main session, so the baseline is not contaminated by the plugin's injection. The model is pinned to sonnet. Outputs go to `evals/results/<run>/` as `<condition>__<scenario>.txt`, with a manifest that records the model, the session's effort setting, the date, and the SHA256 of the rule block. Reply scenarios run twice. The judge is also a subagent, blind pairwise, both orders. Scoring, aggregation, and comparison stay in Python (`score_text_dir.py`, `check_numbers.py`).

Rejected installing the `claude` CLI: user decision. Rejected a direct API path: it needs an API key and is a second generation code path. Cost: a subagent inherits the session's effort setting and cannot pin it the way `claude -p --effort low` does. The manifest records it and the README says so. Other people's reruns can differ. The README publishes only numbers that `check_numbers.py` can recompute from the committed raw files.

Two confounds measured on 2026-09-09. A subagent sees every installed skill, and a task such as "write a README" can trigger this plugin's skill or simple-english's. That list is fixed when the session starts: `plugin disable` and even `plugin uninstall` during a session do not change what subagents of that session see, as three probes showed. So disable both plugins with the app's bundled Claude Code binary first, then start a new session for generation, and `enable` them after. A subagent also inherits the user's global `~/.claude/CLAUDE.md`, which asks for short sentences and one term per meaning, so it pushes the baseline toward the skill's direction. The measured improvement can only be understated, not overstated. Leave that file alone, record `user_claude_md: present` in the manifest, and say in the README that the baseline is "this machine's Claude Code, with the user's own CLAUDE.md". When the Workflow tool is available, generate with it and pin effort to low, as SimpleEnglish does. The manifest's `harness` field records which tool ran.

### 2.10 Plugin, testing, and updates

One repository is both marketplace and plugin. `marketplace.json` has `source` set to `./`. Install is two commands, update is one: `claude plugin update jianming-zhongwen@jianming-zhongwen`, or the `/plugin` screen in the app. The `version` field in `plugin.json` drives updates. A commit without a version bump never reaches users, so the release process makes the bump a hard step.

Testing installs from GitHub, the same path users take. The Code tab of the desktop app has no `/plugin` command, so use the Claude Code binary the app bundles at `~/Library/Application Support/Claude/claude-code/<version>/claude.app/Contents/MacOS/claude`. It writes the same registry the app reads, `~/.claude/plugins/`. Commands: `plugin marketplace add heichaowo/jianming-zhongwen`, `plugin install jianming-zhongwen@jianming-zhongwen`; after a push, `plugin marketplace update jianming-zhongwen`, then `plugin update jianming-zhongwen@jianming-zhongwen`. `plugin update` keys on the version field, so a change under test also needs a version bump, or an uninstall and reinstall. Verify: open a new session and confirm the rule block is injected, write a reply over five sentences and confirm the Stop hook message.

Rejected a local directory marketplace. The official docs do not allow a plugin source that points at the marketplace root itself, and a symlink to the repository is skipped because it resolves outside the marketplace, which leaves a wrapper copy plus a sync script. Tried once on 2026-09-09, it worked, but it duplicates "test updates from GitHub", so it was deleted.

Three hooks. SessionStart runs Node and writes the rule block from `prompts/system-prompt.md` to stdout as plain text, as SimpleEnglish 2.0.2 does in practice, with no JSON wrapper. It is capped at 9500 characters, with a fixed short rule set as fallback when the file is missing or too long. PostToolUse runs the linter after a Write or Edit on a .md file, exits 2, advisory only, and skips `.claude` directories and every path in `JIANMING_ZHONGWEN_LINT_EXCLUDE`. Stop runs reader_check on the last reply, returns one systemMessage on a violation, and always exits 0. The Python hook reconfigures stdout and stderr to UTF-8 at startup so Chinese output works on Windows without a shell variable.

The body of `output-styles/jianming-zhongwen.md` is byte-identical to the rule block in `prompts/system-prompt.md`. `check_numbers.py` verifies this. The style is selected as `jianming-zhongwen:jianming-zhongwen`.

The single source of the version is the SKILL.md frontmatter. `check_numbers.py` verifies that `plugin.json`, `marketplace.json`, and the README badge agree. Rejected a separate VERSION file: one more file, no extra check.

Compatibility: Claude Code plugin and the skills CLI (`npx skills add heichaowo/jianming-zhongwen`). Tools without SKILL.md support paste `prompts/system-prompt.md`. Codex plugin manifests are deferred: they cannot be tested here.

### 2.11 CI and release

CI calls no model. Four steps: linter self-test, Node hook test, Python hook test, `check_numbers.py`. Python is pinned to 3.9 to match this machine. When there are no raw files, `check_numbers.py` checks only the version strings and the rule-block sync and prints that the number check was skipped. This is a bootstrap guard, not permanent logic.

Release: bump the version in SKILL.md, sync the other three places, write the CHANGELOG entry in English, run the four CI steps locally, run `/plugin validate .` in the app, commit `release: vX.Y.Z`, tag, push, create the GitHub release from the CHANGELOG. A commit that moves any published number ships the raw files with it.

Versions start at 0.1.0. Calibrated caps and published benchmark numbers make 1.0.0.

### 2.12 Copyright boundary

MIT. GB/T text is paraphrased, never copied, with links. No STE dictionary content. When citing lieflat ratios, say that its corpus is not public and third parties cannot verify it. Rule sources go in the SKILL.md frontmatter, not in narrative prose. The README is written from scratch, not translated from SimpleEnglish.

## 3. Layout

See the tree in the Chinese section. Same files.

## 4. Plan

Each phase has one observable completion check.

0. Prerequisites. Create the public repository `heichaowo/jianming-zhongwen` (MIT). Rename the local directory. Check: `gh repo view heichaowo/jianming-zhongwen` succeeds.
1. Linter. Write `evals/jm_lint.py`, `slop-zh.tsv`, and the self-test fixtures (one slop document, one clean document, one bad reply, one clean reply, plus edge cases). Check: `python3 evals/jm_lint.py --self-test` exits 0.
2. Rule files. Write SKILL.md, the three references, `prompts/system-prompt.md`, `output-styles/jianming-zhongwen.md`. Check: all three files contain 最多 5 句, the rule block is under 9000 characters, SKILL.md is under 2200 tokens.
3. Plugin. Write the two hooks, two tests, two manifests, and `commands/bench.md`. Check: both tests pass; after a local-path install in the app, a new session shows the rule block, a reply over five sentences triggers the Stop message, and `/plugin validate .` passes.
4. Benchmark scripts. Write the two scenario files, `score_text_dir.py`, `check_numbers.py`. Check: `score_text_dir.py` runs on an empty directory, `check_numbers.py` passes in skip mode.
5. CI and first release. Write `check.yml`, README, CHANGELOG, push, tag v0.1.0. Check: GitHub Actions is green.
6. Calibration and numbers. Run `/jianming-zhongwen:bench` in the app for the baseline, calibrate the caps per 2.7, run the skill condition and two reply runs, run the judge, commit raw files and numbers, release v1.0.0. Check: `check_numbers.py` passes against a README with numbers.

## 5. Measurements

Calibration results and raw benchmark distributions go here. Empty for now.
