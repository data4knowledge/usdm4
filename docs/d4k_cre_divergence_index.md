# d4k ↔ CRE divergence index

The single answer to "have we seen this divergence before?" Each row points
at the authoritative explanation so a re-investigation isn't needed.

**Source of truth.** The corpus baseline at
`validate/corpus_cre_0_16/engine_diff.md` (234 protocols, CRE 0.16.0). All
counts and direction columns below are derived from it. When the corpus is
re-run on a future CRE version, refresh this table — it's frozen against
what the engine actually emitted, not against opinion.

**Last verified.** Corpus run captured against CRE 0.16.0; baseline frozen
2026-05-02. The bucket totals at the top of `engine_diff.md` are: 5 d4k
under-reporting, 13 d4k over-reporting, 195 aligned, 1 core-only.

**Reading the table.**

- **Direction** — `under` means CORE finds errors d4k misses; `over` means
  d4k finds errors CORE doesn't.
- **Files** — count of corpus protocols (out of 234) where the divergence
  fires.
- **Category** — what kind of divergence this is. The seven categories are
  defined in the legend below the table; they're the only legitimate
  outcomes of an investigation. Anything that doesn't fit is "open".
- **Authority** — the doc + section that explains the call. Stop
  investigating once you've read this entry; if you disagree, update the
  authority doc, not the rule.

**Meta-policy.** When a rule's text and CORE's JSONata disagree, mirror
CORE in the d4k rule and note the disagreement in the rule's source
comment. CORE is the reference implementation; the disagreement gets
fixed by a spec/CORE change, not by behavioural divergence in the Python.
This policy prevents re-litigation; it lives in `cre_issues.md`'s
"Rule-text-vs-CORE-JSONata disagreement" section (originally captured in
`lessons_learned.md` §16.4).


## Active divergences (corpus baseline)

### d4k under-reporting — CORE finds errors d4k misses

| DDF id    | CORE id      | Files | Category    | Authority                                                  |
|-----------|--------------|------:|-------------|------------------------------------------------------------|
| DDF00010  | CORE-001013  |   204 | CRE issue 8 | `cre_issues.md` §8 (cross-reference traversal)             |
| DDF00093  | CORE-000873  |   230 | CRE issue 8 | `cre_issues.md` §8 (cross-reference traversal)             |
| DDF00094  | CORE-000814  |   204 | CRE issue 8 | `cre_issues.md` §8 (cross-reference traversal)             |
| DDF00151  | CORE-000834  |   204 | CRE issue 8 | `cre_issues.md` §8 (cross-reference traversal)             |
| DDF00181  | CORE-001068  |   230 | CRE issue 8 | `cre_issues.md` §8 (cross-reference traversal)             |

All five are the same upstream bug: CORE's data traversal visits a
`GovernanceDate` shared between `StudyVersion.dateValues` and
`StudyDefinitionDocumentVersion.dateValues` once per parent reference
instead of once per instance. d4k's id-keyed iteration is correct;
CORE's count or detection is inflated/phantom. No d4k change required.


### d4k over-reporting — d4k finds errors CORE doesn't

| DDF id    | CORE id      | Files | Category                  | Authority                                                                  |
|-----------|--------------|------:|---------------------------|----------------------------------------------------------------------------|
| DDF00031  | —            |   213 | Open / investigate        | this index — needs categorisation (timing FK consistency)                  |
| DDF00045  | —            |    25 | Legit data findings       | this index — V3 rule retained alongside V4 DDF00194; corpus has empty addresses |
| DDF00075  | —            |   216 | d4k stricter (CT / scope) | `cre_issues.md` "Defensibly d4k-stricter" appendix                          |
| DDF00084  | —            |   234 | CRE issue 7 + d4k stricter | `cre_issues.md` §7 + appendix                                              |
| DDF00087  | —            |   210 | Open d4k design call      | `next_steps.md` §3 (first-chain-head selection) — needs decision           |
| DDF00088  | CORE-001048  |   177 | Open d4k design call      | `next_steps.md` §3 (first-chain-head selection) — needs decision           |
| DDF00110  | —            |   200 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix (CT-membership family)   |
| DDF00140  | —            |   227 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix (CT-membership family)   |
| DDF00155  | —            |   234 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix (CT-membership family)   |
| DDF00166  | —            |   234 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix; `next_steps.md` §1     |
| DDF00200  | —            |   227 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix (CT-membership family)   |
| DDF00227  | —            |   234 | Legit data findings       | `corpus_extractor_fixes.md` — corpus extractor not populating `studyType`  |
| DDF00259  | —            |   227 | d4k stricter (CT)         | `cre_issues.md` "Defensibly d4k-stricter" appendix (CT-membership family)   |

The CT-membership cluster (DDF00075, 084, 110, 140, 155, 166, 200, 259)
all share one fingerprint: d4k's `_ct_check` and rule-side helpers
complete correctly when CORE's `codelist_extensible` operation drops into
no-data mode (issue 7). Where d4k flags a real invalid decode or
codeSystemVersion, CORE returns `Pass-or-NA` because its operation
silently emitted an execution-error sentinel that the wrapper filters
out. d4k is doing real work CORE can't.

DDF00227 ("studyType missing or empty") is over-reported only because
the corpus extractor isn't populating `studyType` — the rule is firing
correctly. See `corpus_extractor_fixes.md` for the corpus-side fix
direction.

DDF00045 needs investigation: the V3 rule was retained in d4k alongside
the V4 DDF00194, and CORE's V4 catalogue runs only DDF00194. On the
corpus DDF00194 is aligned-pass (because no protocol reaches the issue 9
null-legalAddress shape — see workarounds-in-place section below) while
DDF00045 fires 25 times. Either the V3 duplicate should be retired in
the V4 library, or the over-fire is a legitimate finding the V4 rule
misses. Decide before the next corpus refresh.

DDF00031, DDF00087, DDF00088 are the three rules without a settled
category. They sit in `next_steps.md` §3 as candidates for
rule-interpretation review against real data; the corpus run made them
visible. Investigate, then move into the appropriate category.


## Workarounds in place (corpus shows aligned)

These rules would diverge under naïve implementation but the d4k Python
code carries a workaround that makes the corpus-baseline outcome
aligned. They are listed here so the workaround isn't accidentally
removed during refactoring.

| DDF id    | CORE id      | Category    | Workaround location                                          |
|-----------|--------------|-------------|--------------------------------------------------------------|
| DDF00114  | CORE-000878  | CRE issue 5/7 | `core_validator.py::_classify_errors` (sentinel filtering)  |
| DDF00141  | CORE-000857  | CRE issue 5/7 | `core_validator.py::_classify_errors` (sentinel filtering)  |
| DDF00152  | CORE-000840  | CRE issue 5/7 | `core_validator.py::_classify_errors` (sentinel filtering)  |
| DDF00161  | —            | CRE issue 10 | `rule_ddf00161.py` (multi-parent allowed-set union)         |
| DDF00194  | CORE-000971  | CRE issue 9  | `rule_ddf00194.py` iterates real Address instances; null `legalAddress` skipped |
| DDF00237  | CORE-001061  | CRE issue 5/7 | `core_validator.py::_classify_errors` (sentinel filtering)  |
| DDF00955* | CORE-000955  | CRE issue 6  | `_EXCLUDED_RULES` in `core_validator.py` (rule skipped)     |
| DDF00956* | CORE-000956  | CRE issue 6  | `_EXCLUDED_RULES` in `core_validator.py` (rule skipped)     |

`*` CORE-000955/956 are CORE rule ids without DDF mappings exposed in
`engine_diff.md`; they're maintained as CORE-id exclusions, not as DDF
rule rows. Listed here for completeness.


## Resolved between baselines

Rules that diverged in earlier runs and are now aligned. Kept here for
audit trail — if one of these starts diverging again on a future run,
read the authority doc before re-investigating.

| DDF id    | Was              | Now            | Reason                                                       |
|-----------|------------------|----------------|--------------------------------------------------------------|
| DDF00025  | under=103 (0.15.x) | aligned_fail=103 | CORE behaviour change — `cre_issues.md` "CRE 0.16.0 upgrade notes" |
| DDF00229  | under=222 (0.15.x) | aligned_fail=222 | CORE behaviour change — `cre_issues.md` "CRE 0.16.0 upgrade notes" |
| DDF00249  | over=200 (0.15.x)  | aligned (0/0/0) | d4k rule rewritten between baselines — `cre_issues.md` "Open follow-ups" |


## Open d4k design calls (no corpus signal yet)

Rules where the DDF text is genuinely ambiguous and d4k chose a
defensibly stricter reading. The corpus run shows them aligned (no
signal either way), so they're parked here rather than in the active
table — but the decision is documented so it doesn't get re-litigated.

| DDF id          | Decision                                                                                                                  | Authority             |
|-----------------|---------------------------------------------------------------------------------------------------------------------------|------------------------|
| DDF00164/00165  | d4k treats `sectionNumber="0"` as "a number is specified" (Python truthy on `"0"`); CORE treats it as "no section"        | `next_steps.md` §4     |
| DDF00187        | d4k wraps fragment as `<html>…<body><div>…</div></body></html>`; CORE wraps directly in `<body>` and flags self-namespacing wrappers | `next_steps.md` §4     |


## Refresh cadence

This index is regenerated when any of the following change:

1. **CRE upgrade.** Run the validation engines on the corpus (recipe in
   `validate/README.md`), regenerate `engine_diff.md`, then walk every
   row of this index and either confirm the category still applies or
   move the rule between sections. New divergences land in "Active
   divergences"; resolved ones move to "Resolved between baselines".
2. **d4k rule library change.** Re-run the corpus on the changed rules
   (the standard test set is faster for spot-checking; full corpus is
   the regression catch-net). If the change resolves a divergence, move
   the row.
3. **Authority-doc revision.** When `cre_issues.md` adds a new issue or
   the "Defensibly d4k-stricter" appendix grows, cross-check that any
   rule pointing to that authority is still in the right category.

Whoever refreshes the index updates the "Last verified" date at the top
and notes the CRE version in the same paragraph.


## What to do with a new divergence

1. Look it up here. If it has a row, read the authority — done.
2. If no row, work through the category legend below in order. Land on
   the first category that fits; add the row.
3. If nothing fits, mark it "Open / investigate" with a one-line
   description, then resolve to a real category before the next refresh.

### Category legend

- **CRE issue 5/6/7/8/9/10** — catalogued upstream behaviour. Authority
  is the corresponding numbered section in `cre_issues.md`.
- **d4k stricter (CT / scope / schema)** — d4k correctly does work CORE
  can't because of an upstream limitation or because d4k's scope is
  wider (e.g. DDF00082's full schema validation). Authority is the
  "Defensibly d4k-stricter" appendix in `cre_issues.md`.
- **Open d4k design call** — DDF text is ambiguous and d4k's reading is
  stricter than CORE's; documented so the call doesn't get re-asked.
  Authority is `next_steps.md` §4.
- **Legit data findings** — d4k correctly flags real protocol issues
  that CORE doesn't catch (often because of corpus extractor gaps or
  rule-scope differences). Authority is `corpus_extractor_fixes.md` or
  `next_steps.md` §1c depending on whether the data lives in the corpus
  or in test fixtures.
- **Open / investigate** — temporary state, must be resolved to one of
  the above before the next corpus refresh.
