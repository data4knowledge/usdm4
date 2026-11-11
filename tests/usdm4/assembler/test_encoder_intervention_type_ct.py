"""Every intervention type the encoder maps resolves in the packaged CDISC
CT (codelist C99078) with the decode given (GitHub 103)."""

import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from usdm4.assembler.encoder import Encoder
from usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(_root_path(), Errors())


@pytest.mark.parametrize("keys, entry", Encoder.INTERVENTION_TYPE_MAP)
def test_mapped_type_resolves_in_ct(builder, keys, entry):
    code = Encoder(builder, Errors()).intervention_type(keys[0])
    assert code is not None
    assert code.code == entry["code"]
    assert code.decode == entry["decode"]
