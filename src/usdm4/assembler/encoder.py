from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder
from usdm4.api.alias_code import AliasCode


class Encoder:
    MODULE = "usdm4.encoder.encoder.Encoder"
    PHASE_MAP = [
        (
            ["0", "PRE-CLINICAL", "PRE CLINICAL"],
            {"code": "C54721", "decode": "Phase 0 Trial"},
        ),
        (["1", "I"], {"code": "C15600", "decode": "Phase I Trial"}),
        (["1-2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
        (["1/2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
        (["1/2/3"], {"code": "C198366", "decode": "Phase I/II/III Trial"}),
        (["1/3"], {"code": "C198367", "decode": "Phase I/III Trial"}),
        (["1A", "IA"], {"code": "C199990", "decode": "Phase Ia Trial"}),
        (["1B", "IB"], {"code": "C199989", "decode": "Phase Ib Trial"}),
        (["2", "II"], {"code": "C15601", "decode": "Phase II Trial"}),
        (["2-3", "II-III"], {"code": "C15694", "decode": "Phase II/III Trial"}),
        (["2A", "IIA"], {"code": "C49686", "decode": "Phase IIa Trial"}),
        (["2B", "IIB"], {"code": "C49688", "decode": "Phase IIb Trial"}),
        (["3", "III"], {"code": "C15602", "decode": "Phase III Trial"}),
        (["3A", "IIIA"], {"code": "C49687", "decode": "Phase IIIa Trial"}),
        (["3B", "IIIB"], {"code": "C49689", "decode": "Phase IIIb Trial"}),
        (["4", "IV"], {"code": "C15603", "decode": "Phase IV Trial"}),
        (["5", "V"], {"code": "C47865", "decode": "Phase V Trial"}),
    ]

    def __init__(self, builder: Builder, errors: Errors):
        self._builder: Builder = builder
        self._errors: Errors = errors

    def phase(self, text: str) -> AliasCode:
        phase = text.upper().replace("PHASE", "").strip() if text else ""
        for tuple in self.PHASE_MAP:
            if phase in tuple[0]:
                entry = tuple[1]
                cdisc_phase_code = self._builder.cdisc_code(
                    entry["code"],
                    entry["decode"],
                )
                self._errors.info(
                    f"Trial phase '{phase}' decoded as '{entry['code']}', '{entry['decode']}'",
                    location=KlassMethodLocation(self.MODULE, "phase"),
                )
                return self._builder.alias_code(cdisc_phase_code)
        cdisc_phase_code = self._builder.cdisc_code(
            "C48660",
            "[Trial Phase] Not Applicable",
        )
        self._errors.warning(
            f"Trial phase '{phase}' not decoded",
            location=KlassMethodLocation(self.MODULE, "_get_phase"),
        )
        return self._builder.alias_code(cdisc_phase_code)
