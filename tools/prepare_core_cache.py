"""
Populate (or force-refresh) the CDISC CORE validation cache on this machine.

Runs USDM4.prepare_core(), which downloads rule definitions, CT packages,
JSONata files and XSD schemas from CDISC Library into the local cache dir.
Once populated, the cached rule YAMLs can be inspected on disk.

By default this only downloads what is *missing* — if the cache is already
complete, prepare_core() returns immediately and nothing is re-downloaded.
Pass --force to delete the existing cache first and pull everything fresh
(useful after a cdisc-rules-engine upgrade, or to adopt newly published
rules / CT). Note: a forced refresh pulls whatever the CDISC Library
currently publishes, so the set of rules can change.

Requirements:
- CDISC Library API key. Resolved in this order:
    1. --api-key argument
    2. CDISC_LIBRARY_API_KEY environment variable
    3. CDISC_LIBRARY_API_KEY in a .development_env file (repo root / CWD)

Usage:
    python tools/prepare_core_cache.py                 # fill in what's missing
    python tools/prepare_core_cache.py --force         # wipe + re-download
    python tools/prepare_core_cache.py --version 4-0
    python tools/prepare_core_cache.py --cache-dir /some/path --force
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from usdm4 import USDM4
from usdm4.core.core_cache_manager import CoreCacheManager


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default="4-0", help="USDM version (default: 4-0)")
    ap.add_argument(
        "--cache-dir",
        default=None,
        help="Override cache directory (default: platform user cache)",
    )
    ap.add_argument(
        "--api-key",
        default=None,
        help="CDISC Library API key (default: $CDISC_LIBRARY_API_KEY)",
    )
    ap.add_argument(
        "--force",
        "--refresh",
        action="store_true",
        help="Delete the existing cache first, then re-download everything",
    )
    args = ap.parse_args()

    # Pick up CDISC_LIBRARY_API_KEY from .development_env if present, matching
    # the other tools/ scripts. Does not override an already-exported var.
    load_dotenv(".development_env")

    api_key = args.api_key or os.environ.get("CDISC_LIBRARY_API_KEY")
    if not api_key:
        print(
            "ERROR: no API key. Set CDISC_LIBRARY_API_KEY, add it to "
            ".development_env, or pass --api-key.",
            file=sys.stderr,
        )
        return 1

    cache_manager = CoreCacheManager(args.cache_dir)
    print(f"Cache dir:   {cache_manager.cache_dir}", file=sys.stderr)

    before = cache_manager.is_populated(version=args.version)
    print(f"Before:      ready={before.ready} {before.details}", file=sys.stderr)

    if args.force:
        print("Clearing cache (--force) ...", file=sys.stderr)
        cache_manager.clear()

    usdm = USDM4(cache_dir=args.cache_dir)
    print(f"Preparing CORE cache (version={args.version}) ...", file=sys.stderr)
    status = usdm.prepare_core(version=args.version, api_key=api_key)
    print(f"After:       ready={status.ready} {status.details}", file=sys.stderr)

    if not status.ready:
        print("WARNING: cache is not fully populated.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
