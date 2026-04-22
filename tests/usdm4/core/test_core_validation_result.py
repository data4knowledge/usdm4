"""Direct tests for CoreRuleFinding and CoreValidationResult.

These are pure data classes — no IO, no engine calls — so the tests
exercise every branch with constructed dicts.
"""

from src.usdm4.core.core_validation_result import (
    CoreRuleFinding,
    CoreValidationResult,
)


# ---------------------------------------------------------------------------
# CoreRuleFinding._sanitise_value — covers each type branch
# ---------------------------------------------------------------------------


def test_sanitise_value_passthrough_primitives():
    assert CoreRuleFinding._sanitise_value(None) is None
    assert CoreRuleFinding._sanitise_value(True) is True
    assert CoreRuleFinding._sanitise_value(1) == 1
    assert CoreRuleFinding._sanitise_value(1.5) == 1.5
    assert CoreRuleFinding._sanitise_value("x") == "x"


def test_sanitise_value_recurses_into_dict():
    result = CoreRuleFinding._sanitise_value({"a": 1, 2: [1, 2]})
    # Non-str keys coerced
    assert result == {"a": 1, "2": [1, 2]}


def test_sanitise_value_recurses_into_list_and_tuple():
    assert CoreRuleFinding._sanitise_value([1, "two", 3.0]) == [1, "two", 3.0]
    assert CoreRuleFinding._sanitise_value((1, 2)) == [1, 2]


def test_sanitise_value_falls_back_to_str_for_non_iterable():
    class NotIterable:
        def __str__(self):
            return "custom-obj"

        def __iter__(self):  # pragma: no cover - not called
            raise TypeError

    # Passing a non-iterable object -> str() fallback
    class WeirdObj:
        def __str__(self):
            return "weird"

    # Use a type that raises TypeError when iterated — int does this.
    assert CoreRuleFinding._sanitise_value(123) == 123
    # Custom object instance that isn't primitive or dict and raises TypeError
    # on iteration should fall back to str().
    obj = object()
    sanitised = CoreRuleFinding._sanitise_value(obj)
    assert isinstance(sanitised, str)


# ---------------------------------------------------------------------------
# CoreRuleFinding._format_error — each branch
# ---------------------------------------------------------------------------


def test_format_error_non_dict_wraps_in_detail():
    assert CoreRuleFinding._format_error("bad") == {"detail": "bad"}


def test_format_error_identity_fields():
    err = {
        "instance_id": "i1",
        "entity": "Study",
        "path": "$.study",
    }
    out = CoreRuleFinding._format_error(err)
    assert out == {"instance_id": "i1", "entity": "Study", "path": "$.study"}


def test_format_error_value_dict_extracts_name_section():
    err = {
        "instance_id": "i1",
        "value": {
            "name": "Section 1",
            "sectionNumber": "1",
            "sectionTitle": "Intro",
            "custom": "keep me",
            "instanceType": "Section",
            "id": "drop",
            "something.id": "drop",
            "something.name": "drop",
            "something.version": "drop",
        },
    }
    out = CoreRuleFinding._format_error(err)
    assert out["name"] == "Section 1"
    assert out["sectionNumber"] == "1"
    assert out["sectionTitle"] == "Intro"
    assert out["details"] == {"custom": "keep me"}


def test_format_error_value_dict_without_extras():
    err = {"value": {"name": "n"}}
    out = CoreRuleFinding._format_error(err)
    assert "details" not in out
    assert out["name"] == "n"


def test_format_error_scalar_value():
    err = {"value": "scalar"}
    out = CoreRuleFinding._format_error(err)
    assert out == {"value": "scalar"}


def test_format_error_error_and_message_fields():
    err = {"error": "bad", "message": "oops"}
    out = CoreRuleFinding._format_error(err)
    assert out == {"error": "bad", "message": "oops"}


def test_format_error_empty_dict_falls_back_to_raw():
    out = CoreRuleFinding._format_error({})
    assert out == {"raw": {}}


# ---------------------------------------------------------------------------
# CoreRuleFinding basics
# ---------------------------------------------------------------------------


def test_core_rule_finding_error_count():
    f = CoreRuleFinding(
        rule_id="R1",
        description="d",
        message="m",
        errors=[{"a": 1}, {"b": 2}],
    )
    assert f.error_count == 2


# ---------------------------------------------------------------------------
# CoreValidationResult — properties
# ---------------------------------------------------------------------------


def _make_finding(rule_id="R1", n=1):
    return CoreRuleFinding(
        rule_id=rule_id,
        description="desc",
        message="msg",
        errors=[{"instance_id": f"i{i}", "entity": "X"} for i in range(n)],
    )


def test_is_valid_true_when_no_findings():
    r = CoreValidationResult()
    assert r.is_valid is True
    assert r.finding_count == 0
    assert r.execution_error_count == 0


def test_is_valid_false_when_findings_present():
    r = CoreValidationResult(findings=[_make_finding(n=2)])
    assert r.is_valid is False
    assert r.finding_count == 2


def test_execution_error_count():
    r = CoreValidationResult(execution_errors=[{"x": 1}, {"x": 2}])
    assert r.execution_error_count == 2


# ---------------------------------------------------------------------------
# CoreValidationResult.format_text — every branch
# ---------------------------------------------------------------------------


def test_format_text_passed_no_exec_errors():
    r = CoreValidationResult(file_path="f.json", version="4-0", rules_executed=1)
    text = r.format_text()
    assert "Validation PASSED - No issues found." in text
    assert "f.json" in text


def test_format_text_passed_with_exec_errors():
    r = CoreValidationResult(
        file_path="f.json", execution_errors=[{"x": 1}], rules_executed=1
    )
    text = r.format_text()
    assert "Validation PASSED - No data issues found." in text
    assert "1 rule execution errors" in text


def test_format_text_failed_with_details_and_path():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="d",
        message="m",
        errors=[
            {
                "instance_id": "i1",
                "entity": "Study",
                "path": "$.study",
                "value": {"name": "N", "sectionNumber": "1"},
            }
        ],
    )
    r = CoreValidationResult(findings=[finding], rules_executed=1)
    text = r.format_text()
    assert "Validation" in text
    assert "R1" in text
    assert "Study (i1)" in text
    assert "$.study" in text


def test_format_text_failed_without_path():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="",
        message="",
        errors=[{"value": {"custom": "xxx"}}],
    )
    r = CoreValidationResult(findings=[finding])
    text = r.format_text()
    # details are present; entity/id missing so line falls through to 'extras'
    assert "custom=xxx" in text


def test_format_text_truncates_errors_beyond_ten():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="",
        message="",
        errors=[{"instance_id": f"i{i}", "entity": "X"} for i in range(15)],
    )
    r = CoreValidationResult(findings=[finding])
    text = r.format_text()
    assert "and 5 more" in text


def test_format_text_lists_ct_packages_loaded():
    r = CoreValidationResult(
        file_path="f",
        ct_packages_available=5,
        ct_packages_loaded=["sdtmct", "adamct"],
    )
    text = r.format_text()
    assert "sdtmct, adamct" in text


def test_format_text_handles_empty_ct_packages():
    r = CoreValidationResult(ct_packages_loaded=[])
    assert "None" in r.format_text()


def test_format_text_failed_with_exec_errors():
    finding = _make_finding(n=1)
    r = CoreValidationResult(findings=[finding], execution_errors=[{"x": 1}])
    text = r.format_text()
    assert "Plus 1 rule execution errors" in text


def test_format_text_failed_without_parts_shows_raw_error():
    """Error without entity, instance_id, path, or details falls through to 'raw'."""
    finding = CoreRuleFinding(
        rule_id="R1", description="", message="", errors=[{"error": "boom"}]
    )
    r = CoreValidationResult(findings=[finding])
    text = r.format_text()
    # "error" field appears in the formatted error fallback
    assert "R1" in text
    assert "boom" in text


# ---------------------------------------------------------------------------
# CoreValidationResult.to_dict
# ---------------------------------------------------------------------------


def test_to_dict_shape():
    finding = _make_finding(n=2)
    r = CoreValidationResult(
        findings=[finding],
        execution_errors=[{"x": 1}],
        rules_executed=3,
        rules_skipped=1,
        ct_packages_available=2,
        ct_packages_loaded=["sdtmct"],
        file_path="path.json",
        version="4-0",
    )
    d = r.to_dict()
    assert d["file"] == "path.json"
    assert d["version"] == "4-0"
    assert d["is_valid"] is False
    assert d["rules_executed"] == 3
    assert d["rules_skipped"] == 1
    assert d["finding_count"] == 2
    assert d["execution_error_count"] == 1
    assert d["ct_packages_available"] == 2
    assert d["ct_packages_loaded"] == ["sdtmct"]
    assert len(d["findings"]) == 1
    assert d["findings"][0]["rule_id"] == "R1"


# ---------------------------------------------------------------------------
# CoreValidationResult.to_errors
# ---------------------------------------------------------------------------


def test_to_errors_with_entity_and_path():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="desc",
        message="msg",
        errors=[
            {
                "instance_id": "i1",
                "entity": "Study",
                "path": "$.study.name",
            }
        ],
    )
    r = CoreValidationResult(findings=[finding])
    errs = r.to_errors()
    messages = [e["message"] for e in errs.to_dict()]
    assert any("Study (i1)" in m and "$.study.name" in m for m in messages)


def test_to_errors_with_instance_only():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="desc",
        message="",
        errors=[{"instance_id": "i1"}],  # no entity, no path
    )
    r = CoreValidationResult(findings=[finding])
    errs = r.to_errors()
    messages = [e["message"] for e in errs.to_dict()]
    assert any("i1" in m for m in messages)


def test_to_errors_with_detail_field():
    """Test that non-dict errors pass through the 'detail' path."""
    finding = CoreRuleFinding(
        rule_id="R1",
        description="desc",
        message="msg",
        errors=["scalar error"],
    )
    r = CoreValidationResult(findings=[finding])
    errs = r.to_errors()
    messages = [e["message"] for e in errs.to_dict()]
    # description + ": scalar error" (from detail key) — no location trailer
    assert any("scalar error" in m for m in messages)


def test_to_errors_without_location_or_detail():
    finding = CoreRuleFinding(
        rule_id="R1",
        description="",
        message="simple",
        errors=[{"error": "boom"}],
    )
    r = CoreValidationResult(findings=[finding])
    errs = r.to_errors()
    messages = [e["message"] for e in errs.to_dict()]
    # Bare description comes through; no brackets
    assert any("simple" in m for m in messages)
