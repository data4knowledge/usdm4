# Next Steps

This repo's current slice: which open issues are being worked, in what order. **Rate of change: weekly — rewritten wholesale, never appended to.** A finished item is deleted; its record is the entry in `memory.md`.

The docs: `aims.md` (what the package is for), `issues.md` (open problems, `N<n>`),
`spec/` (designs — `spec/timeline_assembler.md`), `cre_issues.md` (CORE vs d4k reference),
`lessons_learned.md` (durable lessons).

State of the rule library: all 210 V4 DDF rules covered (207 implemented, 3 delegated to
DDF00082's schema check).

## Next steps (2026-09-27)

Normal development: one issue at a time, gate is tests and pins. The three-machine arrangement
(A/B/C) is dropped. Test inputs are written here in `usdm4`'s structured form — nothing waits on
`protocol_corpus` ground truth.

0. **M11 CT tool (udp_prism N45; GitHub 81, branch `81-m11-ct-from-terminology-file`):**
   built 2026-10-06, `pytest` green, closing comment written. Merge, close and release;
   usdm4_protocol 75 and usdm4_fhir 46 raise their `usdm4>=` pin to that release. N26 (`""`
   passes a required string) is for DDF, not code.
0a. **M11 1.1.2 inputs (udp_prism N6; GitHub 83, branch `83-assembler-m11-112-fields`):**
   built 2026-10-07, full suite green (Dave). Merge, close and release; usdm4_protocol then
   feeds the new keys (its issue), and usdm4_fhir exports / imports them (its issue).
1. N24.1 — one import path for the package in tests. First: every later fix needs tests that
   test what they appear to.
2. N22, N23 — the validators must not report a clean result when rules did not run.
3. The small bugs: N14–N21, then N1.
4. N24.2–N24.11 in number order, one at a time; N24.4 and N24.5 together, N24.6 and N24.7
   together.
5. Then N2 (from CORE-000938), N11, N3.

