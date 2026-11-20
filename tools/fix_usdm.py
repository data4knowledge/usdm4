"""Fix duplicate ids and CT version/decode in a USDM4 JSON file (GitHub 106).

Runs ``USDM4().fix()`` on the input and writes the fixed JSON to the output,
plus an audit log of every change and every issue left for a person (by
default ``<output>.log.json``). The input file is never changed.

    python3 tools/fix_usdm.py input.json output.json [--no-ids] [--no-ct] [--log PATH]
"""

import argparse
import pathlib
import sys

from usdm4 import USDM4


def run(args: argparse.Namespace) -> int:
    source = pathlib.Path(args.input)
    output = pathlib.Path(args.output)
    if not source.is_file():
        print(f"Input file not found: {source}", file=sys.stderr)
        return 1
    if output.resolve() == source.resolve():
        print("Output must not be the input file", file=sys.stderr)
        return 1
    log = pathlib.Path(args.log) if args.log else output.with_suffix(".log.json")
    result = USDM4().fix(str(source), ids=not args.no_ids, ct=not args.no_ct)
    result.save(str(output))
    result.save_log(str(log))
    summary = result.summary()
    print(f"Fixed:  {output}")
    print(f"Log:    {log}")
    print(f"Changes {summary['changes'] or 0}")
    print(f"Issues  {summary['issues'] or 0}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="USDM4 JSON file to fix")
    parser.add_argument("output", help="where to write the fixed JSON")
    parser.add_argument("--no-ids", action="store_true", help="skip the id step")
    parser.add_argument("--no-ct", action="store_true", help="skip the CT step")
    parser.add_argument("--log", help="audit log path (default <output>.log.json)")
    return run(parser.parse_args(argv))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
