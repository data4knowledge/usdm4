"""Tests for IdManager — build_id, add_id, and the _find_id_instance regex."""

from src.usdm4.base.id_manager import IdManager


class DummyKlass:
    pass


def test_initial_state_zero_indexed():
    mgr = IdManager(["DummyKlass"])
    assert mgr.build_id("DummyKlass") == "DummyKlass_1"
    assert mgr.build_id("DummyKlass") == "DummyKlass_2"


def test_build_id_accepts_class_object():
    mgr = IdManager([DummyKlass])
    assert mgr.build_id(DummyKlass) == "DummyKlass_1"


def test_clear_resets_counters():
    mgr = IdManager(["DummyKlass"])
    mgr.build_id("DummyKlass")
    mgr.build_id("DummyKlass")
    mgr.clear()
    assert mgr.build_id("DummyKlass") == "DummyKlass_1"


def test_add_id_bumps_counter_when_higher():
    """Covers the `self._id_index[klass_name] = instance` branch (line 23):
    an existing id with a higher instance number must advance the counter."""
    mgr = IdManager(["DummyKlass"])
    mgr.build_id("DummyKlass")  # counter now 1
    mgr.add_id("DummyKlass", "DummyKlass_5")  # should bump counter to 5
    assert mgr.build_id("DummyKlass") == "DummyKlass_6"


def test_add_id_ignores_lower_number():
    mgr = IdManager(["DummyKlass"])
    for _ in range(3):
        mgr.build_id("DummyKlass")  # counter now 3
    mgr.add_id("DummyKlass", "DummyKlass_1")  # lower — should not change
    assert mgr.build_id("DummyKlass") == "DummyKlass_4"


def test_add_id_with_non_matching_pattern_is_noop():
    mgr = IdManager(["DummyKlass"])
    mgr.build_id("DummyKlass")  # counter now 1
    mgr.add_id("DummyKlass", "nonsense-no-underscore-digit")
    assert mgr.build_id("DummyKlass") == "DummyKlass_2"
