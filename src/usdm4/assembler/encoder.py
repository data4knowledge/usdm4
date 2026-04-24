import datetime
import dateutil.parser as parser
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder
from usdm4.api.alias_code import AliasCode
from usdm4.api.code import Code


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

    # CDISC CT C99076 — Intervention Model
    INTERVENTION_MODEL_MAP = [
        (["PARALLEL"], {"code": "C82639", "decode": "Parallel Study"}),
        (
            ["CROSSOVER", "CROSS-OVER", "CROSS OVER"],
            {"code": "C82637", "decode": "Crossover Study"},
        ),
        (
            ["SEQUENTIAL", "GROUP SEQUENTIAL"],
            {"code": "C142568", "decode": "Group Sequential Design"},
        ),
        (["FACTORIAL"], {"code": "C82638", "decode": "Factorial Study"}),
        (
            ["SINGLE GROUP", "SINGLE-GROUP", "SINGLEGROUP"],
            {"code": "C82640", "decode": "Single Group Study"},
        ),
    ]
    INTERVENTION_MODEL_DEFAULT = {"code": "C82639", "decode": "Parallel Study"}

    # CDISC CT C174222 — Study Arm Type
    ARM_TYPE_MAP = [
        (
            [
                "EXPERIMENTAL",
                "EXPERIMENTAL ARM",
                "INVESTIGATIONAL",
                "INVESTIGATIONAL ARM",
            ],
            {"code": "C174266", "decode": "Investigational Arm"},
        ),
        (
            [
                "PLACEBO COMPARATOR",
                "PLACEBO COMPARATOR ARM",
                "PLACEBO CONTROL",
                "PLACEBO CONTROL ARM",
            ],
            {"code": "C174268", "decode": "Placebo Control Arm"},
        ),
        (
            ["ACTIVE COMPARATOR", "ACTIVE COMPARATOR ARM"],
            {"code": "C174267", "decode": "Active Comparator Arm"},
        ),
        (
            [
                "SHAM COMPARATOR",
                "SHAM COMPARATOR ARM",
                "SHAM INTERVENTION",
                "SHAM INTERVENTION ARM",
            ],
            {"code": "C174269", "decode": "Sham Comparator Arm"},
        ),
        (
            ["NO INTERVENTION", "NO INTERVENTION ARM"],
            {"code": "C174270", "decode": "No Intervention Arm"},
        ),
        (["CONTROL", "CONTROL ARM"], {"code": "C174226", "decode": "Control Arm"}),
        (
            [
                "TREATMENT",
                "TREATMENT ARM",
                "PROTOCOL TREATMENT",
                "PROTOCOL TREATMENT ARM",
            ],
            {"code": "C15538", "decode": "Protocol Treatment Arm"},
        ),
    ]
    ARM_TYPE_DEFAULT = {"code": "C174266", "decode": "Investigational Arm"}

    # CDISC CT C99078 — Intervention Type
    INTERVENTION_TYPE_MAP = [
        (
            ["DRUG", "PHARMACOLOGIC SUBSTANCE"],
            {"code": "C1909", "decode": "Pharmacologic Substance"},
        ),
        (["DEVICE", "MEDICAL DEVICE"], {"code": "C16830", "decode": "Medical Device"}),
        (
            [
                "BEHAVIORAL",
                "BEHAVIOURAL",
                "BEHAVIORAL INTERVENTION",
                "BEHAVIORAL THERAPY",
            ],
            {"code": "C15184", "decode": "Behavioral Intervention"},
        ),
        (
            ["PROCEDURE", "PHYSICAL MEDICAL PROCEDURE", "MEDICAL PROCEDURE"],
            {"code": "C98769", "decode": "Physical Medical Procedure"},
        ),
        (
            ["BIOLOGICAL", "BIOLOGIC", "BIOLOGICAL AGENT"],
            {"code": "C307", "decode": "Biological Agent"},
        ),
        (["VACCINE"], {"code": "C923", "decode": "Vaccine"}),
        (
            ["RADIATION", "RADIATION THERAPY"],
            {"code": "C15313", "decode": "Radiation Therapy"},
        ),
        (["GENETIC", "GENE THERAPY"], {"code": "C15238", "decode": "Gene Therapy"}),
    ]
    INTERVENTION_TYPE_DEFAULT = {"code": "C1909", "decode": "Pharmacologic Substance"}

    # CDISC CT C207417 — Study Intervention Role
    INTERVENTION_ROLE_MAP = [
        (
            [
                "INVESTIGATIONAL TREATMENT",
                "EXPERIMENTAL INTERVENTION",
                "INVESTIGATIONAL",
                "PROTOCOL AGENT",
            ],
            {"code": "C41161", "decode": "Protocol Agent"},
        ),
        (["PLACEBO COMPARATOR", "PLACEBO"], {"code": "C753", "decode": "Placebo"}),
        (
            ["BACKGROUND TREATMENT", "BACKGROUND"],
            {"code": "C165822", "decode": "Background Treatment"},
        ),
        (
            ["ACTIVE COMPARATOR", "ACTIVE CONTROL"],
            {"code": "C68609", "decode": "Active Comparator"},
        ),
        (
            ["RESCUE MEDICINE", "RESCUE MEDICATION", "RESCUE MEDICATIONS"],
            {"code": "C165835", "decode": "Rescue Medications"},
        ),
        (["CHALLENGE AGENT"], {"code": "C158128", "decode": "Challenge Agent"}),
        (
            ["DIAGNOSTIC", "DIAGNOSTIC PROCEDURE"],
            {"code": "C18020", "decode": "Diagnostic Procedure"},
        ),
    ]
    INTERVENTION_ROLE_DEFAULT = {"code": "C41161", "decode": "Protocol Agent"}

    # CDISC CT C66781 — Age Unit
    AGE_UNIT_MAP = [
        (["YEARS", "YEAR", "YR", "YRS", "Y"], {"code": "C29848", "decode": "Year"}),
        (["MONTHS", "MONTH", "MTH", "MTHS"], {"code": "C29846", "decode": "Month"}),
        (["WEEKS", "WEEK", "WK", "WKS", "W"], {"code": "C29844", "decode": "Week"}),
        (["DAYS", "DAY", "DY", "DYS", "D"], {"code": "C25301", "decode": "Day"}),
        (["HOURS", "HOUR", "HR", "HRS", "H"], {"code": "C25529", "decode": "Hour"}),
    ]
    AGE_UNIT_DEFAULT = {"code": "C29848", "decode": "Year"}

    # CDISC CT C66732 — Sex of Participants
    SEX_MAP = [
        (["MALE", "M"], {"code": "C20197", "decode": "Male"}),
        (["FEMALE", "F"], {"code": "C16576", "decode": "Female"}),
    ]
    SEX_DEFAULT = {"code": "C16576", "decode": "Female"}

    # CDISC CT C66729 — Route of Administration (AliasCode return)
    ROUTE_MAP = [
        (
            ["ORAL", "PO", "BY MOUTH"],
            {"code": "C38288", "decode": "Oral Route of Administration"},
        ),
        (
            ["INTRAVENOUS", "IV"],
            {"code": "C38276", "decode": "Intravenous Route of Administration"},
        ),
        (
            ["INTRAMUSCULAR", "IM"],
            {"code": "C28161", "decode": "Intramuscular Route of Administration"},
        ),
        (
            ["SUBCUTANEOUS", "SC", "SUBDERMAL"],
            {"code": "C38299", "decode": "Subcutaneous Route of Administration"},
        ),
        (
            ["INHALATION", "INHALED", "RESPIRATORY", "RESPIRATORY (INHALATION)"],
            {"code": "C38216", "decode": "Inhalation Route of Administration"},
        ),
        (
            ["NASAL", "INTRANASAL"],
            {"code": "C38284", "decode": "Nasal Route of Administration"},
        ),
        (
            ["RECTAL", "PR"],
            {"code": "C38295", "decode": "Rectal Route of Administration"},
        ),
        (
            ["TOPICAL", "TOP"],
            {"code": "C38304", "decode": "Topical Route of Administration"},
        ),
        (
            ["SUBLINGUAL", "SL"],
            {"code": "C38300", "decode": "Sublingual Route of Administration"},
        ),
        (["BUCCAL"], {"code": "C38193", "decode": "Buccal Route of Administration"}),
    ]
    ROUTE_DEFAULT = {"code": "C38288", "decode": "Oral Route of Administration"}

    # CDISC CT C71113 — Frequency (AliasCode return)
    FREQUENCY_MAP = [
        (
            [
                "ONCE DAILY",
                "DAILY",
                "QD",
                "ONCE PER DAY",
                "ONE TIME PER DAY",
                "PER DAY",
            ],
            {"code": "C25473", "decode": "Daily"},
        ),
        (
            ["TWICE DAILY", "BID", "TWO TIMES PER DAY", "TWO TIMES DAILY"],
            {"code": "C64496", "decode": "Twice Daily"},
        ),
        (
            ["THREE TIMES DAILY", "TID", "THREE TIMES PER DAY"],
            {"code": "C64527", "decode": "Three Times Daily"},
        ),
        (
            ["FOUR TIMES DAILY", "QID", "FOUR TIMES PER DAY"],
            {"code": "C64530", "decode": "Four Times Daily"},
        ),
        (
            ["WEEKLY", "ONCE WEEKLY", "ONE TIME PER WEEK", "ONCE PER WEEK", "QW"],
            {"code": "C64526", "decode": "Once Weekly"},
        ),
        (
            ["MONTHLY", "QM", "EVERY MONTH", "ONCE MONTHLY", "PER MONTH"],
            {"code": "C64498", "decode": "Monthly"},
        ),
        (
            ["EVERY OTHER DAY", "QOD", "Q2D", "EVERY SECOND DAY"],
            {"code": "C64525", "decode": "Every Other Day"},
        ),
        (["EVERY HOUR", "QH", "HOURLY"], {"code": "C64510", "decode": "Every Hour"}),
        (["AS NEEDED", "PRN"], {"code": "C64499", "decode": "As Needed"}),
        (["ONCE", "ONE TIME", "SINGLE DOSE"], {"code": "C64576", "decode": "Once"}),
    ]
    FREQUENCY_DEFAULT = {"code": "C25473", "decode": "Daily"}

    def __init__(self, builder: Builder, errors: Errors):
        self._builder: Builder = builder
        self._errors: Errors = errors

    def phase(self, text: str) -> AliasCode:
        phase = text
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
                return self._builder.alias_code(phase_code)
        cdisc_phase_code = self._builder.cdisc_code(
            "C48660",
            "[Trial Phase] Not Applicable",
        )
        self._errors.warning(
            f"Trial phase '{phase}' not decoded",
            location=KlassMethodLocation(self.MODULE, "phase"),
        )
        return self._builder.alias_code(cdisc_phase_code)

    def document_status(self, text: str) -> Code:
        status = text.upper().strip() if text else ""
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
                return cdisc_code
        cdisc_code = self._builder.cdisc_code("C85255", "Draft")
        self._errors.warning(
            f"Document status '{status}' not decoded",
            location=KlassMethodLocation(self.MODULE, "document_status"),
        )
        return cdisc_code

    def amendment_reason(self, reason_str: str):
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
                        return {"code": code, "other_reason": ""}
            self._errors.warning(
                f"Unable to decode amendment reason '{reason_str}'",
                location=KlassMethodLocation(self.MODULE, "amendment_reason"),
            )
            code = self._builder.cdisc_code("C17649", "Other")
            return {"code": code, "other_reason": parts[-1].strip()}
        self._errors.warning(
            "Amendment reason not decoded, missing text",
            location=KlassMethodLocation(self.MODULE, "amendment_reason"),
        )
        code = self._builder.cdisc_code("C17649", "Other")
        return {"code": code, "other_reason": "No reason text found"}

    def geographic_scope(self, type: str) -> Code:
        if type.upper() in self.SCOPE_MAP:
            scope = self.SCOPE_MAP[type.upper()]
            return self._builder.cdisc_code(scope["code"], scope["decode"])
        self._errors.warning(
            f"Geographic scope not set for '{type}', setting global scope",
            location=KlassMethodLocation(self.MODULE, "geographic_scope"),
        )
        scope = self.SCOPE_MAP["GLOBAL"]
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

    def intervention_model(self, text: str) -> Code:
        """Decode an intervention model label to a CDISC Code (codelist C99076).

        Accepts human-readable labels (Parallel, Crossover, Sequential,
        Factorial, Single Group). Empty or unknown input defaults to Parallel
        with a warning, matching how ``phase()`` degrades.
        """
        return self._lookup_code(
            text,
            self.INTERVENTION_MODEL_MAP,
            self.INTERVENTION_MODEL_DEFAULT,
            "intervention_model",
            "Intervention model",
        )

    def arm_type(self, text: str) -> Code:
        """Decode an arm type label to a CDISC Code (codelist C174222)."""
        return self._lookup_code(
            text,
            self.ARM_TYPE_MAP,
            self.ARM_TYPE_DEFAULT,
            "arm_type",
            "Arm type",
        )

    def intervention_type(self, text: str) -> Code:
        """Decode an intervention type label to a CDISC Code (codelist C99078)."""
        return self._lookup_code(
            text,
            self.INTERVENTION_TYPE_MAP,
            self.INTERVENTION_TYPE_DEFAULT,
            "intervention_type",
            "Intervention type",
        )

    def intervention_role(self, text: str) -> Code:
        """Decode an intervention role label to a CDISC Code (codelist C207417)."""
        return self._lookup_code(
            text,
            self.INTERVENTION_ROLE_MAP,
            self.INTERVENTION_ROLE_DEFAULT,
            "intervention_role",
            "Intervention role",
        )

    def age_unit(self, text: str) -> Code:
        """Decode an age unit label to a CDISC Code (codelist C66781)."""
        return self._lookup_code(
            text,
            self.AGE_UNIT_MAP,
            self.AGE_UNIT_DEFAULT,
            "age_unit",
            "Age unit",
        )

    def sex(self, text: str) -> Code:
        """Decode a sex label to a CDISC Code (codelist C66732).

        Accepts ``"MALE"`` / ``"FEMALE"`` (or ``"M"``/``"F"``). The encoder
        does not handle the composite ``"ALL"`` value — callers that need
        both sex codes should invoke this method twice.
        """
        return self._lookup_code(
            text,
            self.SEX_MAP,
            self.SEX_DEFAULT,
            "sex",
            "Sex",
        )

    def route(self, text: str) -> AliasCode:
        """Decode a route-of-administration label to an AliasCode (codelist C66729).

        Returns an ``AliasCode`` so Administration.route can hold the decoded
        value directly, mirroring how ``phase()`` returns an AliasCode.
        """
        code = self._lookup_code(
            text,
            self.ROUTE_MAP,
            self.ROUTE_DEFAULT,
            "route",
            "Route of administration",
        )
        return self._builder.alias_code(code)

    def frequency(self, text: str) -> AliasCode:
        """Decode a frequency label to an AliasCode (codelist C71113)."""
        code = self._lookup_code(
            text,
            self.FREQUENCY_MAP,
            self.FREQUENCY_DEFAULT,
            "frequency",
            "Frequency",
        )
        return self._builder.alias_code(code)

    def _lookup_code(
        self,
        text: str,
        table: list,
        default: dict,
        method_name: str,
        label: str,
    ) -> Code:
        """Shared lookup driver for the simple MAP-based encoder methods.

        Mirrors the phase()/document_status() pattern: normalise input, scan
        the table, emit an info on hit and a warning on miss (or empty
        input), fall back to the supplied default.
        """
        value = text.upper().strip() if text else ""
        for keys, entry in table:
            if value in keys:
                code = self._builder.cdisc_code(entry["code"], entry["decode"])
                self._errors.info(
                    f"{label} '{value}' decoded as '{entry['code']}', '{entry['decode']}'",
                    location=KlassMethodLocation(self.MODULE, method_name),
                )
                return code
        default_code = self._builder.cdisc_code(default["code"], default["decode"])
        self._errors.warning(
            f"{label} '{value}' not decoded; defaulting to '{default['decode']}'",
            location=KlassMethodLocation(self.MODULE, method_name),
        )
        return default_code
