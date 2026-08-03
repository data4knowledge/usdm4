"""
Pytest configuration for the entire USDM4 test suite.

This conftest provides:
1. Environment setup/teardown for test execution
2. Performance optimizations to speed up test execution by sharing expensive-to-create objects
"""

import pytest
import os
import pathlib
from dotenv import load_dotenv
from simple_error_log.errors import Errors


def set_test():
    load_dotenv(".test_env")


def clear_test():
    load_dotenv(".development_env")


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    set_test()
    yield
    clear_test()


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="session")
def usdm4_root_path():
    """
    Session-scoped fixture providing the USDM4 root path.
    Computed once for the entire test session.
    """
    return root_path()


@pytest.fixture(scope="session")
def shared_builder(usdm4_root_path):
    """
    Session-scoped Builder instance.

    The Builder loads CT (Controlled Terminology) libraries which is expensive
    (~3 seconds). By creating it once per session, we avoid this overhead in
    every test.

    IMPORTANT: Tests using this fixture should call builder.clear() to reset
    state, but must not mutate the CT libraries themselves.

    Example usage:
        def test_something(shared_builder):
            shared_builder.clear()  # Reset state
            code = shared_builder.iso639_code("en")
            assert code is not None
    """
    from usdm4.builder.builder import Builder

    errors = Errors()
    builder = Builder(usdm4_root_path, errors)
    return builder


@pytest.fixture
def fresh_builder(shared_builder):
    """
    Function-scoped Builder that reuses CT libraries but has clean state.

    This fixture provides a Builder with cleared state for each test,
    but reuses the expensive CT library data from shared_builder.

    Example usage:
        def test_something(fresh_builder):
            # Builder is ready to use with clean state
            code = fresh_builder.iso639_code("en")
            assert code is not None
    """
    shared_builder.clear()
    # Create a fresh Errors object for this test
    shared_builder.errors = Errors()
    return shared_builder


@pytest.fixture(scope="session")
def shared_assembler(usdm4_root_path):
    """
    Session-scoped Assembler instance.

    The Assembler creates a Builder which loads CT libraries. By creating
    it once per session, we avoid the ~3 second overhead in every test.

    IMPORTANT: Tests using this fixture should call assembler.clear() to
    reset state.

    Example usage:
        def test_something(shared_assembler):
            assembler.clear()  # Reset state
            # Use assembler...
    """
    from usdm4.assembler.assembler import Assembler

    errors = Errors()
    assembler = Assembler(usdm4_root_path, errors)
    return assembler


@pytest.fixture
def fresh_assembler(shared_assembler):
    """
    Function-scoped Assembler that reuses CT libraries but has clean state.

    This fixture provides an Assembler with cleared state for each test.

    Example usage:
        def test_something(fresh_assembler):
            # Assembler is ready to use with clean state
            result = fresh_assembler.execute(data)
            assert result is not None
    """
    shared_assembler.clear()
    return shared_assembler


@pytest.fixture
def errors():
    """
    Function-scoped Errors object.

    Provides a fresh error logger for each test.

    Example usage:
        def test_something(errors):
            errors.error("Something went wrong")
            assert errors.count() == 1
    """
    return Errors()


# Optional: Pytest hook to show slow imports (useful for debugging)
def pytest_sessionstart(session):
    """
    Hook that runs at the start of the test session.
    Can be used to show performance information.
    """
    if session.config.getoption("verbose") > 1:
        print("\n" + "=" * 70)
        print("USDM4 Test Suite - Performance Optimizations Active")
        print("- Shared Builder: CT libraries loaded once per session")
        print("- Shared Assembler: Reuses Builder and CT libraries")
        print("=" * 70)
