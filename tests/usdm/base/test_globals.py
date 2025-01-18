from usdm4.base.globals import Globals


def test_globals():
    globals = Globals()
    assert globals is not None


def test_globals_clear():
    globals = Globals()
    globals.clear()
    assert globals.errors is not None
    assert globals.id_manager is not None
