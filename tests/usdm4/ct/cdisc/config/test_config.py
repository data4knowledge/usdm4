"""Tests for the CDISC CT Config loader."""

import os

import pytest

from src.usdm4.ct.cdisc.config.config import Config


CONFIG_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "..",
    "src",
    "usdm4",
    "ct",
    "cdisc",
    "config",
)


def test_required_code_lists_returns_list():
    """Covers Config.required_code_lists — line 15."""
    cfg = Config(CONFIG_DIR)
    code_lists = cfg.required_code_lists()
    assert isinstance(code_lists, list)
    assert len(code_lists) > 0


def test_required_packages_returns_list():
    cfg = Config(CONFIG_DIR)
    pkgs = cfg.required_packages()
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0


def test_klass_and_attribute_lookup_succeeds():
    cfg = Config(CONFIG_DIR)
    # The YAML has class→attribute→codelist mappings; pick one that actually has
    # an attribute (some entries like `Study: {}` are present but empty).
    mapping = cfg._by_klass_attribute
    klass, attrs = next((k, v) for k, v in mapping.items() if v)
    attr = next(iter(attrs))
    assert cfg.klass_and_attribute(klass, attr) == attrs[attr]


def test_klass_and_attribute_missing_raises_valueerror():
    cfg = Config(CONFIG_DIR)
    with pytest.raises(ValueError, match="failed to find codelist"):
        cfg.klass_and_attribute("NoSuchClass", "noSuchAttr")
