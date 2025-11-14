import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup
from simple_error_log.errors import Errors
from usdm4.utility.soup import get_soup


@pytest.fixture
def errors():
    """Create an Errors instance for testing."""
    return Errors()


class TestGetSoupFunction:
    """Test the get_soup function."""

    def test_get_soup_with_valid_html(self, errors):
        """Test get_soup with valid HTML."""
        text = "<p>This is a paragraph</p>"

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("p") is not None
        assert result.find("p").text == "This is a paragraph"

    def test_get_soup_with_plain_text(self, errors):
        """Test get_soup with plain text."""
        text = "This is plain text"

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert str(result).strip() == text

    def test_get_soup_with_empty_string(self, errors):
        """Test get_soup with empty string."""
        text = ""

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert str(result) == ""

    def test_get_soup_with_complex_html(self, errors):
        """Test get_soup with complex HTML structure."""
        text = """
        <div class="container">
            <h1>Title</h1>
            <p>Paragraph with <a href="link">link</a></p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("div") is not None
        assert result.find("h1") is not None
        assert result.find("a") is not None
        assert len(result.find_all("li")) == 2

    def test_get_soup_with_custom_tags(self, errors):
        """Test get_soup with custom XML-like tags."""
        text = '<usdm:ref id="test" attribute="value"/>'

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("usdm:ref") is not None

    def test_get_soup_with_malformed_html(self, errors):
        """Test get_soup with malformed HTML."""
        text = "<p>Unclosed paragraph<div>Nested div</p></div>"

        result = get_soup(text, errors)

        # BeautifulSoup should handle malformed HTML gracefully
        assert isinstance(result, BeautifulSoup)

    def test_get_soup_with_special_characters(self, errors):
        """Test get_soup with special characters."""
        text = "<p>Text with &amp; special &lt; characters &gt;</p>"

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("p") is not None

    def test_get_soup_with_unicode(self, errors):
        """Test get_soup with unicode characters."""
        text = "<p>Text with unicode: é, ñ, 中文, 🎉</p>"

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("p") is not None

    @patch('usdm4.utility.soup.BeautifulSoup')
    def test_get_soup_handles_exception(self, mock_beautiful_soup, errors):
        """Test get_soup handles exceptions from BeautifulSoup."""
        # Mock BeautifulSoup to raise an exception on first call, return empty soup on second
        mock_beautiful_soup.side_effect = [Exception("Parsing error"), BeautifulSoup("", "html.parser")]

        text = "<p>Test</p>"
        result = get_soup(text, errors)

        # Should return empty BeautifulSoup object
        assert isinstance(result, BeautifulSoup)
        assert str(result) == ""

    def test_get_soup_with_nested_html(self, errors):
        """Test get_soup with deeply nested HTML."""
        text = "<div><section><article><p>Nested content</p></article></section></div>"

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        assert result.find("p") is not None
        assert result.find("p").text == "Nested content"

    def test_get_soup_with_attributes(self, errors):
        """Test get_soup preserves HTML attributes."""
        text = '<div class="container" id="main" data-value="test">Content</div>'

        result = get_soup(text, errors)

        assert isinstance(result, BeautifulSoup)
        div = result.find("div")
        assert div is not None
        assert div.get("class") == ["container"]
        assert div.get("id") == "main"
        assert div.get("data-value") == "test"
