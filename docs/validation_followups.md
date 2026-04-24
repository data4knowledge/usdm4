# d4k validation engine — follow-up items

Written 2026-04-24 at the end of a session that reconciled the d4k rule
library against CORE output on `validate/sample_usdm_1.json` and
`validate/sample_usdm_2.json`. Captures the three decisions and
investigations still open. Lives alongside `core_validation.md` (the CORE
module user guide) and `next_steps.md` (the rule coverage roadmap).

## Context

The `validate/` harness runs CORE and d4k against the same USDM JSON and
produces a rule-by-rule alignment report (`validate/compare.py`). That tool
now reconciles CORE's `CORE-NNNNNN` ids to d4k's `DDF000NN` ids via the
`authorities[].Standards[].References[].Rule_Identifier.Id` field in the
CORE rules JSON cache, so same-rule hits from both engines collapse to a
single row.

After the session's fixes (see `git log`), the headline numbers are:

| Sample    | aligned_pass | aligned_fail | core_only | d4k_only | count_mismatch |
|-----------|--------------|--------------|-----------|----------|----------------|
| sample 1  | 192          | 12           | 8         | 1        | 0              |
| sample 2  | 191          | 10           | 3         | 8        | 1              |

Sample 1 has simple data and exposes few real issues; sample 2 has a
richer, noisier payload that exercises more of the rule library. The
remaining divergences sort into three buckets described below.

## 1. DDF00247 — XHTML well-formedness vs schema validation

**Where it shows up.** Sample 2, `count_mismatch` — d4k 3 findings vs CORE
5. Same rule, same intent, different strictness.

**What's different.** d4k uses `xml.etree.ElementTree.fromstring` around a
namespaced wrapper to test whether `text` parses as XML — a
well-formedness check. CORE runs the text through a schema-aware parser
against the XHTML DTD and flags structural violations like a `<p>` placed
directly inside `<ul>` ("Element 'p' not expected, expected 'li'"). The
two EligibilityCriterionItem texts that d4k passes and CORE flags
(`INC1`, `INC3`) are well-formed XML but not valid XHTML structurally.

**Decision needed.** The DDF rule text is ambiguous — "Syntax template
text is expected to be HTML formatted". Well-formedness is a defensible
minimum; schema validation is the stricter reading CORE adopted.

**Options.**

- *Leave as-is.* d4k stays at well-formedness. Matches the DDF text
  literally but underreports vs CORE on sample 2 and any future sample
  with malformed-but-well-formed XHTML.
- *Upgrade to schema validation.* Swap the parser to `lxml` with an XHTML
  DTD. Matches CORE. Adds an `lxml` dependency and requires bundling the
  DTD (or depending on libxml2's internet catalog). Rule text stays the
  same; the check just gets stricter.

**Recommendation.** If the project is OK with `lxml`, upgrade. The whole
point of this rule is to catch malformed HTML in protocol text, and
"well-formed XML but structurally wrong" is exactly the kind of error
authors make. Schema validation closes the gap.

## 2. DDF00164 / DDF00165 — treatment of `"0"` as a section number

**Where it shows up.** Sample 2, each `d4k_only` with 1 finding on the
same instance — `NarrativeContent_1` (the Title Page) — which has
`sectionNumber: "0"`, `displaySectionNumber: false`, `sectionTitle: "Title
Page"`, `displaySectionTitle: false`.

**What's different.** d4k treats the rule symmetrically: `displayX=true`
iff `X` is truthy. Python's `bool("0")` is `True`, so d4k sees
`sectionNumber="0"` as "a number is specified" and flags the mismatch
with `displaySectionNumber=false`. CORE appears to treat `"0"` as "no
section" and passes.

**Decision needed.** Is `"0"` a valid section number (section zero) or a
sentinel for "unset"? The DDF text ("If a section number is to be
displayed then a number must be specified and vice versa") doesn't
resolve it.

**Options.**

- *Leave as-is.* d4k is defensibly strict per the rule text as written.
- *Relax to match CORE.* Treat `"0"` specially — either strip it to an
  empty string before the truthy test, or strip `"0"`-only
  sectionNumbers entirely. Risk: this is data-specific hand-tuning and
  may hide real errors elsewhere.

**Recommendation.** Leave as-is unless a canonical spec clarifies that
`"0"` is "unset". Document the choice so it isn't re-litigated.

## 3. Upstream `cdisc_rules_engine` dtype bug

**Where it shows up.** Every sample we've run produces thousands of CORE
`exec_errors` (sample 1: 2578; sample 2: 5447), and the overwhelming
majority of remaining `core_only` divergences are downstream effects of a
single class of error inside `cdisc_rules_engine`.

**Symptoms.** The explicit error on DDF00141 is:

```text
Failed to execute rule operation. Operation: codelist_extensible,
Target: None, Domain: StudyDesignPopulation, Error: You are trying to
merge on object and float64 columns for key 'codeSystemVersion'. If you
wish to proceed you should use pd.concat.
```

And on DDF00181:

```text
Cannot perform 'rand_' with a dtyped [float64] array and scalar of type
[bool].
```

The CT-check family (DDF00141, 00142, 00143, 00144, 00146) and several
record-level rules all produce spurious "finding" records whose `details`
block shows the lookups returned `null` for every derived variable
(`$codelist_extensible`, `$value_for_code`, `$code_for_decode_value`,
etc.) — meaning CORE's internal CT-lookup couldn't complete, and the
rule fell through to a generic "not in codelist" message.

**What this implies.** CORE's internal DataFrame for CT packages has
`codeSystemVersion` typed as `float64` (likely because the pandas
JSON/CSV reader inferred numeric for an all-missing column in one of the
cached packages), while the incoming USDM data carries `codeSystemVersion`
as strings like `"2023-12-15"`. When CORE merges the two, pandas refuses
the `object`-vs-`float64` join.

**Action.**

- Draft a minimal reproducer against the cached CT JSON and the incoming
  USDM shape; file upstream at
  https://github.com/cdisc-org/cdisc-rules-engine.
- Until fixed: treat `core_only` findings on DDF00114, 00141, 00142,
  00143, 00144, 00146, 00181, 00187 as noise, not d4k gaps. d4k passes
  these correctly when its own lookup machinery can confirm the codes
  are in the codelist.

**Impact once fixed.** Around 8 of the remaining 11 `core_only` rows
across samples 1 and 2 should flip to either `aligned_pass` or
`aligned_fail`, clearing most of the outstanding noise.

## Not follow-ups — for the record

d4k *is* legitimately stricter than CORE on the current samples in these
cases, and this is by design, not by bug:

- **DDF00082** (d4k_only) — d4k validates the JSON against
  `schema/usdm_v4-0-0.json`. CORE handles schema-shape checks outside
  its rule engine. Scope difference.
- **DDF00051, 00075, 00084, 00097, 00155, 00166, 00249** (d4k_only on
  sample 2) — d4k's `_ct_check` and helpers complete correctly when
  CORE's dtype merge fails, surfacing real CT-membership issues CORE
  can't verify. Keep flagging.
- **DDF00073** (previously count_mismatch 623 vs 2 on sample 2) — rule
  was emitting one failure per Code instance; re-written this session to
  emit one per `(codeSystem, codeSystemVersion)` group to match CORE's
  `$record_count` granularity. Now aligned_fail.
