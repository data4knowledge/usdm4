import os
from pathlib import Path
from usdm4.ct.cdisc.library import Library
from dotenv import load_dotenv

if __name__ == "__main__":
    root = os.path.join(Path(__file__).parent.resolve(), "src/usdm4/ct/cdisc")
    load_dotenv(".development_env")
    library = Library(root)
    library.load()