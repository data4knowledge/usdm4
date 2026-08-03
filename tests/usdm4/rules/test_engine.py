"""Tests for RulesValidationEngine.

Uses heavy mocking to avoid loading every rule_ddf file, a real
DataStore, or a CTLibrary with disk/API access.
"""

from unittest.mock import MagicMock, patch

import pytest


from src.usdm4.rules.engine import RulesValidationEngine
from src.usdm4.rules.results import RuleStatus
from src.usdm4.rules.rule_template import RuleTemplate

# Note: engine.py imports DecompositionError from `usdm4.data_store.data_store`
# (no `src.` prefix). Because pytest has both `.` and `src/` on sys.path, the
# same file gets registered as two different modules, with distinct class
# objects — so `except DecompositionError` in the engine does NOT catch an
# exception raised from `src.usdm4.data_store.data_store`. Import from the
# path the engine actually uses.
from usdm4.data_store.data_store import DataStoreErrorLocation, DecompositionError


def _decomp_error(msg: str = "bad shape") -> DecompositionError:
    loc = DataStoreErrorLocation("$", "Study", "name")
    return DecompositionError(loc, msg)


# Helper: build an engine without loading real rules from disk by stubbing
# out _load_rules before __init__ runs.


@pytest.fixture
def engine():
    with patch.object(RulesValidationEngine, "_load_rules", lambda self: None):
        e = RulesValidationEngine(root_path="/root", package_name="usdm4.rules.library")
    e.rules = []
    return e


# ---------------------------------------------------------------------------
# __init__ wiring
# ---------------------------------------------------------------------------


def test_init_sets_paths_and_package():
    with patch.object(RulesValidationEngine, "_load_rules", lambda self: None):
        e = RulesValidationEngine(root_path="/r", package_name="usdm4.rules.library")
    assert e.root_path == "/r"
    assert e.library_path.endswith("rules/library")
    assert e.package_name == "usdm4.rules.library"
    assert e.rules == []


# ---------------------------------------------------------------------------
# _data_store — happy path and DecompositionError branch
# ---------------------------------------------------------------------------


def test_data_store_returns_store_and_none(engine):
    fake_store = MagicMock()
    with patch("src.usdm4.rules.engine.DataStore", return_value=fake_store) as ds_cls:
        ds, err = engine._data_store("file.json")
    ds_cls.assert_called_once_with("file.json")
    fake_store.decompose.assert_called_once()
    assert ds is fake_store
    assert err is None


def test_data_store_returns_none_and_exception_on_decomp_failure(engine):
    fake_store = MagicMock()
    fake_store.decompose.side_effect = _decomp_error("bad shape")
    with patch("src.usdm4.rules.engine.DataStore", return_value=fake_store):
        ds, err = engine._data_store("file.json")
    assert ds is None
    assert isinstance(err, DecompositionError)


# ---------------------------------------------------------------------------
# _execute_rules — success, failure, NotImplementedError, generic exception
# ---------------------------------------------------------------------------


def _make_rule_class(rule_id: str, validate_behaviour):
    """Produce a RuleTemplate subclass whose validate() applies `validate_behaviour`."""

    class _Rule(RuleTemplate):
        def __init__(self):
            super().__init__(rule_id, RuleTemplate.ERROR, "t")

        def validate(self, config):
            return validate_behaviour(self, config)

    return _Rule


def test_execute_rules_records_success(engine):
    cls = _make_rule_class("R_OK", lambda self, cfg: True)
    engine.rules = [cls]
    results = engine._execute_rules({"data": None, "ct": None})
    assert results.outcomes["R_OK"].status == RuleStatus.SUCCESS


def test_execute_rules_records_failure_when_validate_returns_false(engine):
    def behaviour(self, cfg):
        self._errors.error("fail")
        return False

    cls = _make_rule_class("R_FAIL", behaviour)
    engine.rules = [cls]
    results = engine._execute_rules({"data": None, "ct": None})
    outcome = results.outcomes["R_FAIL"]
    assert outcome.status == RuleStatus.FAILURE
    assert outcome.error_count == 1


def test_execute_rules_records_not_implemented(engine):
    def behaviour(self, cfg):
        raise NotImplementedError

    cls = _make_rule_class("R_NI", behaviour)
    engine.rules = [cls]
    results = engine._execute_rules({"data": None, "ct": None})
    assert results.outcomes["R_NI"].status == RuleStatus.NOT_IMPLEMENTED


def test_execute_rules_records_exception_with_traceback(engine):
    def behaviour(self, cfg):
        raise RuntimeError("boom")

    cls = _make_rule_class("R_EX", behaviour)
    engine.rules = [cls]
    results = engine._execute_rules({"data": None, "ct": None})
    outcome = results.outcomes["R_EX"]
    assert outcome.status == RuleStatus.EXCEPTION
    assert "boom" in outcome.exception


# ---------------------------------------------------------------------------
# validate_rules — top-level entry point
# ---------------------------------------------------------------------------


def test_validate_rules_happy_path(engine):
    fake_store = MagicMock()
    fake_ct = MagicMock()

    cls = _make_rule_class("R_OK", lambda self, cfg: True)
    engine.rules = [cls]

    with (
        patch("src.usdm4.rules.engine.DataStore", return_value=fake_store),
        patch("src.usdm4.rules.engine.CTLibrary", return_value=fake_ct),
    ):
        results = engine.validate_rules("file.json")

    fake_store.decompose.assert_called_once()
    fake_ct.load.assert_called_once()
    assert results.outcomes["R_OK"].status == RuleStatus.SUCCESS


def test_validate_rules_decomposition_error_records_exception(engine):
    fake_store = MagicMock()
    fake_store.decompose.side_effect = _decomp_error("bad shape")

    with patch("src.usdm4.rules.engine.DataStore", return_value=fake_store):
        results = engine.validate_rules("file.json")

    assert "Decomposition" in results.outcomes
    assert results.outcomes["Decomposition"].status == RuleStatus.EXCEPTION


# ---------------------------------------------------------------------------
# _load_rules — uses a tempdir of fake rule files
# ---------------------------------------------------------------------------


def test_load_rules_picks_up_ddf_rules(tmp_path):
    library = tmp_path / "rules" / "library"
    library.mkdir(parents=True)

    # The engine's _load_rules does `issubclass(obj, RuleTemplate)` where its
    # local RuleTemplate is from `usdm4.rules.rule_template`. The fake rule
    # file must import RuleTemplate from the *same* module path — importing
    # via `src.usdm4.rules.rule_template` yields a different class object and
    # the issubclass check fails silently.
    (library / "rule_ddf00001.py").write_text(
        "from usdm4.rules.rule_template import RuleTemplate\n"
        "class RuleDdf00001(RuleTemplate):\n"
        "    def __init__(self):\n"
        "        super().__init__('DDF00001', RuleTemplate.ERROR, 't')\n"
        "    def validate(self, config):\n"
        "        return True\n"
    )
    # File that doesn't match rule_ddf* pattern should be ignored
    (library / "rule_chk00001.py").write_text("# noop\n")

    with patch.object(RulesValidationEngine, "_load_rules", lambda self: None):
        e = RulesValidationEngine(str(tmp_path), "usdm4.rules.library")

    # Swap paths over to our tempdir and call the real _load_rules
    e.root_path = str(tmp_path)
    e.library_path = str(library)
    e.package_name = "usdm4.rules.library"
    e.rules = []
    RulesValidationEngine._load_rules(e)

    assert any(r.__name__ == "RuleDdf00001" for r in e.rules)
    # chk file not picked up
    assert not any("chk" in r.__name__.lower() for r in e.rules)


def test_load_rules_skips_files_with_syntax_error(tmp_path):
    library = tmp_path / "rules" / "library"
    library.mkdir(parents=True)
    (library / "rule_ddf00002.py").write_text("def broken(:\n")  # syntax error

    with patch.object(RulesValidationEngine, "_load_rules", lambda self: None):
        e = RulesValidationEngine(str(tmp_path), "usdm4.rules.library")

    e.root_path = str(tmp_path)
    e.library_path = str(library)
    e.package_name = "usdm4.rules.library"
    e.rules = []
    RulesValidationEngine._load_rules(e)

    # Engine does not crash; rules list stays empty.
    assert e.rules == []


def test_load_rules_handles_spec_none(tmp_path):
    """Cover the 'spec is None or spec.loader is None' continue branch."""
    library = tmp_path / "rules" / "library"
    library.mkdir(parents=True)
    # Create an apparently-valid file that we'll force spec_from_file_location
    # to reject.
    (library / "rule_ddf00003.py").write_text(
        "from src.usdm4.rules.rule_template import RuleTemplate\n"
        "class RuleDdf00003(RuleTemplate):\n"
        "    def __init__(self):\n"
        "        super().__init__('DDF00003', RuleTemplate.ERROR, 't')\n"
        "    def validate(self, config):\n"
        "        return True\n"
    )

    with patch.object(RulesValidationEngine, "_load_rules", lambda self: None):
        e = RulesValidationEngine(str(tmp_path), "usdm4.rules.library")

    e.root_path = str(tmp_path)
    e.library_path = str(library)
    e.package_name = "usdm4.rules.library"
    e.rules = []

    with patch(
        "src.usdm4.rules.engine.importlib.util.spec_from_file_location",
        return_value=None,
    ):
        RulesValidationEngine._load_rules(e)

    assert e.rules == []
