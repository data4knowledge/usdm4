from src.usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem


class TestNarrativeContentLevel:
    """Test NarrativeContent.level() method."""

    def test_level_none_section_number(self):
        """Test level returns 1 when sectionNumber is None (covers line 32)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 1

    def test_level_appendix_section_number(self):
        """Test level returns 1 when sectionNumber starts with 'appendix' (covers line 34)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="Appendix A",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 1

    def test_level_appendix_lowercase(self):
        """Test level returns 1 for lowercase 'appendix' prefix."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="appendix b",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 1

    def test_level_single_number(self):
        """Test level returns 1 for top-level section number."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 1

    def test_level_two_part_number(self):
        """Test level returns 2 for two-part section number."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1.2",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 2

    def test_level_three_part_number(self):
        """Test level returns 3 for three-part section number."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1.2.3",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 3

    def test_level_trailing_dot(self):
        """Test level strips trailing dot before counting."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1.2.",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.level() == 2


class TestNarrativeContentFormatHeading:
    """Test NarrativeContent.format_heading() method."""

    def test_format_heading_zero_section_number(self):
        """Test format_heading returns empty string when number is '0' (covers line 47)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="0",
            sectionTitle="Title",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == ""

    def test_format_heading_number_only(self):
        """Test format_heading with number but no title (covers lines 50-51)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="3",
            sectionTitle=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == "<h1>3</h1>"

    def test_format_heading_title_only(self):
        """Test format_heading with title but no number (covers lines 52-53)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber=None,
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == "<h1>Introduction</h1>"

    def test_format_heading_neither_number_nor_title(self):
        """Test format_heading with no number or title (covers lines 54-55)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber=None,
            sectionTitle=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == ""

    def test_format_heading_number_and_title(self):
        """Test format_heading with both number and title."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == "<h1>2 Methods</h1>"

    def test_format_heading_nested_section_level(self):
        """Test format_heading uses correct heading level for nested sections."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="2.3",
            sectionTitle="Sub-section",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == "<h2>2.3 Sub-section</h2>"

    def test_format_heading_number_only_nested(self):
        """Test format_heading number-only with nested level (covers lines 50-51)."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1.2.3",
            sectionTitle=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )
        assert nc.format_heading() == "<h3>1.2.3</h3>"


class TestNarrativeContentContent:
    """Test NarrativeContent.content() method."""

    def _create_item_map(self, item_id: str, text: str) -> dict:
        """Helper to create a narrative content item map."""
        item = NarrativeContentItem(
            id=item_id,
            name="Item",
            text=text,
            instanceType="NarrativeContentItem",
        )
        return {item_id: item}

    def test_content_with_heading_and_text(self):
        """Test content returns heading + text when content item exists."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="item1",
            instanceType="NarrativeContent",
        )
        item_map = self._create_item_map("item1", "<p>Hello world</p>")
        assert nc.content(item_map) == "<h1>1 Introduction</h1><p>Hello world</p>"

    def test_content_no_heading(self):
        """Test content returns just text when there is no heading."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber=None,
            sectionTitle=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="item1",
            instanceType="NarrativeContent",
        )
        item_map = self._create_item_map("item1", "<p>Body text</p>")
        assert nc.content(item_map) == "<p>Body text</p>"

    def test_content_item_not_in_map(self):
        """Test content returns None when contentItemId is not in the map."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1",
            sectionTitle="Title",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="missing_id",
            instanceType="NarrativeContent",
        )
        item_map = self._create_item_map("item1", "some text")
        assert nc.content(item_map) is None

    def test_content_no_content_item_id(self):
        """Test content returns None when contentItemId is None."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1",
            sectionTitle="Title",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId=None,
            instanceType="NarrativeContent",
        )
        assert nc.content({}) is None

    def test_content_empty_map(self):
        """Test content returns None with empty map."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="1",
            sectionTitle="Title",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="item1",
            instanceType="NarrativeContent",
        )
        assert nc.content({}) is None

    def test_content_nested_section(self):
        """Test content with nested section number produces correct heading level."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="2.3.1",
            sectionTitle="Details",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="item1",
            instanceType="NarrativeContent",
        )
        item_map = self._create_item_map("item1", "<p>Detail text</p>")
        assert nc.content(item_map) == "<h3>2.3.1 Details</h3><p>Detail text</p>"

    def test_content_zero_section_number(self):
        """Test content with section number '0' produces no heading."""
        nc = NarrativeContent(
            id="nc1",
            name="Test",
            sectionNumber="0",
            sectionTitle="Hidden",
            displaySectionNumber=True,
            displaySectionTitle=True,
            contentItemId="item1",
            instanceType="NarrativeContent",
        )
        item_map = self._create_item_map("item1", "<p>Preamble</p>")
        assert nc.content(item_map) == "<p>Preamble</p>"
