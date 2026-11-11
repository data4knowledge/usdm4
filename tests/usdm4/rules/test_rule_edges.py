"""Rule branches the per-rule tests do not reach: non-string values counted
as set, non-dict entries skipped, an address with no attributes, a summary
of more than three XHTML errors, a loaded codelist with no terms, and a
missing XHTML schema."""

from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import pytest
from simple_error_log.errors import Errors

from usdm4.rules.library import (
    rule_ddf00008,
    rule_ddf00097,
    rule_ddf00098,
    rule_ddf00132,
    rule_ddf00133,
    rule_ddf00194,
)
from usdm4.rules.library.rule_ddf00045 import RuleDDF00045
from usdm4.rules.library.rule_ddf00181 import RuleDDF00181
from usdm4.rules.library.rule_ddf00185 import RuleDDF00185
from usdm4.rules.library.rule_ddf00247 import RuleDDF00247
from usdm4.rules.library.rule_ddf00256 import RuleDDF00256
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.xhtml_validation import XhtmlValidator


def _data(instances):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda klass: instances.get(klass, [])
    data.path_by_id.return_value = "$.path"
    return data


@pytest.mark.parametrize(
    "helper",
    [
        rule_ddf00008._is_set,
        rule_ddf00097._is_specified,
        rule_ddf00098._is_specified,
        rule_ddf00132._is_specified,
        rule_ddf00133._is_specified,
    ],
)
def test_non_string_value_is_set(helper):
    assert helper(5) is True


def test_address_non_string_attribute_is_specified():
    assert rule_ddf00194._any_attribute_specified({"lines": 0}) is True


def test_ddf00045_address_without_attributes_fails():
    rule = RuleDDF00045()
    data = _data({"Address": [{"id": "A1", "text": "", "city": None}]})
    assert rule.validate({"data": data}) is False
    assert rule.errors().count() == 1


def test_ddf00045_address_with_attribute_passes():
    rule = RuleDDF00045()
    data = _data({"Address": [{"id": "A1", "city": "Bonn"}]})
    assert rule.validate({"data": data}) is True


def test_ddf00181_non_dict_date_skipped():
    rule = RuleDDF00181()
    data = _data({"StudyDefinitionDocumentVersion": [{"dateValues": ["not a dict"]}]})
    assert rule.validate({"data": data}) is True


def test_ddf00185_non_dict_intervention_and_administration_skipped():
    rule = RuleDDF00185()
    data = _data(
        {
            "StudyVersion": [
                {
                    "id": "SV1",
                    "studyInterventions": ["not a dict", {"administrations": ["x"]}],
                }
            ]
        }
    )
    assert rule.validate({"data": data}) is True


def test_ddf00247_more_than_three_errors_summarised():
    rule = RuleDDF00247()
    validator = MagicMock()
    validator.validate.return_value = [NS(line=n, message=f"bad {n}") for n in range(5)]
    data = _data({"Objective": [{"id": "O1", "text": "<p>x</p>"}]})
    # Patch the globals the rule's own validate() reads: the rule engine
    # reloads library modules under the same name, so a patch by module
    # path can miss the class imported here.
    with patch.dict(
        RuleDDF00247.validate.__globals__, {"get_validator": lambda: validator}
    ):
        assert rule.validate({"data": data}) is False
    messages = [e["message"] for e in rule.errors().to_dict(Errors.DEBUG)]
    assert "; ... and 2 more" in messages[0]


def test_ddf00256_non_dict_secondary_skipped():
    rule = RuleDDF00256()
    data = _data(
        {
            "StudyAmendment": [
                {
                    "primaryReason": {"code": {"code": "C1"}},
                    "secondaryReasons": ["not a dict"],
                }
            ]
        }
    )
    assert rule.validate({"data": data}) is True


def test_ct_check_codelist_without_terms_raises():
    rule = RuleTemplate("R1", RuleTemplate.ERROR, "text")
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {"terms": []}
    with pytest.raises(RuleTemplate.CTException, match="has no terms"):
        rule._ct_check({"data": MagicMock(), "ct": ct}, "Study", "status")


def test_xhtml_schema_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="XHTML schema not found"):
        XhtmlValidator(schema_path=tmp_path / "missing.xsd")
