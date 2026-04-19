import datetime
import dateutil.parser as parser
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder
from usdm4.api.alias_code import AliasCode
from usdm4.api.code import Code
from usdm4.assembler.normalisation import (
    KIND_COERCED,
    KIND_UNMAPPED,
    record_normalisation,
)


class Encoder:
    MODULE = "usdm4.encoder.encoder.Encoder"

    ZERO_DURATION = "PT0M"

    PHASE_MAP = [
        (
            ["0", "PRE-CLINICAL", "PRE CLINICAL"],
            {
                "code": "C54721",
                "m11_decode": "Early Phase 1",
                "cdisc_decode": "Phase 0 Trial",
            },
        ),
        (
            ["1", "I"],
            {
                "code": "C15600",
                "m11_decode": "Phase 1",
                "cdisc_decode": "Phase I Trial",
            },
        ),
        (
            ["1-2"],
            {
                "code": "C15693",
                "m11_decode": "Phase 1/Phase 2",
                "cdisc_decode": "Phase I/II Trial",
            },
        ),
        (
            ["1/2"],
            {
                "code": "C15693",
                "m11_decode": "Phase 1/Phase 2",
                "cdisc_decode": "Phase I/II Trial",
            },
        ),
        (
            ["1/2/3"],
            {
                "code": "C198366",
                "m11_decode": "Phase 1/Phase 2/Phase 3",
                "cdisc_decode": "Phase I/II/III Trial",
            },
        ),
        (
            ["1/3"],
            {
                "code": "C198367",
                "m11_decode": "Phase 1/Phase 3",
                "cdisc_decode": "Phase I/III Trial",
            },
        ),
        (
            ["1A", "IA"],
            {"code": "C199990", "m11_decode": None, "cdisc_decode": "Phase Ia Trial"},
        ),
        (
            ["1B", "IB"],
            {"code": "C199989", "m11_decode": None, "cdisc_decode": "Phase Ib Trial"},
        ),
        (
            ["2", "II"],
            {
                "code": "C15601",
                "m11_decode": "Phase 2",
                "cdisc_decode": "Phase II Trial",
            },
        ),
        (
            ["2-3", "II-III"],
            {
                "code": "C15694",
                "m11_decode": "Phase 2/Phase 3",
                "cdisc_decode": "Phase II/III Trial",
            },
        ),
        (
            ["2A", "IIA"],
            {"code": "C49686", "m11_decode": None, "cdisc_decode": "Phase IIa Trial"},
        ),
        (
            ["2B", "IIB"],
            {"code": "C49688", "m11_decode": None, "cdisc_decode": "Phase IIb Trial"},
        ),
        (
            ["3", "III"],
            {
                "code": "C15602",
                "m11_decode": "Phase 3",
                "cdisc_decode": "Phase III Trial",
            },
        ),
        (
            ["3A", "IIIA"],
            {"code": "C49687", "m11_decode": None, "cdisc_decode": "Phase IIIa Trial"},
        ),
        (
            ["3B", "IIIB"],
            {"code": "C49689", "m11_decode": None, "cdisc_decode": "Phase IIIb Trial"},
        ),
        (
            ["4", "IV"],
            {
                "code": "C15603",
                "m11_decode": "Phase 4",
                "cdisc_decode": "Phase IV Trial",
            },
        ),
        (
            ["5", "V"],
            {"code": "C47865", "m11_decode": None, "cdisc_decode": "Phase V Trial"},
        ),
        (
            ["2/3/4", "V"],
            {
                "code": "C217024",
                "m11_decode": "Phase 2/Phase 3/Phase 4",
                "cdisc_decode": None,
            },
        ),
    ]
    STATUS_MAP = [
        (["APPROVED"], {"code": "C25425", "decode": "Approved"}),
        (["DRAFT", "DFT"], {"code": "C85255", "decode": "Draft"}),
        (["FINAL"], {"code": "C25508", "decode": "Final"}),
        (["OBSOLETE"], {"code": "C63553", "decode": "Obsolete"}),
        (
            ["PENDING", "PRENDING REVIEW"],
            {"code": "C188862", "decode": "Pending Review"},
        ),
    ]
    REASON_MAP = [
        {"code": "C207612", "decode": "Regulatory Agency Request To Amend"},
        {"code": "C207608", "decode": "New Regulatory Guidance"},
        {"code": "C207605", "decode": "IRB/IEC Feedback"},
        {"code": "C207609", "decode": "New Safety Information Available"},
        {"code": "C207606", "decode": "Manufacturing Change"},
        {"code": "C207602", "decode": "IMP Addition"},
        {"code": "C207601", "decode": "Change In Strategy"},
        {"code": "C207600", "decode": "Change In Standard Of Care"},
        {
            "code": "C207607",
            "decode": "New Data Available (Other Than Safety Data)",
        },
        {"code": "C207604", "decode": "Investigator/Site Feedback"},
        {"code": "C207611", "decode": "Recruitment Difficulty"},
        {
            "code": "C207603",
            "decode": "Inconsistency And/Or Error In The Protocol",
        },
        {"code": "C207610", "decode": "Protocol Design Error"},
        {"code": "C17649", "decode": "Other"},
        {"code": "C48660", "decode": "Not Applicable"},
    ]

    BOOLEAN_MAP = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
    }

    SCOPE_MAP = {
        "COUNTRY": {"code": "C25464", "decode": "Country"},
        "GLOBAL": {"code": "C68846", "decode": "Global"},
        "REGION": {"code": "C41129", "decode": "Region"},
    }

    def __init__(self, builder: Builder, errors: Errors):
        self._builder: Builder = builder
        self._errors: Errors = errors

    def phase(self, text: str) -> AliasCode:
        # Preserve the raw input for normalisation reporting; the decoded
        # value is reported alongside so downstream consumers can show the
        # user exactly what was coerced.
        source = text or ""
        phase = source
        for word in ["PHASE", "TRIAL"]:
            phase = phase.upper().replace(word, "").strip() if phase else ""
        for tuple in self.PHASE_MAP:
            if phase in tuple[0]:
                entry = tuple[1]
                code = entry["code"]
                m11_decode = entry["m11_decode"]
                decode = m11_decode if m11_decode else entry["cdisc_decode"]
                phase_code = self._builder.cdisc_code(code, decode)
                self._errors.info(
                    f"Trial phase '{phase}' decoded as '{code}', '{decode}', {'using M11 decode' if m11_decode else 'using CDISC decode'}",
                    location=KlassMethodLocation(self.MODULE, "phase"),
                )
                if not m11_decode:
                    self._errors.warning(
                        f"Could not find M11 decode for phase '{phase}'"
                    )
                # Structured trace for the M11 validator. record_normalisation
                # suppresses the entry when source already matches the canonical
                # value (case/whitespace insensitive) so well-formed inputs
                # don't generate noise.
                record_normalisation(
                    self._errors,
                    element="Trial Phase",
                    source=source,
                    normalised=decode,
                    kind=KIND_COERCED,
                    location=KlassMethodLocation(self.MODULE, "phase"),
                )
                return self._builder.alias_code(phase_code)
        cdisc_phase_code = self._builder.cdisc_code(
            "C48660",
            "[Trial Phase] Not Applicable",
        )
        self._errors.warning(
            f"Trial phase '{phase}' not decoded",
            location=KlassMethodLocation(self.MODULE, "phase"),
        )
        record_normalisation(
            self._errors,
            element="Trial Phase",
            source=source,
            normalised="[Trial Phase] Not Applicable",
            kind=KIND_UNMAPPED,
            location=KlassMethodLocation(self.MODULE, "phase"),
        )
        return self._builder.alias_code(cdisc_phase_code)

    def document_status(self, text: str) -> Code:
        source = text or ""
        status = source.upper().strip() if source else ""
        for tuple in self.STATUS_MAP:
            if status in tuple[0]:
                entry = tuple[1]
                cdisc_code = self._builder.cdisc_code(
                    entry["code"],
                    entry["decode"],
                )
                self._errors.info(
                    f"Document status '{status}' decoded as '{entry['code']}', '{entry['decode']}'",
                    location=KlassMethodLocation(self.MODULE, "document_status"),
                )
                record_normalisation(
                    self._errors,
                    element="Document Status",
                    source=source,
                    normalised=entry["decode"],
                    kind=KIND_COERCED,
                    location=KlassMethodLocation(self.MODULE, "document_status"),
                )
                return cdisc_code
        cdisc_code = self._builder.cdisc_code("C85255", "Draft")
        self._errors.warning(
            f"Document status '{status}' not decoded",
            location=KlassMethodLocation(self.MODULE, "document_status"),
        )
        record_normalisation(
            self._errors,
            element="Document Status",
            source=source,
            normalised="Draft",
            kind=KIND_UNMAPPED,
            location=KlassMethodLocation(self.MODULE, "document_status"),
        )
        return cdisc_code

    def amendment_reason(self, reason_str: str):
        source = reason_str or ""
        if reason_str:
            parts = reason_str.split(":")
            if len(parts) >= 2:
                reason_text = parts[1].strip()
                for reason in self.REASON_MAP:
                    if reason_text.upper() == reason["decode"].upper():
                        self._errors.info(
                            f"Amendment reason '{reason_text}' decoded as '{reason['code']}', '{reason['decode']}'"
                        )
                        code = self._builder.cdisc_code(
                            reason["code"], reason["decode"]
                        )
                        record_normalisation(
                            self._errors,
                            element="Amendment Reason",
                            source=reason_text,
                            normalised=reason["decode"],
                            kind=KIND_COERCED,
                            location=KlassMethodLocation(
                                self.MODULE, "amendment_reason"
                            ),
                        )
                        return {"code": code, "other_reason": ""}
            self._errors.warning(
                f"Unable to decode amendment reason '{reason_str}'",
                location=KlassMethodLocation(self.MODULE, "amendment_reason"),
            )
            code = self._builder.cdisc_code("C17649", "Other")
            record_normalisation(
                self._errors,
                element="Amendment Reason",
                source=source,
                normalised="Other",
                kind=KIND_UNMAPPED,
                location=KlassMethodLocation(self.MODULE, "amendment_reason"),
            )
            return {"code": code, "other_reason": parts[-1].strip()}
        self._errors.warning(
            "Amendment reason not decoded, missing text",
            location=KlassMethodLocation(self.MODULE, "amendment_reason"),
        )
        code = self._builder.cdisc_code("C17649", "Other")
        return {"code": code, "other_reason": "No reason text found"}

    def geographic_scope(self, type: str) -> Code:
        source = type or ""
        if type and type.upper() in self.SCOPE_MAP:
            scope = self.SCOPE_MAP[type.upper()]
            record_normalisation(
                self._errors,
                element="Geographic Scope",
                source=source,
                normalised=scope["decode"],
                kind=KIND_COERCED,
                location=KlassMethodLocation(self.MODULE, "geographic_scope"),
            )
            return self._builder.cdisc_code(scope["code"], scope["decode"])
        self._errors.warning(
            f"Geographic scope not set for '{type}', setting global scope",
            location=KlassMethodLocation(self.MODULE, "geographic_scope"),
        )
        scope = self.SCOPE_MAP["GLOBAL"]
        record_normalisation(
            self._errors,
            element="Geographic Scope",
            source=source,
            normalised=scope["decode"],
            kind=KIND_UNMAPPED,
            location=KlassMethodLocation(self.MODULE, "geographic_scope"),
        )
        return self._builder.cdisc_code(scope["code"], scope["decode"])

    def to_date(self, text: str) -> datetime.datetime | None:
        if not text:
            return None
        input_text = text.strip()
        if not input_text:
            return None
        try:
            return parser.parse(input_text)
        except (ValueError, TypeError, OverflowError):
            # Unparseable is a normal case — the docx often carries non-date
            # text here (e.g. "Not applicable", "Refer to electronic
            # signature…", "TBD"). Keep the log short; no traceback needed.
            preview = input_text[:80] + ("…" if len(input_text) > 80 else "")
            self._errors.warning(
                f"No date detected for '{preview}'; treating as absent.",
                location=KlassMethodLocation(self.MODULE, "to_date"),
            )
            return None
        except Exception as e:
            # Unexpected — keep the full traceback for these.
            self._errors.exception(
                f"Unexpected error decoding date text '{text}'",
                e,
                location=KlassMethodLocation(self.MODULE, "to_date"),
            )
            return None

    def iso8601_duration(self, value: int, unit: str) -> str:
        try:
            if value == 0:
                return self.ZERO_DURATION
            unit_text: str = unit.strip()
            if unit_text.upper() in ["Y", "YRS", "YR", "YEARS", "YEAR"]:
                return f"P{value}Y"
            if unit_text.upper() in ["MTHS", "MTH", "MONTHS", "MONTH"]:
                return f"P{value}M"
            if unit_text.upper() in ["W", "WKS", "WK", "WEEKS", "WEEK"]:
                return f"P{value}W"
            if unit_text.upper() in ["D", "DYS", "DY", "DAYS", "DAY"]:
                return f"P{value}D"
            if unit_text.upper() in ["H", "HRS", "HR", "HOURS", "HOUR"]:
                return f"PT{value}H"
            if unit_text.upper() in ["M", "MINS", "MIN", "MINUTES", "MINUTE"]:
                return f"PT{value}M"
            if unit_text.upper() in ["S", "SECS", "SEC", "SECONDS", "SECOND"]:
                return f"PT{value}S"
            self._errors.warning(
                f"Failed to encode ISO8601 duration of '{value}, {unit}'"
            )
            return self.ZERO_DURATION
        except Exception as e:
            self._errors.exception(
                f"Failed to encode ISO8601 duration of '{value}, {unit}'",
                e,
                location=KlassMethodLocation(self.MODULE, "iso8601_duration"),
            )
            return self.ZERO_DURATION

    def to_boolean(self, text: str) -> bool:
        return False if text is None else self.BOOLEAN_MAP.get(text.lower(), False)
