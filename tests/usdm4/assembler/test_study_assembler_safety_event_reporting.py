"""M11 9.2 reporting table on the StudyVersion (GitHub 109)."""

import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.api import extensions_d4k as d4k
from src.usdm4.api.extension import ExtensionAttribute, ExtensionClass
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.assembler.study_assembler import StudyAssembler
from src.usdm4.builder.builder import Builder


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


TEXT = {
    "situational_scope": "Related to trial intervention",
    "reporting_period_start": "Informed consent",
    "reporting_period_end": "30 days after last dose",
    "reporting_timing": "Within 24 hours",
    "reporting_method": "EDC\nSafety form",
    "backup_reporting_method": "Email",
}


@pytest.fixture(scope="module")
def shared_builder():
    return Builder(root_path(), Errors())


@pytest.fixture
def assembler(shared_builder):
    shared_builder.clear()
    return StudyAssembler(shared_builder, Errors())


def version(extensions):
    return StudyVersion(
        id="StudyVersion_1",
        versionIdentifier="1",
        rationale="r",
        studyIdentifiers=[],
        titles=[],
        extensionAttributes=[ExtensionAttribute(**e.model_dump()) for e in extensions],
    )


def rows(assembler, *data):
    return version(
        assembler._safety_event_reporting_extensions(list(data))
    ).safety_event_reporting()


def event(assembler, event_type, other=""):
    row = rows(assembler, {"event_type": event_type, "other_event_type": other})[0]
    return row["event_type"].code, row["other_event_type"]


class TestExtensions:
    def test_none_given(self, assembler):
        for value in (None, []):
            assert assembler._safety_event_reporting_extensions(value) == []

    def test_structure(self, assembler):
        result = assembler._safety_event_reporting_extensions(
            [
                {"event_type": "Serious Adverse Event", **TEXT},
                {"event_type": "Adverse Event"},
            ]
        )
        assert [e.url for e in result] == [d4k.SER_EXT_URL, d4k.SER_EXT_URL]
        assert all(e.extensionAttributes == [] for e in result)
        classes = [e.valueExtensionClass for e in result]
        assert [c.url for c in classes] == [d4k.SERC_EXT_URL, d4k.SERC_EXT_URL]
        assert [c.instanceType for c in classes] == ["ExtensionClass"] * 2
        assert [e.url for e in classes[0].extensionAttributes] == [
            d4k.SERT_EXT_URL,
            d4k.SERU_EXT_URL,
            d4k.SERS_EXT_URL,
            d4k.SERE_EXT_URL,
            d4k.SERG_EXT_URL,
            d4k.SERM_EXT_URL,
            d4k.SERB_EXT_URL,
        ]
        assert [e.url for e in classes[1].extensionAttributes] == [d4k.SERT_EXT_URL]

    def test_rows_in_order(self, assembler):
        result = rows(
            assembler,
            {"event_type": "Serious Adverse Event", **TEXT},
            {"event_type": "Adverse Event"},
        )
        assert [r["event_type"].code for r in result] == ["C41335", "C41331"]
        assert {k: result[0][k] for k in TEXT} == TEXT
        assert result[0]["other_event_type"] == ""
        assert {k: result[1][k] for k in TEXT} == dict.fromkeys(TEXT, "")


class TestEventType:
    def test_every_term(self, assembler, shared_builder):
        for term in shared_builder.codelist("C217287")["terms"]:
            text = term["preferredTerm"]
            assert event(assembler, text) == (term["conceptId"], ""), text

    def test_case_and_full_stop(self, assembler):
        assert event(assembler, " pregnancy EVENT. ") == ("C218509", "")

    def test_other_text(self, assembler):
        assert event(assembler, "Medication error.") == ("C17649", "Medication error.")

    def test_other_keeps_given(self, assembler):
        assert event(assembler, "Other", " Overdose ") == ("C17649", "Overdose")
        assert event(assembler, "Other") == ("C17649", "")

    def test_given_dropped_when_not_other(self, assembler):
        assert event(assembler, "Adverse Event", "Overdose") == ("C41331", "")
        assert event(assembler, "Misuse", "Overdose") == ("C17649", "Misuse")
        assert str(assembler._errors.dump(0)).count("'Overdose' stated but") == 2

    def test_blank_dropped(self, assembler):
        assert rows(assembler, {"event_type": " ", "reporting_method": "EDC"}) == []
        assert "has no event type" in str(assembler._errors.dump(0))


class TestFailure:
    def test_exception(self, assembler, monkeypatch):
        def fail(text):
            raise ValueError("no")

        monkeypatch.setattr(assembler._encoder, "safety_event_type", fail)
        assert (
            assembler._safety_event_reporting_extensions([{"event_type": "Other"}])
            == []
        )
        assert "safety event reporting" in str(assembler._errors.dump(0))


class TestAccessor:
    def test_no_extension(self):
        assert version([]).safety_event_reporting() == []

    @staticmethod
    def ext(url, row_class=None):
        return ExtensionAttribute(
            id="e1",
            url=url,
            valueExtensionClass=row_class,
            instanceType="ExtensionAttribute",
        )

    def test_not_a_row(self):
        extensions = [self.ext(d4k.CS_EXT_URL), self.ext(d4k.SER_EXT_URL)]
        assert version(extensions).safety_event_reporting() == []

    def test_row_without_event_type(self):
        row_class = ExtensionClass(
            id="c1", url=d4k.SERC_EXT_URL, instanceType="ExtensionClass"
        )
        result = version([self.ext(d4k.SER_EXT_URL, row_class)])
        rows = result.safety_event_reporting()
        assert len(rows) == 1
        assert rows[0]["event_type"] is None
        assert set(list(rows[0].values())[1:]) == {""}
