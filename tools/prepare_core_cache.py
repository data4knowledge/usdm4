"""
Populate the CDISC CORE validation cache on this machine.

Runs USDM4.prepare_core(), which downloads rule definitions, CT packages,
JSONata files and XSD schemas from CDISC Library into the local cache dir.
Once populated, the cached rule YAMLs can be inspected on disk.

Requirements:
- CDISC Library API key set via the CDISC_LIBRARY_API_KEY environment
  variable, or passed with --api-key.

Usage:
    export CDISC_LIBRARY_API_KEY=...
    python tools/prepare_core_cache.py
    python tools/prepare_core_cache.py --version 4-0
    python tools/prepare_core_cache.py --cache-dir /some/path
"""

from __future__ import annotations

import argparse
import os
import sys

from usdm4 import USDM4


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default="4-0", help="USDM version (default: 4-0)")
    ap.add_argument("--cache-dir", default=None,
                    help="Override cache directory (default: platform user cache)")
    ap.add_argument("--api-key", default=None,
                    help="CDISC Library API key (default: $CDISC_LIBRARY_API_KEY)")
    args = ap.parse_args()

    api_key = args.api_key or os.environ.get("CDISC_LIBRARY_API_KEY")
    if not api_key:
        print("ERROR: no API key. Set CDISC_LIBRARY_API_KEY or pass --api-key.",
              file=sys.stderr)
        return 1

    usdm = USDM4(cache_dir=args.cache_dir)
    print(f"Preparing CORE cache (version={args.version}) ...", file=sys.stderr)
    status = usdm.prepare_core(version=args.version, api_key=api_key)
    print(f"Cache dir:   {usdm._core_validator.cache_manager.cache_dir if usdm._core_validator else '(none)'}",
          file=sys.stderr)
    print(f"Status:      {status}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
