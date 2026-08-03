"""Force-refresh the CDISC BC (Biomedical Concept) library cache.

Loads the CT library first (BC depends on CT), then clears the on-disk BC
cache and reloads from the CDISC Library API. Use this when the CDISC
publishes a new BC package and you want the local cache to pick it up.

Requires a CDISC Library API key. The script reads `.development_env` from
the current working directory; run from the repo root:

    python tools/bc_cache.py
"""

import os
from pathlib import Path
from usdm4.ct.cdisc.library import Library as CtLibrary
from usdm4.bc.cdisc.library import Library as BcLibrary

from dotenv import load_dotenv

if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent.resolve()
    root = os.path.join(repo_root, "src/usdm4")
    load_dotenv(".development_env")
    ct = CtLibrary(root)
    ct.load()
    bc = BcLibrary(root, ct)
    bc._cache.delete()
    bc.load()
