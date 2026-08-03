"""
Data classes for CDISC CORE validation results.
"""

from dataclasses import dataclass, field
from typing import Any

from simple_error_log.errors import Errors


@dataclass
class CoreRuleFinding:
    """A single validation finding from a CORE rule."""

    rule_id: str
    description: str
    message: str
    errors: list[dict[str, Any]]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @staticmethod
    def _sanitise_value(obj: Any) -> Any:
        """
        Recursively convert non-standard types (e.g. jsonata JList) to
        plain Python types so the result is safe for JSON/YAML serialisation.
        """
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, dict):
            return {str(k): CoreRuleFinding._sanitise_value(v) for k, v in obj.items()}
        # Catch list, tuple, and list-like objects (e.g. jsonata.utils.JList)
        try:
            return [CoreRuleFinding._sanitise_value(item) for item in obj]
        except TypeError:
            return str(obj)

    @staticmethod
    def _format_error(error: dict[str, Any]) -> dict[str, Any]:
        """
        Extract the useful fields from a raw CORE engine error dict
        into a concise, readable form.
        """
        if not isinstance(error, dict):
            return {"detail": str(error)}

        formatted: dict[str, Any] = {}

        # Instance identity
        if "instance_id" in error:
            formatted["instance_id"] = error["instance_id"]
        if "entity" in error:
            formatted["entity"] = error["entity"]
        if "path" in error:
            formatted["path"] = error["path"]

        # Pull useful fields out of the value sub-dict
        value = error.get("value")
        if isinstance(value, dict):
            for key in ("name", "sectionNumber", "sectionTitle"):
                if key in value:
                    formatted[key] = value[key]
            # Include any check-related or domain-specific fields
            # (exclude the redundant identity keys already captured)
            skip = {
                "instanceType",
                "id",
                "path",
                "name",
                "sectionNumber",
                "sectionTitle",
            }
            extras = {
                k: CoreRuleFinding._sanitise_value(v)
                for k, v in value.items()
                if k not in skip
                and not k.endswith(".id")
                and not k.endswith(".name")
                and not k.endswith(".version")
            }
            if extras:
                formatted["details"] = extras
        elif value is not None:
            formatted["value"] = CoreRuleFinding._sanitise_value(value)

        # Any top-level error message from the engine
        if "error" in error and error["error"]:
            formatted["error"] = error["error"]
        if "message" in error and error["message"]:
            formatted["message"] = error["message"]

        return formatted if formatted else {"raw": error}


@dataclass
class CoreValidationResult:
    """
    Complete results from a CDISC CORE validation run.

    Attributes:
        findings: List of validation findings (real data issues).
        execution_errors: List of rule execution errors
            (rules that don't apply to this file's structure).
        rules_executed: Total number of rules that were executed.
        rules_skipped: Number of rules skipped (known bugs).
        ct_packages_available: Number of CT packages known to CDISC Library.
        ct_packages_loaded: List of CT package names actually loaded.
        file_path: Path to the validated file.
        version: USDM version used for validation.
    """

    findings: list[CoreRuleFinding] = field(default_factory=list)
    execution_errors: list[dict[str, Any]] = field(default_factory=list)
    rules_executed: int = 0
    rules_skipped: int = 0
    ct_packages_available: int = 0
    ct_packages_loaded: list[str] = field(default_factory=list)
    file_path: str = ""
    version: str = "4-0"

    @property
    def is_valid(self) -> bool:
        """True if no validation findings were reported."""
        return len(self.findings) == 0

    @property
    def finding_count(self) -> int:
        """Total number of individual validation errors across all findings."""
        return sum(f.error_count for f in self.findings)

    @property
    def execution_error_count(self) -> int:
        return len(self.execution_errors)

    def format_text(self) -> str:
        """Format results as a human-readable text report."""
        lines = []
        lines.append("=" * 60)
        lines.append("USDM CORE Validation Report")
        lines.append("=" * 60)
        lines.append(f"File: {self.file_path}")
        lines.append(f"USDM Version: {self.version}")
        lines.append(f"Rules executed: {self.rules_executed}")
        lines.append(f"Rules skipped: {self.rules_skipped}")
        lines.append(f"CT packages available: {self.ct_packages_available}")
        loaded = (
            ", ".join(self.ct_packages_loaded) if self.ct_packages_loaded else "None"
        )
        lines.append(f"CT packages loaded: {loaded}")
        lines.append("")

        if self.is_valid and self.execution_error_count == 0:
            lines.append("Validation PASSED - No issues found.")
            return "\n".join(lines)

        if self.is_valid:
            lines.append("Validation PASSED - No data issues found.")
            lines.append(
                f"(Note: {self.execution_error_count} rule execution errors - "
                "these rules may not apply to all entity types)"
            )
            return "\n".join(lines)

        lines.append(f"Found {self.finding_count} validation issue(s):")
        if self.execution_error_count > 0:
            lines.append(f"(Plus {self.execution_error_count} rule execution errors)")
        lines.append("-" * 60)

        for finding in self.findings:
            lines.append(f"\nRule: {finding.rule_id}")
            if finding.description:
                lines.append(f"Description: {finding.description}")
            if finding.message:
                lines.append(f"Message: {finding.message}")
            lines.append(f"Errors ({finding.error_count}):")
            for error in finding.errors[:10]:
                fe = CoreRuleFinding._format_error(error)
                entity = fe.get("entity", "")
                iid = fe.get("instance_id", "")
                path = fe.get("path", "")
                parts = []
                if entity and iid:
                    parts.append(f"{entity} ({iid})")
                if path:
                    parts.append(path)
                details = fe.get("details")
                if details:
                    extras = ", ".join(f"{k}={v}" for k, v in details.items())
                    parts.append(extras)
                lines.append(f"  - {' | '.join(parts) if parts else error}")
            if finding.error_count > 10:
                lines.append(f"  ... and {finding.error_count - 10} more")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to a JSON-serialisable dictionary."""
        return {
            "file": self.file_path,
            "version": self.version,
            "is_valid": self.is_valid,
            "rules_executed": self.rules_executed,
            "rules_skipped": self.rules_skipped,
            "finding_count": self.finding_count,
            "execution_error_count": self.execution_error_count,
            "ct_packages_available": self.ct_packages_available,
            "ct_packages_loaded": self.ct_packages_loaded,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "description": f.description,
                    "message": f.message,
                    "error_count": f.error_count,
                    "errors": [CoreRuleFinding._format_error(e) for e in f.errors],
                }
                for f in self.findings
            ],
        }

    def to_errors(self) -> Errors:
        """Convert findings to an :class:`~simple_error_log.errors.Errors` instance."""
        errors = Errors()
        for finding in self.findings:
            for error in finding.errors:
                formatted = CoreRuleFinding._format_error(error)
                # Build a concise, human-readable message
                parts = []
                entity = formatted.get("entity", "")
                instance_id = formatted.get("instance_id", "")
                path = formatted.get("path", "")
                if entity and instance_id:
                    parts.append(f"{entity} ({instance_id})")
                elif instance_id:
                    parts.append(instance_id)
                if path:
                    parts.append(f"at {path}")
                location = " ".join(parts)

                detail = formatted.get("detail", "")
                description = finding.message or finding.description
                if detail:
                    description = f"{description}: {detail}"
                if location:
                    message = f"{description} [{location}]"
                else:
                    message = description
                errors.add(message, error_type=finding.rule_id)
        return errors
