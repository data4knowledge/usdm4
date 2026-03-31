"""Validate a USDM4 JSON file using CDISC CORE rules and write results to YAML."""

import argparse
import sys
from pathlib import Path

import yaml

from usdm4 import USDM4


def main():
    parser = argparse.ArgumentParser(
        description="Validate a USDM4 JSON file using CDISC CORE rules"
    )
    parser.add_argument("file", help="Path to USDM JSON file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output YAML file path (default: <input_stem>_core.yaml)",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Cache directory for CDISC resources",
    )
    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_name(
        f"{input_path.stem}_core.yaml"
    )

    usdm = USDM4(cache_dir=args.cache_dir)

    print(f"Validating {input_path} ...", file=sys.stderr)
    errors = usdm.validate_core(str(input_path), cache_dir=args.cache_dir)

    output = errors.to_dict()
    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"Results written to {output_path}", file=sys.stderr)
    if errors.error_count() == 0:
        print("Validation PASSED", file=sys.stderr)
    else:
        print(
            f"Validation found {errors.error_count()} issue(s)",
            file=sys.stderr,
        )
    sys.exit(0 if errors.error_count() == 0 else 1)


if __name__ == "__main__":
    main()
