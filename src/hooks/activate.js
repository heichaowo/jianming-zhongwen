#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

// Claude Code caps hook stdout at about 10,000 characters. Anything above that is
// written to a file and replaced by a preview, which defeats the hook.
const MAX_CHARS = 9500;

const FALLBACK_CONTEXT = `简明技术中文规则已自动加载

技术写作按简明技术中文的规则：短句，实义动词，条件在前，情态词只用 必须 / 建议 / 可以 / 能 / 可能，一词一义，不动代码、命令和报错原文。回复只用散文，最多 5 句，第一句给答案，不用破折号。`;

const HEADER = [
  '简明技术中文规则已自动加载',
  '',
  '不用等用户点名，直接按下面的规则写。完整规则和检查模式在本插件的 skills/jianming-zhongwen/SKILL.md，做检查时读它。',
  '',
].join('\n');

function candidates(pluginRoot, hookDirectory, relative) {
  const roots = [];
  if (pluginRoot) {
    roots.push(pluginRoot);
  }
  roots.push(path.join(hookDirectory, '..', '..'), path.join(hookDirectory, '..'));
  return roots.map((root) => path.join(root, ...relative));
}

function promptCandidates(pluginRoot, hookDirectory) {
  return candidates(pluginRoot, hookDirectory, ['prompts', 'system-prompt.md']);
}

function readFirstFile(list) {
  for (const candidate of list) {
    try {
      return fs.readFileSync(candidate, 'utf8');
    } catch (error) {
      // Missing, unreadable, or a directory: try the next candidate.
    }
  }
  return '';
}

function stripFrontmatter(content) {
  return content.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '');
}

// prompts/system-prompt.md is a page for people: a title, a paragraph that says
// where to paste the block, the rule block between two "---" lines, then a
// short variant. The model gets the fenced block only.
function ruleBlock(content) {
  const fence = /^---[ \t]*\r?$/m;
  const first = content.search(fence);
  if (first === -1) {
    return content;
  }
  const rest = content.slice(first).replace(fence, '');
  const second = rest.search(fence);
  return second === -1 ? rest : rest.slice(0, second);
}

function buildContext(promptText) {
  if (!promptText) {
    return FALLBACK_CONTEXT;
  }
  const out = HEADER + ruleBlock(stripFrontmatter(promptText)).trim();
  if (out.length > MAX_CHARS) {
    process.stderr.write(`jianming-zhongwen hook: payload is ${out.length} characters, over the ${MAX_CHARS} cap; sending the fallback rules\n`);
    return FALLBACK_CONTEXT;
  }
  return out;
}

function main() {
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || process.env.PLUGIN_ROOT;
  process.stdout.write(buildContext(readFirstFile(promptCandidates(pluginRoot, __dirname))));
}

if (require.main === module) {
  main();
}

module.exports = {
  FALLBACK_CONTEXT,
  MAX_CHARS,
  buildContext,
  promptCandidates,
  readFirstFile,
  ruleBlock,
  stripFrontmatter,
};
