"""tools/references_map.py, the reference map generator (GitHub 106)."""

import importlib.util
import sys

import yaml

from tools import references_map
from usdm4.fixer import references
from usdm4.fixer.walk import concrete, reference_attributes, super_classes

STRUCTURE = {
    "ScheduledInstance": {
        "Sub Classes": [{"$ref": "#/ScheduledDecisionInstance"}],
        "Attributes": {
            "epochId": {"Type": [{"$ref": "#/StudyEpoch"}], "Relationship Type": "Ref"}
        },
    },
    "ScheduleTimeline": {
        "Attributes": {
            "name": {"Type": [{"$ref": "#/string"}], "Relationship Type": "Value"},
            "entryId": {
                "Type": [{"$ref": "#/ScheduledInstance"}],
                "Relationship Type": "Ref",
            },
        }
    },
    "Code": {},
}


def test_build_and_render(tmp_path):
    refs, subs = references_map.build(STRUCTURE)
    assert refs == {
        "ScheduledInstance": {"epochId": ["StudyEpoch"]},
        "ScheduleTimeline": {"entryId": ["ScheduledInstance"]},
    }
    assert subs == {"ScheduledInstance": ["ScheduledDecisionInstance"]}
    text = references_map.render(refs, subs, "v9")
    module_path = tmp_path / "generated.py"
    module_path.write_text(text)
    spec = importlib.util.spec_from_file_location("generated", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REFERENCES == refs and module.SOURCE == "v9"


def test_main(tmp_path, monkeypatch):
    source = tmp_path / "ds.yml"
    source.write_text(yaml.safe_dump(STRUCTURE))
    output = tmp_path / "references.py"
    monkeypatch.setattr(references_map, "OUTPUT", output)
    monkeypatch.setattr(sys, "argv", ["x", "--source", str(source)])
    references_map.main()
    assert "SOURCE = 'v4.0.0'" in output.read_text()


def test_packaged_map():
    assert references.SOURCE == "v4.0.0"
    assert sum(len(v) for v in references.REFERENCES.values()) == 83
    assert concrete(["ScheduledInstance"]) == {
        "ScheduledActivityInstance",
        "ScheduledDecisionInstance",
    }
    attributes = reference_attributes("ScheduledDecisionInstance")
    assert attributes["epochId"] == {"StudyEpoch"}
    assert super_classes("InterventionalStudyDesign") == [
        "InterventionalStudyDesign",
        "StudyDesign",
    ]
