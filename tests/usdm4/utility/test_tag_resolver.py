import pytest
from unittest.mock import Mock
from bs4 import BeautifulSoup
from simple_error_log.errors import Errors
from usdm4.utility.tag_resolver import TagResolver


@pytest.fixture
def errors():
    """Create an Errors instance for testing."""
    return Errors()


@pytest.fixture
def data_store():
    """Create a mocked data store for testing."""
    return Mock()


@pytest.fixture
def tag_resolver(data_store, errors):
    """Create a TagResolver instance for testing."""
    return TagResolver(data_store, errors)


@pytest.fixture
def tag_resolver_with_data_store(data_store, errors):
    """Create a TagResolver instance with a mocked data store."""
    return TagResolver(data_store, errors)


class TestTagResolverInitialization:
    """Test TagResolver initialization."""

    def test_init_with_valid_parameters(self, data_store, errors):
        """Test TagResolver initialization with valid parameters."""
        resolver = TagResolver(data_store, errors)

        assert resolver._data_store is data_store
        assert resolver._errors is errors
        assert isinstance(resolver._errors, Errors)

    def test_init_stores_data_store_reference(self, data_store, errors):
        """Test that TagResolver stores the data_store reference correctly."""
        resolver = TagResolver(data_store, errors)

        # Verify the data_store reference is stored and accessible
        assert hasattr(resolver, "_data_store")
        assert resolver._data_store is data_store

    def test_init_stores_errors_reference(self, data_store, errors):
        """Test that TagResolver stores the errors reference correctly."""
        resolver = TagResolver(data_store, errors)

        # Verify the errors reference is stored and accessible
        assert hasattr(resolver, "_errors")
        assert resolver._errors is errors

    def test_init_sets_module_constant(self, data_store, errors):
        """Test that TagResolver sets the MODULE constant correctly."""
        resolver = TagResolver(data_store, errors)

        assert hasattr(resolver, "MODULE")
        assert resolver.MODULE == "usdm4.utility.tag_resolver.TagResolver"


class TestTranslateMethod:
    """Test the translate method."""

    def test_translate_simple_text_without_tags(self, tag_resolver_with_data_store):
        """Test translate with simple text containing no special tags."""
        instance = {"id": "test-instance-1"}
        text = "This is simple text without any tags"

        result = tag_resolver_with_data_store.translate(instance, text)

        assert result == text

    def test_translate_html_text_without_special_tags(self, tag_resolver_with_data_store):
        """Test translate with HTML text containing no special tags."""
        instance = {"id": "test-instance-1"}
        text = "<p>This is <b>bold</b> text</p>"

        result = tag_resolver_with_data_store.translate(instance, text)

        # BeautifulSoup may normalize the HTML
        assert "<b>bold</b>" in result or "<strong>bold</strong>" in result

    def test_translate_empty_text(self, tag_resolver_with_data_store):
        """Test translate with empty text."""
        instance = {"id": "test-instance-1"}
        text = ""

        result = tag_resolver_with_data_store.translate(instance, text)

        assert result == ""

    def test_translate_with_usdm_ref_tag(self, tag_resolver_with_data_store):
        """Test translate with usdm:ref tag."""
        instance = {"id": "test-instance-1"}
        text = 'This is a <usdm:ref id="ref-1" attribute="name"/> reference'
        
        # Mock the data store to return a referenced instance
        referenced_instance = {"id": "ref-1", "name": "Test Name"}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "Test Name" in result
        assert "usdm:ref" not in result

    def test_translate_with_usdm_tag(self, tag_resolver_with_data_store):
        """Test translate with usdm:tag."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        text = 'This uses <usdm:tag name="parameter1"/> tag'
        
        # Mock the data store to return a dictionary with parameter maps
        dictionary = {
            "id": "dict-1",
            "parameterMaps": [
                {"tag": "parameter1", "reference": "resolved value"}
            ]
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "resolved value" in result
        assert "usdm:tag" not in result

    def test_translate_with_multiple_tags(self, tag_resolver_with_data_store):
        """Test translate with multiple special tags."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        text = 'Text with <usdm:ref id="ref-1" attribute="value"/> and <usdm:ref id="ref-2" attribute="name"/>'
        
        # Mock the data store to return different instances based on id
        def mock_instance_by_id(id_value):
            if id_value == "ref-1":
                return {"id": "ref-1", "value": "Value1"}
            elif id_value == "ref-2":
                return {"id": "ref-2", "name": "Name2"}
            return None
        
        tag_resolver_with_data_store._data_store.instance_by_id.side_effect = mock_instance_by_id

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "Value1" in result
        assert "Name2" in result


class TestTranslateReferencesMethod:
    """Test the _translate_references private method."""

    def test_translate_references_with_nested_tags(self, tag_resolver_with_data_store):
        """Test _translate_references with nested special tags."""
        instance = {"id": "test-instance-1"}
        text = '<div><usdm:ref id="ref-1" attribute="content"/></div>'
        
        # Mock to return text that itself contains a tag
        referenced_instance = {"id": "ref-1", "content": "Nested content"}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store._translate_references(instance, text)

        assert "Nested content" in result
        assert "usdm:ref" not in result

    def test_translate_references_exception_handling(self, tag_resolver_with_data_store):
        """Test _translate_references handles exceptions gracefully."""
        instance = {"id": "test-instance-1"}
        text = '<usdm:ref id="ref-1" attribute="value"/>'
        
        # Mock to raise an exception
        tag_resolver_with_data_store._data_store.instance_by_id.side_effect = Exception("Test exception")

        # Should handle exception and continue
        result = tag_resolver_with_data_store._translate_references(instance, text)

        # Exception should be logged but method should return something
        assert result is not None


class TestResolveUsdmRefMethod:
    """Test the _resolve_usdm_ref private method."""

    def test_resolve_usdm_ref_basic(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_ref with valid reference."""
        instance = {"id": "test-instance-1"}
        soup = BeautifulSoup('<usdm:ref id="ref-1" attribute="name"/>', "html.parser")
        ref_tag = soup.find("usdm:ref")
        
        # Mock the data store
        referenced_instance = {"id": "ref-1", "name": "Referenced Name"}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store._resolve_usdm_ref(instance, ref_tag)

        assert result == "Referenced Name"
        tag_resolver_with_data_store._data_store.instance_by_id.assert_called_once_with("ref-1")

    def test_resolve_usdm_ref_with_numeric_attribute(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_ref with numeric attribute value."""
        instance = {"id": "test-instance-1"}
        soup = BeautifulSoup('<usdm:ref id="ref-1" attribute="count"/>', "html.parser")
        ref_tag = soup.find("usdm:ref")
        
        # Mock the data store with numeric value
        referenced_instance = {"id": "ref-1", "count": 42}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store._resolve_usdm_ref(instance, ref_tag)

        assert result == "42"

    def test_resolve_usdm_ref_with_boolean_attribute(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_ref with boolean attribute value."""
        instance = {"id": "test-instance-1"}
        soup = BeautifulSoup('<usdm:ref id="ref-1" attribute="active"/>', "html.parser")
        ref_tag = soup.find("usdm:ref")
        
        # Mock the data store with boolean value
        referenced_instance = {"id": "ref-1", "active": True}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store._resolve_usdm_ref(instance, ref_tag)

        assert result == "True"

    def test_resolve_usdm_ref_with_none_attribute(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_ref with None attribute value."""
        instance = {"id": "test-instance-1"}
        soup = BeautifulSoup('<usdm:ref id="ref-1" attribute="optional"/>', "html.parser")
        ref_tag = soup.find("usdm:ref")
        
        # Mock the data store with None value
        referenced_instance = {"id": "ref-1", "optional": None}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store._resolve_usdm_ref(instance, ref_tag)

        assert result == "None"

    def test_resolve_usdm_ref_missing_attribute_raises_error(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_ref raises error when attribute is missing."""
        instance = {"id": "test-instance-1"}
        soup = BeautifulSoup('<usdm:ref id="ref-1" attribute="missing"/>', "html.parser")
        ref_tag = soup.find("usdm:ref")
        
        # Mock the data store without the requested attribute
        referenced_instance = {"id": "ref-1", "name": "Referenced Name"}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        with pytest.raises(KeyError):
            tag_resolver_with_data_store._resolve_usdm_ref(instance, ref_tag)


class TestResolveUsdmTagMethod:
    """Test the _resolve_usdm_tag private method."""

    def test_resolve_usdm_tag_found(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_tag when tag is found in dictionary."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        soup = BeautifulSoup('<usdm:tag name="param1"/>', "html.parser")
        tag_element = soup.find("usdm:tag")
        
        # Mock the data store with a dictionary containing the parameter
        dictionary = {
            "id": "dict-1",
            "parameterMaps": [
                {"tag": "param1", "reference": "param1 value"},
                {"tag": "param2", "reference": "param2 value"}
            ]
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store._resolve_usdm_tag(instance, tag_element)

        assert result == "param1 value"

    def test_resolve_usdm_tag_not_found_in_parameter_maps(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_tag when tag is not found in parameter maps."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        soup = BeautifulSoup('<usdm:tag name="missing-param"/>', "html.parser")
        tag_element = soup.find("usdm:tag")
        
        # Mock the data store with a dictionary without the requested parameter
        dictionary = {
            "id": "dict-1",
            "parameterMaps": [
                {"tag": "param1", "reference": "param1 value"}
            ]
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store._resolve_usdm_tag(instance, tag_element)

        # Should return error message
        assert "failed to resolve tag" in result
        assert "test-instance-1" in result

    def test_resolve_usdm_tag_no_dictionary(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_tag when dictionary is not found."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        soup = BeautifulSoup('<usdm:tag name="param1"/>', "html.parser")
        tag_element = soup.find("usdm:tag")
        
        # Mock the data store to return None (no dictionary found)
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = None

        result = tag_resolver_with_data_store._resolve_usdm_tag(instance, tag_element)

        # Should return error message
        assert "failed to resolve tag" in result
        assert "test-instance-1" in result

    def test_resolve_usdm_tag_empty_parameter_maps(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_tag with empty parameter maps."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        soup = BeautifulSoup('<usdm:tag name="param1"/>', "html.parser")
        tag_element = soup.find("usdm:tag")
        
        # Mock the data store with empty parameter maps
        dictionary = {
            "id": "dict-1",
            "parameterMaps": []
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store._resolve_usdm_tag(instance, tag_element)

        # Should return error message
        assert "failed to resolve tag" in result

    def test_resolve_usdm_tag_multiple_parameters(self, tag_resolver_with_data_store):
        """Test _resolve_usdm_tag with multiple parameters in dictionary."""
        instance = {"id": "test-instance-1", "dictionaryId": "dict-1"}
        soup = BeautifulSoup('<usdm:tag name="param3"/>', "html.parser")
        tag_element = soup.find("usdm:tag")
        
        # Mock the data store with multiple parameters
        dictionary = {
            "id": "dict-1",
            "parameterMaps": [
                {"tag": "param1", "reference": "value1"},
                {"tag": "param2", "reference": "value2"},
                {"tag": "param3", "reference": "value3"},
                {"tag": "param4", "reference": "value4"}
            ]
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store._resolve_usdm_tag(instance, tag_element)

        assert result == "value3"


class TestIntegrationScenarios:
    """Integration tests for complete translation workflows."""

    def test_complete_translation_workflow(self, tag_resolver_with_data_store):
        """Test complete translation workflow with mixed content."""
        instance = {"id": "study-1", "dictionaryId": "dict-1"}
        text = """
        <div>
            <h1>Study Title: <usdm:ref id="title-1" attribute="value"/></h1>
            <p>Parameter: <usdm:tag name="param1"/></p>
            <p>Regular text with <b>bold</b> content</p>
        </div>
        """
        
        # Mock the data store
        def mock_instance_by_id(id_value):
            if id_value == "title-1":
                return {"id": "title-1", "value": "Clinical Study ABC"}
            elif id_value == "dict-1":
                return {
                    "id": "dict-1",
                    "parameterMaps": [
                        {"tag": "param1", "reference": "Parameter Value"}
                    ]
                }
            return None
        
        tag_resolver_with_data_store._data_store.instance_by_id.side_effect = mock_instance_by_id

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "Clinical Study ABC" in result
        assert "Parameter Value" in result
        assert "<b>bold</b>" in result or "<strong>bold</strong>" in result
        assert "usdm:ref" not in result
        assert "usdm:tag" not in result

    def test_translation_with_no_special_tags(self, tag_resolver_with_data_store):
        """Test translation with content that has no special tags."""
        instance = {"id": "test-1"}
        text = """
        <article>
            <h2>Regular Content</h2>
            <p>This is regular HTML content without any special tags.</p>
        </article>
        """

        result = tag_resolver_with_data_store.translate(instance, text)

        # Should return the content relatively unchanged (maybe normalized by BeautifulSoup)
        assert "Regular Content" in result
        assert "usdm:ref" not in result
        assert "usdm:tag" not in result

    def test_translation_with_only_usdm_ref(self, tag_resolver_with_data_store):
        """Test translation with only usdm:ref tags."""
        instance = {"id": "test-1"}
        text = 'Study: <usdm:ref id="study-1" attribute="name"/> Version: <usdm:ref id="study-1" attribute="version"/>'
        
        # Mock the data store
        referenced_instance = {"id": "study-1", "name": "Study Name", "version": "1.0"}
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = referenced_instance

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "Study Name" in result
        assert "1.0" in result
        assert "usdm:ref" not in result

    def test_translation_with_only_usdm_tag(self, tag_resolver_with_data_store):
        """Test translation with only usdm:tag tags."""
        instance = {"id": "test-1", "dictionaryId": "dict-1"}
        text = 'Value 1: <usdm:tag name="p1"/> Value 2: <usdm:tag name="p2"/>'
        
        # Mock the data store
        dictionary = {
            "id": "dict-1",
            "parameterMaps": [
                {"tag": "p1", "reference": "First Value"},
                {"tag": "p2", "reference": "Second Value"}
            ]
        }
        tag_resolver_with_data_store._data_store.instance_by_id.return_value = dictionary

        result = tag_resolver_with_data_store.translate(instance, text)

        assert "First Value" in result
        assert "Second Value" in result
        assert "usdm:tag" not in result
