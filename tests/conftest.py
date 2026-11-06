"""Parse the CT and BC library caches once per test run.

Each new ``Builder`` loads the CDISC CT and BC libraries the first time it needs
them, which means parsing several MB of YAML, many seconds each time. A test
that builds its own ``Assembler`` or ``Builder`` pays that again. This fixture
keeps the first parse of each packaged cache file and gives every later read its
own copy (the CT library adds to what it reads), so such a test costs little.

Only the packaged cache files are held. Any other ``FileCache`` file reads from
disk as usual, so the ``file_cache`` tests are not affected.
"""

import importlib
import os
import pathlib
import pickle

import pytest

PACKAGE_ROOT = str(pathlib.Path(__file__).resolve().parents[1] / "src" / "usdm4")
CACHE_FILES = (
    "library_cache.yaml",
    "library_cache_all.yaml",
    "library_cache_usdm.yaml",
)
# Tests import the package by both paths, and the two are distinct classes.
MODULES = ("usdm4.file_cache.file_cache", "src.usdm4.file_cache.file_cache")


def parse_once(read, parsed: dict):
    def wrapper(self) -> dict:
        path = os.path.realpath(self._full_filepath())
        if self.filename not in CACHE_FILES or not path.startswith(PACKAGE_ROOT):
            return read(self)
        if path not in parsed:
            parsed[path] = pickle.dumps(read(self))
        return pickle.loads(parsed[path])

    return wrapper


@pytest.fixture(scope="session", autouse=True)
def library_caches_parsed_once():
    parsed = {}
    patch = pytest.MonkeyPatch()
    for name in MODULES:
        file_cache = importlib.import_module(name).FileCache
        patch.setattr(file_cache, "read", parse_once(file_cache.read, parsed))
    yield
    patch.undo()
