# Changelog

## 1.0.0, 2026-09-10

- First measured release, run `evals/results/run-2026-09-09` (sonnet, effort
  low, generated inside Claude Code). Replies: reader-visible defects 322 to 2
  over 16 replies, 14 of 16 within five sentences. Documents: 12.94 to 7.36
  violations per 1000 characters. Blind judge with one vote per order: 7 wins,
  0 ties, 9 losses, and the two orders disagree on 5 of 8 scenarios, so the
  judge shows position bias, not a verdict.
- Known cost: the five-sentence cap can turn "it depends" into an assertion
  (the consumer-lag scenario).

## 0.1.1, 2026-09-09

- Calibrated the sentence caps on the first baseline run (8 documents, 27
  Chinese sentences, sonnet at low effort). Procedural stays at 30 字 (P70
  30). Descriptive goes from 45 to 50 字 (P70 49). The clause line stays at
  40 字. Details in docs/design.md section 5.
- The error-message scenario now asks for Chinese text. The baseline wrote it
  in English.

## 0.1.0, 2026-09-09

- First version. SKILL.md with a document register (16 rules) and a reply
  register (7 rules). A standard-library linter with a self-test. A Claude
  Code plugin with SessionStart, PostToolUse, and Stop hooks, an output style,
  and the `/jianming-zhongwen:bench` command that generates benchmark output
  inside Claude Code.
- The sentence caps (30 / 45 / 40 字) are provisional until the calibration
  run recorded in docs/design.md section 5. No benchmark numbers yet.
