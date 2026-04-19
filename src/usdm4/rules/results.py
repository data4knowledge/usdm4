"""
Results from a usdm4 rule library validation run.

Shape mirrors :class:`usdm4.core.core_validation_result.CoreValidationResult`
so the two sibling engines (CDISC CORE JSONata, usdm4 Python library) expose
a consistent contract to callers:

    engine                 result type               flat log exit
    ---------------------  ------------------------  -----------------
    CDISC CORE (JSONata)   CoreValidationResult      .to_errors()
    usdm4 library (Py)     RulesValidationResults    .to_errors()

The external consumer (``study_definitions_workbench``) reads two things
off this class: ``passed_or_not_implemented()`` as a gate, and
``to_dict()`` as a flat row-per-error list fed into a Jinja template
at ``validate/partials/results.html``. The row keys the template
consumes are contract: ``rule_id``, ``status``, ``message``, ``level``,
``klass``, ``attribute``, ``path``, ``exception``. Any simplification
of ``_row()`` must preserve these keys for as long as that template
still renders rows from this engine (currently until usdm3 retires).
"""

from dataclasses import dataclass, field
from enum import Enum

from simple_error_log.errors import Errors
from usdm4.rules.rule_template import ValidationLocation


class RuleStatus(str, Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"
    EXCEPTION = "Exception"
    NOT_IMPLEMENTED = "Not Implemented"


@dataclass
class RuleOutcome:
    """Outcome of executing a single rule against a USDM document."""

    rule_id: str
    status: RuleStatus
    errors: Errors = field(default_factory=Errors)
    exception: str | None = None

    @property
    def error_count(self) -> int:
        return self.errors.count()


@dataclass
class RulesValidationResults:
    """
    Results from running the usdm4 rule library against a USDM JSON file.

    Parallel in shape to
    :class:`usdm4.core.core_validation_result.CoreValidationResult`.
    """

    outcomes: dict[str, RuleOutcome] = field(default_factory=dict)

    # ---- writer API used by engine.py ---------------------------------------

    def add_success(self, rule: str) -> None:
        self.outcomes[rule] = RuleOutcome(rule, RuleStatus.SUCCESS)

    def add_failure(self, rule: str, errors: Errors) -> None:
        self.outcomes[rule] = RuleOutcome(rule, RuleStatus.FAILURE, errors=errors)

    def add_exception(
        self, rule: str, exception: Exception, traceback: str = ""
    ) -> None:
        text = f"{exception}\n\n{traceback}" if traceback else str(exception)
        self.outcomes[rule] = RuleOutcome(rule, RuleStatus.EXCEPTION, exception=text)

    def add_not_implemented(self, rule: str) -> None:
        self.outcomes[rule] = RuleOutcome(rule, RuleStatus.NOT_IMPLEMENTED)

    # ---- query API ----------------------------------------------------------

    def count(self) -> int:
        return len(self.outcomes)

    @property
    def finding_count(self) -> int:
        return sum(o.error_count for o in self.outcomes.values())

    @property
    def is_valid(self) -> bool:
        return self.passed()

    def passed(self) -> bool:
        return all(o.status == RuleStatus.SUCCESS for o in self.outcomes.values())

    def passed_or_not_implemented(self) -> bool:
        return all(
            o.status in (RuleStatus.SUCCESS, RuleStatus.NOT_IMPLEMENTED)
            for o in self.outcomes.values()
        )

    def by_status(self, status: RuleStatus) -> list[RuleOutcome]:
        return [o for o in self.outcomes.values() if o.status == status]

    # ---- rendering ----------------------------------------------------------

    def to_dict(
        self,
        include_success: bool = False,
        include_not_implemented: bool = False,
    ) -> list[dict]:
        """
        Flat row-per-error list, sorted by rule id.

        Defaults drop Success / NotImplemented rows (the phantom rows
        every current caller filters out). Pass ``include_success=True``
        / ``include_not_implemented=True`` to restore the pre-refactor
        full-shape output.

        Row keys for a Failure/Exception are identical to the
        pre-refactor output so YAML baselines in
        ``tests/usdm4/test_files/convert/*_errors.yaml`` do not churn.

        Warnings are preserved — we pass ``level=Errors.DEBUG`` through
        so rules constructed at ``RuleTemplate.WARNING`` still surface.
        """
        keep = {RuleStatus.FAILURE, RuleStatus.EXCEPTION}
        if include_success:
            keep.add(RuleStatus.SUCCESS)
        if include_not_implemented:
            keep.add(RuleStatus.NOT_IMPLEMENTED)

        rows: list[dict] = []
        for rule_id in sorted(self.outcomes):
            outcome = self.outcomes[rule_id]
            if outcome.status not in keep:
                continue
            errors = outcome.errors.to_dict(level=Errors.DEBUG)
            if not errors:
                rows.append(self._row(outcome, error=None))
            else:
                for error in errors:
                    rows.append(self._row(outcome, error=error))
        return rows

    def to_errors(self) -> Errors:
        """
        Flatten failure evidence into a single
        :class:`simple_error_log.errors.Errors` instance.

        Bridge method for callers that speak ``Errors`` everywhere else
        in usdm4 (Builder, Assembler, load, loadd).
        """
        merged = Errors()
        for outcome in self.outcomes.values():
            if outcome.status == RuleStatus.FAILURE:
                merged.merge(outcome.errors)
        return merged

    def format_text(self) -> str:
        """Human-readable report (mirrors ``CoreValidationResult.format_text``)."""
        lines = [
            "=" * 60,
            "USDM4 Rule Library Validation Report",
            "=" * 60,
            f"Rules executed: {self.count()}",
        ]
        for status in RuleStatus:
            lines.append(f"  {status.value}: {len(self.by_status(status))}")
        lines.append(f"Finding count: {self.finding_count}")
        lines.append("")

        if self.passed():
            lines.append("Validation PASSED.")
            return "\n".join(lines)

        lines.append(f"Validation FAILED ({self.finding_count} finding(s)).")
        lines.append("-" * 60)
        for outcome in self.by_status(RuleStatus.FAILURE):
            lines.append(f"\n{outcome.rule_id}:")
            for error in outcome.errors.to_dict(level=Errors.DEBUG):
                loc = error.get("location") or {}
                head = ".".join(
                    x for x in (loc.get("klass", ""), loc.get("attribute", "")) if x
                )
                tail = f" @ {loc.get('path')}" if loc.get("path") else ""
                lines.append(f"  - {head}{tail}: {error.get('message', '')}")
        for outcome in self.by_status(RuleStatus.EXCEPTION):
            lines.append(f"\n{outcome.rule_id}: EXCEPTION")
            lines.append(f"  {outcome.exception}")
        return "\n".join(lines)

    # ---- back-compat --------------------------------------------------------

    @property
    def _items(self) -> dict[str, dict]:
        """
        Compatibility shim for ``tests/usdm4/test_package.py``, whose
        ``dump_validation_result`` helper reaches into ``result._items``
        directly. Canonical accessor is :attr:`outcomes`. Remove once
        that test migrates.
        """
        return {
            rule_id: {
                "status": outcome.status.value,
                "errors": (
                    outcome.errors.to_dict(level=Errors.DEBUG)
                    if outcome.status == RuleStatus.FAILURE
                    else None
                ),
                "exception": outcome.exception,
            }
            for rule_id, outcome in self.outcomes.items()
        }

    # ---- internals ----------------------------------------------------------

    @staticmethod
    def _row(outcome: RuleOutcome, error: dict | None) -> dict:
        """
        Build one flat row. Keys match the pre-refactor output exactly:
        ``rule_id``, ``status``, ``exception``, ``level``, ``message``,
        ``type``, ``timestamp``, plus the five
        ``ValidationLocation.headers()`` keys (``rule``, ``rule_text``,
        ``klass``, ``attribute``, ``path``) initialised to "" and
        overwritten from the error's location dict when present.
        """
        row = {
            "rule_id": outcome.rule_id,
            "status": outcome.status.value,
            "exception": outcome.exception,
            "level": error.get("level", "") if error else "",
            "message": error.get("message", "") if error else "",
            "type": error.get("type", "") if error else "",
            "timestamp": error.get("timestamp", "") if error else "",
        }
        # Keep ValidationLocation.headers() initialisation so row shape
        # is stable even when an error carries a different ErrorLocation
        # subclass. Unknown location keys are dropped, matching pre-
        # refactor behaviour.
        for key in ValidationLocation.headers():
            row[key] = ""
        if error:
            for key, value in (error.get("location") or {}).items():
                if key in ValidationLocation.headers():
                    row[key] = value
        return row
