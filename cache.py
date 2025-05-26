import os
from pathlib import Path
from usdm3.ct.cdisc.library import Library
from dotenv import load_dotenv

if __name__ == "__main__":
    root = os.path.join(Path(__file__).parent.resolve(), "src/usdm4")
    load_dotenv(".development_env")
    library = Library(root)
    library.load()
