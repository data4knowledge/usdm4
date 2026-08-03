"""Tests for RuleDDF00082 — schema validation of data types."""

from unittest.mock import MagicMock, patch

from usdm4.rules.library.rule_ddf00082 import RuleDDF00082
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.schema.schema_validation import SchemaValidation, ValidationError


class TestRuleDDF00082:
    def test_metadata(self):
        rule = RuleDDF00082()
        assert rule._rule == "DDF00082"
        assert rule._level == RuleTemplate.ERROR

    def test_schema_path_ends_with_file(self):
        rule = RuleDDF00082()
        path = rule._schema_path()
        assert path.endswith("usdm_v4-0-0.json")
        assert "schema" in path

    def test_validate_passes(self):
        rule = RuleDDF00082()
        data = MagicMock()
        data.filename = "/path/to/study.json"
        # Patch the class methods directly so the patch affects all
        # references to SchemaValidation regardless of import path.
        with (
            patch.object(SchemaValidation, "__init__", return_value=None),
            patch.object(SchemaValidation, "validate_file", return_value=None),
        ):
            assert rule.validate({"data": data}) is True

    def test_validate_fails_on_validation_error(self):
        rule = RuleDDF00082()
        data = MagicMock()
        data.filename = "/path/to/study.json"
        err = ValidationError("bad type", path=["study"], instance={"x": 1})
        with (
            patch.object(SchemaValidation, "__init__", return_value=None),
            patch.object(SchemaValidation, "validate_file", side_effect=err),
        ):
            assert rule.validate({"data": data}) is False
            assert rule.errors().count() == 1
