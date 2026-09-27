# USDM4 — open issues

Problems that need solving. Open items only: when one is closed, delete its row and its
section (the session log in `next_steps.md` records how it was closed). `next_steps.md` says
which of these is being worked and in what order.

Numbered `N<n>`; numbers are never reused. A GitHub issue, when one is raised, is noted on the
row.

| #  | Issue | Area |
|----|-------|------|
| N1 | Placeholder procedure code `12345` in every assembled USDM | assembler |
| N2 | Minimum assembled study fails CORE and d4k rules | assembler |
| N3 | Small timeline output defects | assembler |
| N4 | Amendment enrollment geographic scope untested | assembler |
| N5 | `test_example_2` xfail — 339 findings on `example_2.json` | rules / fixtures |
| N6 | d4k–CORE divergences with no verdict (DDF00031, 00045, 00087, 00088) | rules |
| N7 | Upstream CRE bugs not yet raised with the CRE team | CORE |
| N8 | CORE engine output always suppressed | CORE |
| N9 | `udp_prism` as a validation set — keep or retire | validation |
| N10 | ~87 hand-authored rule tests have no behavioural fixture | rules / tests |
| N11 | Empty population label fails assembly | assembler |
| N12 | Timings in a unit other than the anchor's are not converted | assembler |
| N13 | Convert is USDM3 → USDM4 but nothing says or checks so | convert |

---

## N1 — Placeholder procedure code `12345`

`src/usdm4/assembler/timeline/build.py` (~line 390) builds each activity's `Procedure` with
`Code(code="12345", codeSystem="LOINC", codeSystemVersion="1")`. Every assembled USDM carries a
made-up code presented as real LOINC. Either a real code comes from the input, or the
`Procedure` is not built without one.

## N2 — Minimum assembled study fails CORE and d4k rules

The minimum `AssemblerInput` fixture (`tests/usdm4/integration/conftest.py`) does not assemble
into a conformant study. Both engines' integration tests are regression detectors on today's
failures, not conformance tests.

**d4k.** `tests/usdm4/integration/test_assembler_to_d4k.py` pins ceilings — at most 12 failing
rules, 15 findings, 0 rule exceptions — and fails if any is exceeded. The strict "all rules
pass" test is `xfail(strict=False)`. Which rules fail is not recorded; list them before working
this. As they clear, lower the ceilings, then drop them and the xfail.

**CORE.** `tests/usdm4/integration/test_assembler_to_core.py` pins the failing rule ids as
`_KNOWN_FAILING_RULES`: CORE-000815, 000938, 000973, 001016, 001036, 001054, 001065, 001076,
001077. The test is a regression detector — it passes while the set is unchanged. The ones
with a known cause:

- **CORE-000938** (DDF00126, schema cardinality) — `StudyAmendment.changes`,
  `InterventionalStudyDesign.arms` and `.studyCells` emitted as `[]` where the schema needs at
  least one.
- **CORE-000973** — exactly one `StudyRole(code="sponsor")`. No code path creates it;
  `IdentificationAssembler` wires the sponsor through the identifier scope only. Smallest fix:
  `_create_organization` emits a sponsor `StudyRole` when the org's role is `sponsor`.
- **CORE-001016** — `ScheduleTimeline.plannedDuration` on the main timeline. `build.py`
  (~line 811) sets it `None`; the input has no duration.
- **CORE-001036** — at least one primary endpoint. `StudyDesignInput` has no objectives or
  endpoints; needs schema and an assembler.

The rest are not decoded. A 2026-05-02 bisection tried three fixture additions (sponsor
identifier, demographics with age range, activity BCs); all three cleared some rules and
introduced more, so all were reverted. The BC variant produced 8 CORE-001013 name-uniqueness
errors — look at that before any fixture references BCs.

## N3 — Small timeline output defects

- `Paricipant identified` — `PLANNED_ENTRY_CONDITION` in `build.py` (~line 87). Typo kept on
  purpose so far (spec R1); fixing it changes every pin.
- `≥ 1 weeks` — `gate_condition` and `render_delay` pluralise without checking the value.
- Instances in a second period or a copied timeline are named by de-duplication (`D1-2`,
  `D-1-2`, `ED-2`), not by period or timeline.

## N4 — Amendment enrollment geographic scope untested

`AmendmentsAssembler._enrollment_geographic_scope` (2026-06-18, branch
`39-further-ich-m11-updates`) derives the enrollment scope from the amendment scope. No unit
tests exist and the `udp_prism` end-to-end check (TCBCPT_03 renders "Locally") was never
confirmed. Tests needed: global, country in `countries`, country in `unknown`, region, site
fallback. Known gap: a site- or cohort-scoped amendment has no C207412 code, so it falls back
to Global with a warning.

## N5 — `test_example_2` xfail

`tests/usdm4/test_package.py::test_example_2` is `xfail(strict=True)`: the V4 rule library
fires 339 findings on `example_2.json` across ~30 rules. When the file produces none, the
xfail turns XPASS and the run fails — the signal to remove the marker.

- **Fixture drift** — DDF00051 (timing type labels, not decodes), DDF00157, DDF00199, DDF00218
  (invalid CT codes/decodes), DDF00075 (activities with no leaf references). Fix the fixture,
  or for DDF00075 reconsider the rule's strictness.
- **Rule interpretation** — DDF00010 checks `(instanceType, name)` model-wide, matching CORE's
  JSONata; the rule text says "same parent class", and `SubjectEnrollment` names repeat across
  amendments. The mirror-CORE policy (`cre_issues.md`) says keep it; the question is whether
  this is a case for a spec change.
- **The rest** — the xfail reason lists them. The list is a pre-rewrite snapshot; re-run and
  triage per finding before working it.

## N6 — d4k–CORE divergences with no verdict

From the CRE 0.16.0 corpus baseline (`validate/corpus_cre_0_16/engine_diff.md`); rows and
counts in `cre_issues.md` § *Divergence index*.

- **DDF00031** (d4k over, 213 files) — timing FK consistency. Not categorised.
- **DDF00045** (d4k over, 25 files) — the V3 rule kept alongside V4 DDF00194; CORE runs only
  DDF00194. Retire the V3 duplicate, or show the over-fire is a real finding DDF00194 misses.
- **DDF00087 / DDF00088** (d4k over, 210 / 177 files) — first-chain-head selection. Needs a
  design decision.

When one is decided, move its row in `cre_issues.md` to the matching category and delete it
here.

## N7 — Upstream CRE bugs not yet raised

`cre_issues.md` issues 1–10 each carry a *Suggested fix* for the CRE team. None is recorded as
raised. Issue 5 (execution errors mixed with findings) is no longer a cost to us: since #54
`_classify_errors` follows the engine's own `executionStatus`, with the string set kept only as
a fallback for items that carry none. Ask for the rest anyway; each still needs a workaround here.

## N8 — CORE engine output always suppressed

`core_validator.py` `_run_validation` redirects stdout/stderr to a `StringIO` unconditionally.
During the CRE 0.16.0 upgrade this hid the engine's own tracebacks. Make it switchable (env var
or flag) for diagnostic runs.

## N9 — `udp_prism` as a validation set

A plan to run the rules over 21 `udp_prism` protocols predates the 234-protocol corpus baseline,
which already covers what they exercise. Decide: give it its own frozen baseline under
`validate/`, or drop the plan.

## N10 — Hand-authored rule tests without fixtures

About 87 hand-authored rule tests have their positive/negative fixture cases marked
`@pytest.mark.skip` (metadata-only coverage). A minimal JSON per rule makes each a behavioural
test — roughly 15 minutes a pair. Start with the structurally unusual ones: DDF00189 (mutex),
DDF00196 (1:1 dict of sets), DDF00124 (regex ref), DDF00010 (model-wide uniqueness), DDF00161
(preorder walk).

## N11 — Empty population label fails assembly

The population input (`src/usdm4/assembler/schema/`) defaults `label` to `""`.
`PopulationAssembler` (`population_assembler.py` ~line 92) builds the `StudyDesignPopulation`
`name` as `data["label"].upper()…`, and the API model requires `name` to have at least one
character. An input with no population label therefore fails Pydantic validation instead of
assembling with a warning. Seen on the 19 CORP* corpus protocols (2026-05-01). Decide: require
a label in the input schema, or have the assembler supply a name and warn.

## N12 — Timings in a unit other than the anchor's are not converted

The timeline spec said a column timed in a different unit from the anchor is converted where
exact (weeks to days, hours to minutes). It never was: `plan.py` (`_interval`,
`interval_from_anchor`) warns and uses the column's printed number as its distance from the anchor, ignoring where
the anchor sits and the crossing-zero rule. `_convert` exists and is used only for cycle
lengths.
Spec: `docs/spec/timeline_assembler.md` R4.6.

## N13 — Convert is USDM3 → USDM4 but nothing says or checks so

`Convert.convert` (`src/usdm4/convert/convert.py`) rewrites a USDM3 study into USDM4 shape
and stamps `usdmVersion` with the v4 model version. It never reads the input's
`usdmVersion`, so any file is converted as if it were USDM3. The README calls it "transform
USDM data structures between formats". The test inputs (`tests/usdm4/test_files/convert/`)
say `usdmVersion` `2.11.0` in two files (a pre-release number for what became USDM3) and
`3.0.0` in two. Needed: say it is USDM3 → USDM4 (README, docstring), check the input version
(accept 3.x and 2.11, warn otherwise), and label the fixtures `3.0.0`.

