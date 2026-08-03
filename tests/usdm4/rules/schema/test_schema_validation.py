"""Tests for SchemaValidation helper.

Covers the two error branches in get_component_schema (no components/
schemas section, unknown component) plus the happy paths for
validate_against_component and validate_file.
"""

import json

import pytest

from usdm4.rules.schema.schema_validation import SchemaValidation


# ---------------------------------------------------------------------------
# get_component_schema — error branches
# ---------------------------------------------------------------------------


def _write_schema(tmp_path, payload):
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(payload))
    return schema_file


def test_missing_components_raises(tmp_path):
    """A schema without a 'components' key fails fast with ValueError."""
    f = _write_schema(tmp_path, {"openapi": "3.1"})
    sv = SchemaValidation(str(f))
    with pytest.raises(ValueError, match="components/schemas"):
        sv.get_component_schema("Anything")


def test_missing_schemas_raises(tmp_path):
    """'components' present but no 'schemas' sub-key → same ValueError."""
    f = _write_schema(tmp_path, {"components": {}})
    sv = SchemaValidation(str(f))
    with pytest.raises(ValueError, match="components/schemas"):
        sv.get_component_schema("Anything")


def test_unknown_component_raises(tmp_path):
    """Valid components/schemas but no matching component name."""
    f = _write_schema(tmp_path, {"components": {"schemas": {"Other": {}}}})
    sv = SchemaValidation(str(f))
    with pytest.raises(ValueError, match="Schema component 'Missing' not found"):
        sv.get_component_schema("Missing")


def test_existing_component_returns_schema(tmp_path):
    """Happy path — returns the matching sub-schema dict."""
    component = {"type": "object", "properties": {"name": {"type": "string"}}}
    f = _write_schema(tmp_path, {"components": {"schemas": {"Thing": component}}})
    sv = SchemaValidation(str(f))
    assert sv.get_component_schema("Thing") == component


# ---------------------------------------------------------------------------
# validate_against_component + validate_file
# ---------------------------------------------------------------------------


def test_validate_against_component_accepts_valid_data(tmp_path):
    schema = {
        "components": {
            "schemas": {
                "Simple": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            }
        }
    }
    f = _write_schema(tmp_path, schema)
    sv = SchemaValidation(str(f))
    assert sv.validate_against_component({"name": "ok"}, "Simple") is True


def test_validate_against_component_rejects_invalid_data(tmp_path):
    """Data that fails validation surfaces jsonschema.ValidationError."""
    from jsonschema import ValidationError

    schema = {
        "components": {
            "schemas": {
                "Simple": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            }
        }
    }
    f = _write_schema(tmp_path, schema)
    sv = SchemaValidation(str(f))
    with pytest.raises(ValidationError):
        sv.validate_against_component({}, "Simple")


def test_validate_file_round_trip(tmp_path):
    """validate_file loads the JSON and validates it."""
    schema = {
        "components": {
            "schemas": {
                "Simple": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            }
        }
    }
    schema_file = _write_schema(tmp_path, schema)
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps({"name": "ok"}))
    sv = SchemaValidation(str(schema_file))
    assert sv.validate_file(str(data_file), "Simple") is True
