# USDM4 — next steps

The immediate plan: which open issues are being worked, in what order, and the session log.

The docs: `aims.md` (what the package is for), `issues.md` (open problems, `N<n>`),
`spec/` (designs — `spec/timeline_assembler.md`), `cre_issues.md` (CORE vs d4k reference),
`lessons_learned.md` (durable lessons).

State of the rule library: all 210 V4 DDF rules covered (207 implemented, 3 delegated to
DDF00082's schema check).

## Next steps (2026-09-27)

Normal development: one issue at a time, gate is tests and pins. The three-machine arrangement
(A/B/C) is dropped. Test inputs are written here in `usdm4`'s structured form — nothing waits on
`protocol_corpus` ground truth.

1. N24.1 — one import path for the package in tests. First: every later fix needs tests that
   test what they appear to.
2. N22, N23 — the validators must not report a clean result when rules did not run.
3. The small bugs: N14–N21, then N1.
4. N24.2–N24.11 in number order, one at a time; N24.4 and N24.5 together, N24.6 and N24.7
   together.
5. Then N2 (from CORE-000938), N11, N3.

