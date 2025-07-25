import pytest
from src.usdm4.builder.cross_reference import CrossReference, PathError as CRPathError


class CRTest:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.value = "VALUE"


class CRTest2:
    def __init__(self, id, name, instance):
        self.id = id
        self.name = name
        self.child = instance
        self.value = "VALUE"


class CRTest3:
    def __init__(self, id, name, instance):
        self.id = id
        self.name = name
        self.child = instance
        self.value = "VALUE"


def test_create():
    object = CrossReference()
    assert len(object._by_name.keys()) == 0
    assert object._by_name == {}


def test_clear():
    cross_references = CrossReference()
    item = CRTest(id="1234", name="name")
    cross_references._by_name = {}
    cross_references._by_id = {}
    cross_references._by_name["CRTest.name"] = item
    cross_references._by_id["CRTest.1234"] = item
    assert len(cross_references._by_name.keys()) == 1
    assert len(cross_references._by_id.keys()) == 1
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0


def test_add():
    cross_references = CrossReference()
    item = CRTest(id="1234", name="name")
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0
    cross_references.add(item, "name")
    assert len(cross_references._by_name.keys()) == 1
    assert cross_references._by_name["CRTest.name"] == item
    assert len(cross_references._by_id.keys()) == 1
    assert cross_references._by_id["CRTest.1234"] == item


def test_get_by_name():
    cross_references = CrossReference()
    item = CRTest(id="1234", name="name")
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0
    cross_references._by_name["CRTest.name"] = item
    assert cross_references.get_by_name(CRTest, "name") == item


def test_get_by_id():
    cross_references = CrossReference()
    item = CRTest(id="1234", name="name")
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0
    cross_references._by_id["CRTest.1234"] = item
    assert cross_references.get_by_id(CRTest, "1234") == item
    assert cross_references.get_by_id("CRTest", "1234") == item


def test_get_by_path():
    cross_references = CrossReference()
    item1 = CRTest(id="1234", name="name1")
    item2 = CRTest2(id="1235", name="name2", instance=item1)
    item3 = CRTest3(id="1236", name="name3", instance=item2)
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0
    cross_references.add(item1, item1.name)
    cross_references.add(item2, item2.name)
    cross_references.add(item3, item3.name)
    instance, attribute = cross_references.get_by_path(
        "CRTest3", "name3", "child/CRTest2/@child/CRTest/@value"
    )
    assert instance.id == "1234"
    assert attribute == "value"
    instance, attribute = cross_references.get_by_path(
        "CRTest3", "name3", "child/CRTest2/child/CRTest/@value"
    )
    assert instance.id == "1234"
    assert attribute == "value"


def test_get_by_path_errors():
    cross_references = CrossReference()
    item1 = CRTest(id="1234", name="name1")
    item2 = CRTest2(id="1235", name="name2", instance=item1)
    item3 = CRTest3(id="1236", name="name3", instance=item2)
    cross_references.clear()
    assert len(cross_references._by_name.keys()) == 0
    assert len(cross_references._by_id.keys()) == 0
    cross_references.add(item1, item1.name)
    cross_references.add(item2, item2.name)
    cross_references.add(item3, item3.name)
    with pytest.raises(CRPathError) as ex_info:
        instance, attribute = cross_references.get_by_path(
            "CRTest4", "name3", "child/CRTest2/@child/CRTest/@value"
        )
    assert (
        str(ex_info.value)
        == "Failed to translate reference path 'child/CRTest2/@child/CRTest/@value', could not find start instance 'CRTest4', 'name3'"
    )

    with pytest.raises(CRPathError) as ex_info:
        instance, attribute = cross_references.get_by_path(
            "CRTest3", "name3", "child/CRTest4/@child/CRTest/@value"
        )
    assert (
        str(ex_info.value)
        == "Failed to translate reference path 'child/CRTest4/@child/CRTest/@value', class mismtach, expecting 'CRTest4', found 'CRTest2'"
    )

    with pytest.raises(CRPathError) as ex_info:
        instance, attribute = cross_references.get_by_path(
            "CRTest3", "name3", "child/CRTest2/@childXXX/CRTest/@value"
        )
    assert (
        str(ex_info.value)
        == "Failed to translate reference path 'child/CRTest2/@childXXX/CRTest/@value', attribute 'childXXX' was not found"
    )

    with pytest.raises(CRPathError) as ex_info:
        instance, attribute = cross_references.get_by_path(
            "CRTest3", "name3", "child/CRTest2//CRTest/@value"
        )
    assert (
        str(ex_info.value)
        == "Failed to translate reference path 'child/CRTest2//CRTest/@value', attribute '' was not found"
    )

    with pytest.raises(CRPathError) as ex_info:
        instance, attribute = cross_references.get_by_path(
            "CRTest3", "name3", "child/CRTest2/child/CRTest"
        )
    assert (
        str(ex_info.value)
        == "Failed to translate reference path 'child/CRTest2/child/CRTest', format error"
    )
