"""Tests for SchemaErrorLocation."""

from src.usdm4.rules.schema.schema_location import SchemaErrorLocation


def test_to_dict():
    loc = SchemaErrorLocation("a.b.c", {"id": "I1"})
    assert loc.to_dict() == {"path": "a.b.c", "instance": {"id": "I1"}}


def test_str_representation():
    """Covers __str__ — line 13."""
    loc = SchemaErrorLocation("a.b.c", "INSTANCE")
    assert str(loc) == "[a.b.c, INSTANCE]"
