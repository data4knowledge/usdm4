from src.usdm4.assembler.schema.document_schema import (
    DocumentInput,
    DocumentMetadata,
    Section,
)


class TestDocumentMetadata:

    def test_defaults(self):
        m = DocumentMetadata()
        assert m.status == "Draft"
        assert m.version == ""

    def test_full_metadata(self):
        m = DocumentMetadata.model_validate({
            "label": "Protocol",
            "version": "2.0",
            "status": "final",
            "template": "ICH",
            "version_date": "2024-06-01",
        })
        assert m.label == "Protocol"
        assert m.version == "2.0"


class TestSection:

    def test_minimal_section(self):
        s = Section.model_validate({"section_number": "1"})
        assert s.section_number == "1"
        assert s.section_title == ""
        assert s.text == ""


class TestDocumentInput:

    def test_empty_defaults(self):
        d = DocumentInput()
        assert d.sections == []

    def test_with_sections(self):
        data = {
            "document": {"label": "Doc", "version": "1.0", "status": "final", "template": "T", "version_date": "2024-01-01"},
            "sections": [
                {"section_number": "1", "section_title": "Intro", "text": "Hello"},
                {"section_number": "2", "section_title": "Methods"},
            ],
        }
        result = DocumentInput.model_validate(data)
        assert len(result.sections) == 2
        assert result.sections[0].text == "Hello"
