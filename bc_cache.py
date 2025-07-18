import os
from pathlib import Path
from usdm3.ct.cdisc.library import Library as CtLibrary
from usdm3.bc.cdisc.library import Library as BcLibrary

from dotenv import load_dotenv

if __name__ == "__main__":
    root = os.path.join(Path(__file__).parent.resolve(), "src/usdm3")
    load_dotenv(".development_env")
    ct = CtLibrary(root)
    ct.load()
    bc = BcLibrary(root, ct)
    bc._cache.delete()
    bc.load()
    # print(f"BC Library Valid: {bc._api.valid}")
    # print(f"BC Library Errors: {bc._api.errors.dump()}")
