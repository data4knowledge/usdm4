"""Force-refresh the CDISC CT (Controlled Terminology) library cache.

Clears the on-disk CT cache, then loads the library from the CDISC Library
API. Use this when the CDISC publishes a new CT package and you want the
local cache to pick it up.

Requires a CDISC Library API key. The script reads `.development_env` from
the current working directory; run from the repo root:

    python tools/ct_cache.py

For a soft load (refresh only what's missing, no delete), use the
`Library.load()` API directly — there's no separate script for that.
"""

import os
from pathlib import Path
from usdm4.ct.cdisc.library import Library
from dotenv import load_dotenv

if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent.resolve()
    root = os.path.join(repo_root, "src/usdm4")
    load_dotenv(".development_env")
    library = Library(root)
    library._cache.delete()
    library.load()
