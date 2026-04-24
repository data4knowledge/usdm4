"""Validate a USDM4 JSON file using the d4k rule library and write results to YAML.

This is the sibling of ``core.py``. Where ``core.py`` runs the CDISC CORE
JSONata engine, this script runs the usdm4 Python rule library
(``USDM4.validate`` → ``RulesValidation4`` → ``RulesValidationEngine``) and
emits a YAML report whose shape is easy to diff against the CORE YAML via
``compare.py``.

Output shape::

    file: <path>
    engine: d4k
    is_valid: true|false
    rules_executed: <int>
    finding_count: <int>
    counts:
      success: <int>
      failure: <int>
      exception: <int>
      not_implemented: <int>
    outcomes:
      - rule_id: DDF00010
        status: Failure
        error_count: 3
        errors:
          - message: ...
            klass: TransitionRule
            attribute: name
            path: $.Study...
            level: Error
        exception: null
"""

import argparse
import sys
from pathlib import Path

import yaml

from simple_error_log.errors import Errors
from usdm4 import USDM4
from usdm4.rules.results import RuleStatus, RulesValidationResults


def _format_outcome(rule_id: str, outcome) -> dict:
    """Convert a single RuleOutcome into a YAML-safe dict."""
    row = {
        "rule_id": rule_id,
        "status": outcome.status.value,
        "error_count": outcome.error_count,
    }
    if outcome.status == RuleStatus.FAILURE:
        formatted = []
        for err in outcome.errors.to_dict(level=Errors.DEBUG):
            location = err.get("location") or {}
            formatted.append(
                {
                    "message": err.get("message", ""),
                    "level": err.get("level", ""),
                    "klass": location.get("klass", ""),
                    "attribute": location.get("attribute", ""),
                    "path": location.get("path", ""),
                    "rule_text": location.get("rule_text", ""),
                }
            )
        row["errors"] = formatted
    if outcome.status == RuleStatus.EXCEPTION:
        row["exception"] = outcome.exception
    return row


def results_to_dict(result: RulesValidationResults, file_path: str) -> dict:
    """Serialise a RulesValidationResults into a stable, comparison-friendly dict."""
    outcomes = [
        _format_outcome(rule_id, result.outcomes[rule_id])
        for rule_id in sorted(result.outcomes)
    ]
    counts = {status.value.lower().replace(" ", "_"): 0 for status in RuleStatus}
    for outcome in result.outcomes.values():
        counts[outcome.status.value.lower().replace(" ", "_")] += 1

    return {
        "file": file_path,
        "engine": "d4k",
        "is_valid": result.is_valid,
        "rules_executed": result.count(),
        "finding_count": result.finding_count,
        "counts": counts,
        "outcomes": outcomes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate a USDM4 JSON file using the d4k rule library"
    )
    parser.add_argument("file", help="Path to USDM JSON file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output YAML file path (default: <input_stem>_d4k.yaml)",
    )
    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_name(f"{input_path.stem}_d4k.yaml")
    )

    usdm = USDM4()

    print(f"Validating {input_path} ...", file=sys.stderr)
    result = usdm.validate(str(input_path))

    output = results_to_dict(result, str(input_path))
    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"Results written to {output_path}", file=sys.stderr)
    if result.passed():
        print("Validation PASSED", file=sys.stderr)
    elif result.passed_or_not_implemented():
        not_impl = len(
            [
                o
                for o in result.outcomes.values()
                if o.status == RuleStatus.NOT_IMPLEMENTED
            ]
        )
        print(
            f"Validation PASSED (all implemented rules). "
            f"{not_impl} rule(s) not implemented.",
            file=sys.stderr,
        )
    else:
        failures = [
            o for o in result.outcomes.values() if o.status == RuleStatus.FAILURE
        ]
        exceptions = [
            o for o in result.outcomes.values() if o.status == RuleStatus.EXCEPTION
        ]
        print(
            f"Validation FAILED: {result.finding_count} finding(s) across "
            f"{len(failures)} rule(s); {len(exceptions)} rule exception(s).",
            file=sys.stderr,
        )

    sys.exit(0 if result.passed_or_not_implemented() else 1)


if __name__ == "__main__":
    main()
