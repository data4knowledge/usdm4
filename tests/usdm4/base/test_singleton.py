"""Tests for the Singleton metaclass, including the _clear test-helper."""

from src.usdm4.base.singleton import Singleton


class _S(metaclass=Singleton):
    def __init__(self, value: int = 0):
        self.value = value


def test_singleton_returns_same_instance():
    a = _S(1)
    b = _S(99)  # args ignored after first call
    assert a is b
    assert a.value == 1
    Singleton._clear(_S)


def test_clear_removes_instance_so_next_call_reinitialises():
    """Covers Singleton._clear — lines 14-16."""
    a = _S(10)
    Singleton._clear(_S)
    b = _S(20)
    assert a is not b
    assert b.value == 20
    Singleton._clear(_S)


def test_clear_on_non_registered_class_is_noop():
    class _Unregistered(metaclass=Singleton):
        pass

    # Never instantiated, so name is not in _instances. _clear should not raise.
    Singleton._clear(_Unregistered)
