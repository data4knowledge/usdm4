import pytest
from unittest.mock import Mock
from usdm4.rules.library.rule_ddf00106 import RuleDDF00106
from usdm3.rules.library.rule_template import RuleTemplate


@pytest.fixture
def rule():
    return RuleDDF00106()


def test_initialization(rule):
    """Test rule initialization"""
    assert rule._rule == "DDF00106"
    assert rule._level == RuleTemplate.ERROR
    assert (
        rule._rule_text
        == "A scheduled activity instance must only reference an encounter that is defined within the same study design as the scheduled activity instance."
    )
    assert rule._errors.count() == 0


def test_validate_encounter_in_different_study_design(rule):
    data_store = Mock()
    data_store.instances_by_klass.return_value = [
        {
            "id": "sai1",
            "encounterId": "enc1",
            "instanceType": "ScheduledActivityInstance",
        },
    ]
    data_store.instance_by_id.return_value = {
        "id": "enc1",
    }
    data_store.parent_by_klass.side_effect = [
        {"id": "sai1"},
        {"id": "sai2"},
    ]
    data_store.path_by_id.side_effect = ["path/path1"]

    config = {"data": data_store}
    assert rule.validate(config) is False
    assert rule._errors.count() == 1
    assert rule._errors._items[0].to_dict() == {
        "level": "Error",
        "location": {
            "attribute": "encounterId",
            "klass": "ScheduledActivityInstance",
            "path": "path/path1",
            "rule": "DDF00106",
            "rule_text": "A scheduled activity instance must only reference an encounter that is defined within the same study design as the scheduled activity instance.",
        },
        "message": "Encounter defined in a different study design",
    }


def test_validate_encounter_in_same_study_design(rule):
    data_store = Mock()
    data_store.instances_by_klass.return_value = [
        {
            "id": "sai1",
            "encounterId": "enc1",
            "instanceType": "ScheduledActivityInstance",
        },
    ]
    data_store.instance_by_id.return_value = {
        "id": "enc1",
    }
    data_store.parent_by_klass.side_effect = [
        {"id": "sai1"},
        {"id": "sai1"},
    ]
    data_store.path_by_id.side_effect = ["path/path1"]

    config = {"data": data_store}
    assert rule.validate(config) is True
    assert rule._errors.count() == 0

def test_validate_encounter_both_missing(rule):
    data_store = Mock()
    data_store.instances_by_klass.side_effect = [
        [
            {
                "id": "sai1",
                "encounterId": "ep1",
                "instanceType": "ScheduledActivityInstance",
            },
            {
                "id": "sai2",
                "encounterId": "ep2",
                "instanceType": "ScheduledActivityInstance",
            }
        ],
    ]
    data_store.instance_by_id.side_effect = [
        {
            "id": " ep1",
            "instanceType": "XXX"
        },
        {
            "id": "ep2",
            "instanceType": "YYY"
        },
    ]
    data_store.parent_by_klass.side_effect = [None, None, None, None]
    data_store.path_by_id.side_effect = ["path/path1", "path/path2"]

    config = {"data": data_store}
    assert rule.validate(config) is False
    assert rule._errors.count() == 2
    assert rule._errors._items[0].to_dict() == {
        "level": "Error",
        "location": {
            "attribute": "encounterId",
            "klass": "ScheduledActivityInstance",
            "path": "path/path1",
            "rule": "DDF00106",
            "rule_text": "A scheduled activity instance must only reference an encounter that is defined within the same study design as the scheduled activity instance.",
        },
        "message": "ScheduledActivityInstance and XXX missing parents",
    }
    assert rule._errors._items[1].to_dict() == {
        "level": "Error",
        "location": {
            "attribute": "encounterId",
            "klass": "ScheduledActivityInstance",
            "path": "path/path2",
            "rule": "DDF00106",
            "rule_text": "A scheduled activity instance must only reference an encounter that is defined within the same study design as the scheduled activity instance.",
        },
        "message": "ScheduledActivityInstance and YYY missing parents",
    }


