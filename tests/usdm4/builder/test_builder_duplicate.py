"""Builder.duplicate: a deep copy with fresh ids throughout, outside the
cross-reference index (used by usdm4_excel)."""

import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from usdm4.api.code import Code
from usdm4.api.governance_date import GovernanceDate
from usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(_root_path(), Errors())


def test_none_gives_none(builder):
    assert builder.duplicate(None) is None


def test_fresh_ids_throughout(builder):
    builder.clear()
    code = builder.cdisc_code("C71476", "Approval Date")
    original = builder.create(
        GovernanceDate,
        {
            "name": "APPROVAL",
            "type": code,
            "dateValue": "2024-01-01",
            "geographicScopes": [],
        },
    )
    copy = builder.duplicate(original)
    assert isinstance(copy, GovernanceDate)
    assert copy.id != original.id
    assert isinstance(copy.type, Code)
    assert copy.type.id != original.type.id
    assert copy.type.code == original.type.code
    assert copy.name == original.name
