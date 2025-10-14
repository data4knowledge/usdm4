import json
import enum
import datetime
from uuid import UUID
from src.usdm4.api.serialize import serialize_as_json
from src.usdm4.api.api_base_model import (
    ApiBaseModel,
    ApiBaseModelWithIdOnly,
    ApiBaseModelWithId,
    ApiBaseModelWithIdAndDesc,
    ApiBaseModelWithIdAndName,
    ApiBaseModelWithIdNameAndLabel,
    ApiBaseModelWithIdNameLabelAndDesc,
    ApiBaseModelWithIdNameAndDesc,
    serialize_as_json,
)
from src.usdm4.api.extension import ExtensionAttribute


class TestEnum(enum.Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"


class TestObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class TestApiBaseModel:
    def testserialize_as_json_enum(self):
        """Test serialize_as_json with enum."""
        test_enum = TestEnum.VALUE1
        result = serialize_as_json(test_enum)
        assert result == "value1"

    def testserialize_as_json_date(self):
        """Test serialize_as_json with date."""
        test_date = datetime.date(2023, 12, 25)
        result = serialize_as_json(test_date)
        assert result == "2023-12-25"

    def testserialize_as_json_uuid(self):
        """Test serialize_as_json with UUID."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = serialize_as_json(test_uuid)
        assert result == "12345678-1234-5678-1234-567812345678"

    def testserialize_as_json_object(self):
        """Test serialize_as_json with regular object."""
        test_obj = TestObject("test", 42)
        result = serialize_as_json(test_obj)
        expected = {"name": "test", "value": 42}
        assert result == expected

    def test_api_base_model_init(self):
        """Test ApiBaseModel initialization."""
        model = ApiBaseModel()
        # Test that the model can be created
        assert isinstance(model, ApiBaseModel)
        # Test that the model has the expected methods
        assert hasattr(model, "to_json")

    def test_api_base_model_to_json(self):
        """Test ApiBaseModel to_json method."""
        model = ApiBaseModel()
        json_str = model.to_json()
        parsed = json.loads(json_str)
        # The model should serialize to an empty dict by default
        assert isinstance(parsed, dict)

    def test_api_base_model_with_id_only(self):
        """Test ApiBaseModelWithIdOnly."""
        model = ApiBaseModelWithIdOnly(id="test_id")
        assert model.id == "test_id"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id(self):
        """Test ApiBaseModelWithId with default extensionAttributes."""
        model = ApiBaseModelWithId(id="test_id")
        assert model.id == "test_id"
        assert model.extensionAttributes == []
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_and_extensions(self):
        """Test ApiBaseModelWithId with extension attributes."""
        ext_attr = ExtensionAttribute(
            id="ext1",
            url="http://example.com/extension",
            instanceType="ExtensionAttribute",
        )
        model = ApiBaseModelWithId(id="test_id", extensionAttributes=[ext_attr])
        assert model.id == "test_id"
        assert len(model.extensionAttributes) == 1
        assert model.extensionAttributes[0].id == "ext1"
        assert model.extensionAttributes[0].url == "http://example.com/extension"

    def test_api_base_model_with_id_and_desc(self):
        """Test ApiBaseModelWithIdAndDesc."""
        model = ApiBaseModelWithIdAndDesc(id="test_id", description="Test description")
        assert model.id == "test_id"
        assert model.description == "Test description"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_and_desc_none(self):
        """Test ApiBaseModelWithIdAndDesc with None description."""
        model = ApiBaseModelWithIdAndDesc(id="test_id")
        assert model.id == "test_id"
        assert model.description is None

    def test_api_base_model_with_id_and_name(self):
        """Test ApiBaseModelWithIdAndName."""
        model = ApiBaseModelWithIdAndName(id="test_id", name="Test Name")
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_name_and_label(self):
        """Test ApiBaseModelWithIdNameAndLabel."""
        model = ApiBaseModelWithIdNameAndLabel(
            id="test_id", name="Test Name", label="Test Label"
        )
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.label == "Test Label"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_name_and_label_none(self):
        """Test ApiBaseModelWithIdNameAndLabel with None label."""
        model = ApiBaseModelWithIdNameAndLabel(id="test_id", name="Test Name")
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.label is None

    def test_label_name_with_label(self):
        """Test label_name method when label is provided."""
        model = ApiBaseModelWithIdNameAndLabel(
            id="test_id", name="Test Name", label="Test Label"
        )
        assert model.label_name() == "Test Label"

    def test_label_name_without_label(self):
        """Test label_name method when label is None."""
        model = ApiBaseModelWithIdNameAndLabel(id="test_id", name="Test Name")
        assert model.label_name() == "Test Name"

    def test_label_name_with_empty_label(self):
        """Test label_name method when label is empty string."""
        model = ApiBaseModelWithIdNameAndLabel(id="test_id", name="Test Name", label="")
        assert model.label_name() == "Test Name"

    def test_api_base_model_with_id_name_label_and_desc(self):
        """Test ApiBaseModelWithIdNameLabelAndDesc."""
        model = ApiBaseModelWithIdNameLabelAndDesc(
            id="test_id",
            name="Test Name",
            label="Test Label",
            description="Test Description",
        )
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.label == "Test Label"
        assert model.description == "Test Description"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_name_label_and_desc_none(self):
        """Test ApiBaseModelWithIdNameLabelAndDesc with None values."""
        model = ApiBaseModelWithIdNameLabelAndDesc(id="test_id", name="Test Name")
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.label is None
        assert model.description is None

    def test_api_base_model_with_id_name_and_desc(self):
        """Test ApiBaseModelWithIdNameAndDesc."""
        model = ApiBaseModelWithIdNameAndDesc(
            id="test_id", name="Test Name", description="Test Description"
        )
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.description == "Test Description"
        assert isinstance(model, ApiBaseModel)

    def test_api_base_model_with_id_name_and_desc_none(self):
        """Test ApiBaseModelWithIdNameAndDesc with None description."""
        model = ApiBaseModelWithIdNameAndDesc(id="test_id", name="Test Name")
        assert model.id == "test_id"
        assert model.name == "Test Name"
        assert model.description is None

    def test_inheritance_chain(self):
        """Test that inheritance chain works correctly."""
        # Test that all models inherit from ApiBaseModel
        models = [
            ApiBaseModelWithIdOnly(id="test"),
            ApiBaseModelWithId(id="test"),
            ApiBaseModelWithIdAndDesc(id="test"),
            ApiBaseModelWithIdAndName(id="test", name="test"),
            ApiBaseModelWithIdNameAndLabel(id="test", name="test"),
            ApiBaseModelWithIdNameLabelAndDesc(id="test", name="test"),
            ApiBaseModelWithIdNameAndDesc(id="test", name="test"),
        ]

        for model in models:
            assert isinstance(model, ApiBaseModel)
            assert hasattr(model, "to_json")

    def test_json_serialization_with_complex_data(self):
        """Test JSON serialization with complex data types."""
        ext_attr = ExtensionAttribute(
            id="ext1",
            url="http://example.com/extension",
            instanceType="ExtensionAttribute",
        )

        model = ApiBaseModelWithIdNameLabelAndDesc(
            id="test_id",
            name="Test Name",
            label="Test Label",
            description="Test Description",
            extensionAttributes=[ext_attr],
        )

        # Test regular JSON serialization
        json_str = model.to_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == "test_id"
        assert parsed["name"] == "Test Name"


class TestApiBaseModelWithIdOnly:
    def test_label_name(self):
        item = ApiBaseModelWithIdOnly(id="1")
        assert item.label_name() == ""


class TestApiBaseModelWithId:
    def test_find_extension(self):
        ext_1 = ExtensionAttribute(
            id="1",
            url="http://www.example.com/ext-001",
            valueString="001",
            instanceType="ExtensionAttribute",
        )
        ext_2 = ExtensionAttribute(
            id="1",
            url="http://www.example.com/ext-002",
            valueString="002",
            instanceType="ExtensionAttribute",
        )
        ext_3 = ExtensionAttribute(
            id="1",
            url="http://www.example.com/ext-003",
            valueString="003",
            instanceType="ExtensionAttribute",
        )
        item = ApiBaseModelWithId(id="2", extensionAttributes=[ext_1, ext_2, ext_3])
        ext = item.get_extension("http://www.example.com/ext-003")
        assert ext is ext_3
        ext = item.get_extension("http://www.example.com/ext-001")
        assert ext is ext_1
        ext = item.get_extension("http://www.example.com/ext-002")
        assert ext is ext_2
        ext = item.get_extension("http://www.example.com/ext-004")
        assert ext is None


class TestApiBaseModelWithIdAndName:
    def test_label_name(self):
        item = ApiBaseModelWithIdAndName(id="2", name="xxx")
        assert item.label_name() == "xxx"


class TestApiBaseModelWithIdNameAndLabel:
    def test_label_name_name(self):
        item = ApiBaseModelWithIdNameAndLabel(id="2", name="xxx", label="")
        assert item.label_name() == "xxx"

    def test_label_name_label(self):
        item = ApiBaseModelWithIdNameAndLabel(id="2", name="xxx", label="123")
        assert item.label_name() == "123"
