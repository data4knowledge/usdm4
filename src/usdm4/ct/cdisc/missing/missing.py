"""Loader for missing-from-CDISC controlled-terminology data.

Two sibling YAML files in this directory:

  - ``missing_ct.yaml``   — extensions to existing extensible CDISC
    codelists, using the ``extends:`` shape.
  - ``m11_codelists.yaml`` — whole M11 codelists not served by the CDISC
    Library API (sourced from the m11_specification snapshot), using the
    ``codelist:`` shape.

Each file is optional; absent files are silently skipped. ``code_lists``
yields ``(entry, source_filename)`` tuples so the consumer
(``Library._add_missing_ct``) can enforce the per-file shape invariant
and emit useful errors when an entry is in the wrong file.
"""

import os
from typing import Iterator

import yaml


class Missing:
    """Reads the two missing-CT YAML files and yields entries with their source.

    The two-file split keeps per-source provenance obvious in the file
    tree: ``missing_ct.yaml`` only carries extensions, ``m11_codelists.yaml``
    only carries whole codelists. See ``Library._add_missing_ct`` for the
    invariant enforcement.
    """

    _FILES: tuple[str, ...] = ("missing_ct.yaml", "m11_codelists.yaml")

    def __init__(self, file_path: str):
        self._entries: list[tuple[dict, str]] = []
        for filename in self._FILES:
            full = os.path.join(file_path, filename)
            if not os.path.exists(full):
                continue
            with open(full) as f:
                data = yaml.load(f, Loader=yaml.FullLoader) or []
            for entry in data:
                self._entries.append((entry, filename))

    def code_lists(self) -> Iterator[tuple[dict, str]]:
        """Yield ``(entry, source_filename)`` for each entry across both files."""
        for entry, source_file in self._entries:
            yield entry, source_file
