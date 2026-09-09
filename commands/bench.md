---
description: 生成 benchmark 的原始输出，基线和 skill 两个条件，再用 Python 打分
---

# 跑 benchmark

参数 `$ARGUMENTS`：`docs`、`replies`、`judge`，或者留空（先 docs 再 replies）。可以加 `--run <名字>`，默认 `run-<今天日期>`。可以加 `--only baseline` 或 `--only skill`，只跑一个条件。批次目录是 `evals/results/<run>/`。

这条命令代替 SimpleEnglish 的 `claude -p`。生成由子代理完成，打分由 Python 完成。不要自己打分。

## 准备

1. 子代理看得到已安装的全部 skill，而且列表在会话开始时定下，会话中途禁用或卸载插件都不生效。所以先禁用本插件和 simple-english 这类写作插件，再新开一个会话跑生成。不这样做，写 README 的任务会触发 skill，基线就不干净。桌面 App 用自带的内核：`~/Library/Application Support/Claude/claude-code/<版本>/claude.app/Contents/MacOS/claude plugin disable <插件>@<marketplace>`。生成完再 `enable`。
2. 用 Bash 读 `evals/scenarios.json` 和 `evals/reply_scenarios.json`。
3. 用 Bash 取规则块：`prompts/system-prompt.md` 里两条 `---` 之间的文字。算它的 SHA256：`python3 -c "import re,hashlib,pathlib;t=pathlib.Path('prompts/system-prompt.md').read_text();print(hashlib.sha256(re.split(r'^---[ \t]*$',t,flags=re.M)[1].strip().encode()).hexdigest())"`。
4. 如果 `evals/results/<run>/manifest.json` 不存在，写一个：`{"model": "sonnet", "effort": "<钉住的 effort，钉不住就写 inherited>", "date": "<今天>", "rule_block_sha256": "<上一步的值>", "harness": "claude-code-agent-tool 或 claude-code-workflow-tool", "plugins_disabled": [<禁用了哪些>], "user_claude_md": "present 或 absent"}`。有 Workflow 工具时用它生成，effort 钉为 low。

## 生成

对每个场景、每个条件，用 Agent 工具起一个子代理。`model` 固定 `sonnet`，`run_in_background` 设为 false。一次最多起 4 个。已经存在且非空的输出文件跳过，中断后可以续跑。

- `baseline` 条件的提示词：场景的 `prompt` 原文，末尾加一行「只返回正文，不用工具。」
- `skill` 条件的提示词分四段，段之间空一行。第一段是规则块。第二段是 `---`。第三段是「任务：」加场景的 `prompt`。第四段是「只返回正文，不解释规则，不用工具。」

不要往 baseline 的提示词里塞任何规则。子代理看不到这个会话，所以插件注入的规则不会污染基线。

文档场景写到 `evals/results/<run>/docs/<条件>__<id>.txt`。回复场景跑两轮，写到 `evals/results/<run>/reply1/` 和 `evals/results/<run>/reply2/`，文件名同样是 `<条件>__<id>.txt`。把子代理返回的最终文本原样写入，不改一个字。

## 打分

```
python3 evals/score_text_dir.py evals/results/<run>
```

它读上面三个目录，输出 Markdown 表格。把输出存为 `evals/results/<run>/RESULTS.md`。

## 评委（参数是 judge 时）

对每个回复场景，取 `reply1` 里 baseline 和 skill 两份文本。起两个评委子代理，`model` 用 `sonnet`。第一次 A 是 baseline，第二次 A 是 skill。评委提示词：

> 下面是回答同一个技术问题的两份中文回复，标为 A 和 B。判断哪份对技术读者更有用，标准有三条。非母语读者能不能一遍读懂每一句。每条指令能不能照做。有没有废话、开场白、结束语和 AI 腔。不看礼貌，不看详细。只返回 JSON，形如 {"winner": "A"}，值是 A、B 或 tie。
>
> A：
> <文本>
>
> B：
> <文本>

把两次结果和映射写到 `evals/results/<run>/judge/<id>.json`：`{"id": ..., "order1": {"A": "baseline", "B": "skill", "winner": ...}, "order2": {"A": "skill", "B": "baseline", "winner": ...}}`。

## 收尾

把 RESULTS.md 的表格贴给用户。不改 README，不改 SKILL.md。README 的数字只能由 `evals/check_numbers.py` 校验通过后再写。
