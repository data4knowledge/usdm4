# USDM4 — Working Memory

The session log. **Rate of change: per session, appended. Never retired.**

An entry is a dated record of what happened, and the file's one job is total
recall — a cold start on another machine reads this plus `docs/lessons_learned.md`
plus `CLAUDE.md` and resumes without the chat. Nothing is removed.

Entries are appended at the END, headed `## YYYY-MM-DD — title` and nothing else.
Several entries may share a date. The plan is `docs/next_steps.md`, rewritten
wholesale; it holds no log.

Every session that works a `usdm4` issue is entered here in full, whichever
Claude project drove it. Entries up to 2026-10-02 were moved verbatim from the
Session Log formerly in `docs/next_steps.md`.

References in entries up to 2026-09-27 to "design § n" and "plan …" are to
`timeline_assembler_design.md` and `timeline_assembler_plan.md`, both retired that day (git
history). The design's as-built sections are now in the entries they belong to; the current
rules and decisions (U4-n) are in `docs/spec/timeline_assembler.md`.

## 2026-11-07 — GitHub 98, 99, 100: 1.1.2 assignment in extensions, repeating secondary reasons and sponsor-type parties

**Repos.** usdm4 (this work). Callers: usdm4_protocol 144 to 146, usdm4_fhir 58 to 60. Pointer in udp_prism `memory.md` 2026-11-07.

**What it was.** M11 1.1.2 Intervention Assignment Method and stratification have a USDM 4.1 home that 4.0 lacks, and usdm4 validates against the strict 4.0 schema, so they cannot sit on the design as attributes. An amendment could hold one secondary reason, and a sponsor-type party one organisation; M11 and sheet 03.13 repeat both.

**What changed.**
- Assembler inputs — `randomisation_type`, `other_assignment_method`, `stratified`, held in extension `IA_EXT_URL` with children for method, stratified, other method and randomisation type (GitHub 98); list `secondary` (99); list `roles` (100).
- Accessors — `secondary_reasons_as_text()`, `co_sponsor_organizations()` and siblings.
- `tests/conftest.py` — parses the packaged CT and BC caches once per run. The 15 new tests reloaded them each time; a Builder is shared and the file stays.
- `docs/issues.md` — N28: M11 Primary Reason repeats on an element USDM holds once.

**Figures.** `pytest` passed on each branch (Dave). Version 0.31.0.

**Rejected.** Attributes on the design under 4.0: the schema refuses them.

**Found, not this work.** None.
