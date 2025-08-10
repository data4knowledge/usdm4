import pytest
from src.usdm4.builder.base_manager import BaseManager


class TestBaseManager:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.manager = BaseManager()

    def test_init(self):
        """Test BaseManager initialization."""
        manager = BaseManager()
        assert manager._items == {}

    def test_add(self):
        """Test adding items to the manager."""
        self.manager.add("test_key", "test_value")
        assert self.manager._items["TEST_KEY"] == "test_value"

        # Test that keys are converted to uppercase
        self.manager.add("lowercase", "value1")
        assert self.manager._items["LOWERCASE"] == "value1"

        # Test overwriting existing key
        self.manager.add("test_key", "new_value")
        assert self.manager._items["TEST_KEY"] == "new_value"

    def test_get(self):
        """Test getting items from the manager."""
        # Test getting existing item
        self.manager.add("test_key", "test_value")
        assert self.manager.get("test_key") == "test_value"
        assert self.manager.get("TEST_KEY") == "test_value"
        assert self.manager.get("Test_Key") == "test_value"

        # Test getting non-existent item returns empty string
        assert self.manager.get("non_existent") == ""
        assert self.manager.get("MISSING") == ""

    def test_includes(self):
        """Test checking if items exist in the manager."""
        # Test with existing item
        self.manager.add("test_key", "test_value")
        assert self.manager.includes("test_key") is True
        assert self.manager.includes("TEST_KEY") is True
        assert self.manager.includes("Test_Key") is True

        # Test with non-existent item
        assert self.manager.includes("non_existent") is False
        assert self.manager.includes("MISSING") is False

    def test_clear(self):
        """Test clearing all items from the manager."""
        # Add some items
        self.manager.add("key1", "value1")
        self.manager.add("key2", "value2")
        assert len(self.manager._items) == 2

        # Clear and verify empty
        self.manager.clear()
        assert self.manager._items == {}
        assert len(self.manager._items) == 0

    def test_iter(self):
        """Test iterating over the manager."""
        # Test empty manager
        items = list(iter(self.manager))
        assert items == []

        # Add some items and test iteration
        self.manager.add("key1", "value1")
        self.manager.add("key2", "value2")
        self.manager.add("key3", "value3")

        items = list(iter(self.manager))
        assert len(items) == 3
        assert "KEY1" in items
        assert "KEY2" in items
        assert "KEY3" in items

    def test_case_insensitive_operations(self):
        """Test that all operations are case insensitive."""
        # Add with lowercase
        self.manager.add("lowercase", "value1")

        # Get with different cases
        assert self.manager.get("lowercase") == "value1"
        assert self.manager.get("LOWERCASE") == "value1"
        assert self.manager.get("LowerCase") == "value1"

        # Check includes with different cases
        assert self.manager.includes("lowercase") is True
        assert self.manager.includes("LOWERCASE") is True
        assert self.manager.includes("LowerCase") is True

        # Add with uppercase should overwrite
        self.manager.add("LOWERCASE", "value2")
        assert self.manager.get("lowercase") == "value2"

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        # Add empty string as value
        self.manager.add("empty", "")
        assert self.manager.get("empty") == ""
        assert self.manager.includes("empty") is True

        # Add empty string as key
        self.manager.add("", "empty_key_value")
        assert self.manager.get("") == "empty_key_value"
        assert self.manager.includes("") is True

    def test_multiple_operations(self):
        """Test multiple operations in sequence."""
        # Add multiple items
        self.manager.add("item1", "value1")
        self.manager.add("item2", "value2")
        self.manager.add("item3", "value3")

        # Verify all exist
        assert self.manager.includes("item1") is True
        assert self.manager.includes("item2") is True
        assert self.manager.includes("item3") is True

        # Get all values
        assert self.manager.get("item1") == "value1"
        assert self.manager.get("item2") == "value2"
        assert self.manager.get("item3") == "value3"

        # Clear and verify empty
        self.manager.clear()
        assert self.manager.includes("item1") is False
        assert self.manager.includes("item2") is False
        assert self.manager.includes("item3") is False
        assert self.manager.get("item1") == ""
        assert self.manager.get("item2") == ""
        assert self.manager.get("item3") == ""

    def test_special_characters(self):
        """Test handling of special characters in keys and values."""
        # Test with special characters
        self.manager.add("key-with-dashes", "value-with-dashes")
        self.manager.add("key_with_underscores", "value_with_underscores")
        self.manager.add("key.with.dots", "value.with.dots")
        self.manager.add("key with spaces", "value with spaces")

        assert self.manager.get("key-with-dashes") == "value-with-dashes"
        assert self.manager.get("key_with_underscores") == "value_with_underscores"
        assert self.manager.get("key.with.dots") == "value.with.dots"
        assert self.manager.get("key with spaces") == "value with spaces"

        assert self.manager.includes("key-with-dashes") is True
        assert self.manager.includes("key_with_underscores") is True
        assert self.manager.includes("key.with.dots") is True
        assert self.manager.includes("key with spaces") is True
