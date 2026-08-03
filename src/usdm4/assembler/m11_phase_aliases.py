"""Single source for M11/CPT trial-phase preferred-term renderings.

The same NCI conceptId resolves to different preferredTerm strings in
SDTM C66737 (e.g. ``"Phase I Trial"``) and in ICH M11 / TransCelerate
CPT C217045 (e.g. ``"Phase 1"``). The CDISC SDTM library is loaded as
the canonical source for the model itself; this dict supplies the
parallel M11 rendering for the two consumers that need to translate
between them:

  - :mod:`usdm4.rules.library.rule_ddf00229` — when a document carries
    a ``Code.decode`` that is the M11 PT for an SDTM-valid code, the
    rule reports the divergence at level=Warning rather than Error.
  - :mod:`usdm4_protocol.m11.decoder.m11_decoder` — at M11 emit time,
    flips the model's SDTM-form ``Code.decode`` to the M11 form expected
    by the M11 codelist.

Three copies of this table previously existed across DDF00229,
M11Decoder, and (input-direction) Encoder.PHASE_MAP. The first two
now import from this module. The third (PHASE_MAP) is a different
shape — input strings → conceptId — and stays separate.

Source: M11 specification, codelist C217045
("ICH M11 Trial Phase Value Set Terminology"), 11 terms.

Drift guard: ``usdm4_protocol/tests/m11/elements/test_round_trip_phase.py``
exercises the full input→encode→decode→output cycle and will fail if
this dict, ``Encoder.PHASE_MAP``, or the SDTM CT cache fall out of
alignment.
"""

# NCI conceptId → M11/CPT preferredTerm string.
# Codes are listed in the order they appear in C217045 in the M11
# spec; keep this ordering when adding entries.
M11_TRIAL_PHASE_PTS: dict[str, str] = {
    "C54721": "Early Phase 1",
    "C15600": "Phase 1",
    "C15693": "Phase 1/Phase 2",
    "C198366": "Phase 1/Phase 2/Phase 3",
    "C198367": "Phase 1/Phase 3",
    "C15601": "Phase 2",
    "C15694": "Phase 2/Phase 3",
    "C217024": "Phase 2/Phase 3/Phase 4",
    "C15602": "Phase 3",
    "C217025": "Phase 3/Phase 4",
    "C15603": "Phase 4",
}
