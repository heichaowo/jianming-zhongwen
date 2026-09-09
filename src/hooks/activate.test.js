const test = require('node:test');
const assert = require('node:assert/strict');

const {
  FALLBACK_CONTEXT,
  MAX_CHARS,
  buildContext,
  promptCandidates,
  readFirstFile,
  ruleBlock,
  stripFrontmatter,
} = require('./activate.js');

test('ruleBlock returns the text between the first two --- lines', () => {
  const page = '# 标题\n\n说明段落。\n\n---\n\n规则一。\n规则二。\n\n---\n\n## 短版本\n\n短。\n';
  assert.equal(ruleBlock(page).trim(), '规则一。\n规则二。');
});

test('ruleBlock returns everything when there is no fence', () => {
  assert.equal(ruleBlock('只有规则。'), '只有规则。');
});

test('stripFrontmatter removes a YAML block at the top', () => {
  assert.equal(stripFrontmatter('---\nname: x\n---\n正文'), '正文');
  assert.equal(stripFrontmatter('正文'), '正文');
});

test('the real prompt file builds a payload with both registers and under the cap', () => {
  const text = readFirstFile(promptCandidates(undefined, __dirname));
  assert.ok(text.length > 0, 'prompts/system-prompt.md not found');
  const out = buildContext(text);
  assert.ok(out.includes('最多 5 句'));
  assert.ok(out.includes('必须'));
  assert.ok(out.includes('不超过 30 字'));
  assert.ok(!out.includes('短版本'), 'the short variant must stay out of the payload');
  assert.ok(out.length <= MAX_CHARS);
});

test('an empty prompt file gives the fallback rules', () => {
  assert.equal(buildContext(''), FALLBACK_CONTEXT);
});

test('an oversized payload gives the fallback rules', () => {
  // A title line first, so the fences read as the rule block and not as YAML frontmatter.
  const big = '# 标题\n\n---\n' + '字'.repeat(MAX_CHARS + 10) + '\n---\n';
  assert.equal(buildContext(big), FALLBACK_CONTEXT);
});

test('readFirstFile skips missing candidates', () => {
  assert.equal(readFirstFile(['/nonexistent/a.md', '/nonexistent/b.md']), '');
});
