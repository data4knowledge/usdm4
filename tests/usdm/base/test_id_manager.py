from usdm.base.id_manager import IdManager
from usdm.api.address import Address


def test_init():
    instance_1 = IdManager(["Address", "xxx"])
    assert instance_1._id_index["Address"] == 0
    assert instance_1._id_index["xxx"] == 0


def test_clear():
    instance_1 = IdManager(["Address", "xxx"])
    instance_1.clear()
    assert instance_1._id_index["Address"] == 0
    assert instance_1._id_index["xxx"] == 0


def test_build_id_with_string():
    instance_1 = IdManager(["Address", "xxx"])
    assert instance_1.build_id("Address") == "Address_1"
    assert instance_1.build_id("Address") == "Address_2"
    assert instance_1.build_id("xxx") == "xxx_1"
    assert instance_1.build_id("xxx") == "xxx_2"


def test_build_id_with_class():
    instance_1 = IdManager(["Address"])
    assert instance_1.build_id(Address) == "Address_1"
    assert instance_1.build_id(Address) == "Address_2"
