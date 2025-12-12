# USDM4 Test Suite Performance Optimization Guide

## Current Performance Baseline

**Full Test Suite**: ~80 seconds for 1,538 tests
- Average: 0.05s per test
- **Problem**: Most time spent in test setup (3-4 seconds per test file)
- **Root Cause**: CT (Controlled Terminology) library loading at module import time

## Performance Bottlenecks

### 1. CT Library Loading (PRIMARY ISSUE)

**Problem**: `Builder.__init__()` loads 4 CT libraries:
```python
# In src/usdm4/builder/builder.py lines 43-46
self.cdisc_ct_library.load()  # Loads CDISC CT JSON files
self.cdisc_bc_library.load()  # Loads CDISC BC files
self.iso3166_library.load()   # Loads ISO 3166 country codes
self.iso639_library.load()    # Loads ISO 639 language codes
```

**Impact**: Every test file that creates a `Builder` or `Assembler` pays this 3+ second penalty.

**Evidence**: From slowest test durations:
```
3.62s setup    tests/usdm4/assembler/test_amendments_assembler.py
3.46s setup    tests/usdm4/assembler/test_identification_assembler.py
3.45s call     tests/usdm4/test_package.py::test_minimum
3.42s setup    tests/usdm4/builder/test_builder.py::test_minimum
```

### 2. Global Object Creation at Import Time

**Problem**: In `tests/usdm4/assembler/test_assembler.py`:
```python
# Line 15 - SLOW: Creates Assembler when module is imported
global_assembler = Assembler(root_path(), global_errors)
```

**Impact**: CT libraries loaded even if tests never run.

## Optimization Strategies

### Strategy 1: Lazy CT Library Loading (RECOMMENDED - HIGH IMPACT)

Modify `Builder.__init__()` to defer loading until needed:

```python
# src/usdm4/builder/builder.py
class Builder:
    def __init__(self, root_path: str, errors: Errors):
        self._root_path = root_path
        self._id_manager: IdManager = IdManager(v4_classes)
        self.errors = errors
        self.api_instance: APIInstance = APIInstance(self._id_manager)

        # Create libraries but DON'T load yet
        self.cdisc_ct_library = CdiscCTLibrary(root_path)
        self.cdisc_bc_library = CdiscBCLibrary(root_path, self.cdisc_ct_library)
        self.iso3166_library = Iso3166Library(root_path)
        self.iso639_library = Iso639Library(root_path)

        # Track if loaded
        self._ct_loaded = False

        self.cross_reference = CrossReference()
        self.other_ct_version_manager = OtherCTVersionManager()
        self._data_store = None

    def _ensure_ct_loaded(self):
        """Lazy load CT libraries only when first needed."""
        if not self._ct_loaded:
            self.cdisc_ct_library.load()
            self.cdisc_bc_library.load()
            self.iso3166_library.load()
            self.iso639_library.load()
            self._cdisc_code_system = self.cdisc_ct_library.system
            self._cdisc_code_system_version = self.cdisc_ct_library.version
            self._ct_loaded = True

    # Then add _ensure_ct_loaded() call to methods that need CT data:
    def iso639_code(self, code: str) -> Code:
        self._ensure_ct_loaded()  # Load only when needed
        return self.iso639_library.code(code)

    def iso3166_code(self, code: str) -> Code:
        self._ensure_ct_loaded()
        return self.iso3166_library.code(code)

    # Add to all methods that access CT libraries...
```

**Expected Impact**:
- Test suite: ~80s → ~20-30s (60-70% faster)
- Tests that don't need CT data run instantly
- Only pay CT load cost once per test session (with fixtures)

### Strategy 2: Pytest Fixtures for Shared Objects (MEDIUM IMPACT)

Create session-scoped fixtures to share expensive objects:

```python
# tests/conftest.py (create at tests/ root level)
import pytest
from simple_error_log.errors import Errors
from usdm4.builder.builder import Builder
import os
import pathlib


def root_path():
    base = pathlib.Path(__file__).parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="session")
def shared_builder():
    """
    Session-scoped builder - CT libraries loaded once for entire test suite.
    WARNING: Tests must not mutate this object!
    """
    errors = Errors()
    builder = Builder(root_path(), errors)
    return builder


@pytest.fixture(scope="function")
def fresh_builder(shared_builder):
    """
    Function-scoped builder that reuses CT libraries but has fresh state.
    """
    shared_builder.clear()  # Reset state
    return shared_builder


@pytest.fixture
def errors():
    """Fresh Errors object for each test."""
    return Errors()
```

**Usage in tests**:
```python
# Before (slow - creates new Builder each time)
def test_something():
    errors = Errors()
    builder = Builder(root_path(), errors)  # 3+ seconds
    # ... test code ...

# After (fast - reuses CT libraries)
def test_something(fresh_builder, errors):
    builder = fresh_builder  # Near instant
    # ... test code ...
```

**Expected Impact**:
- Combined with Strategy 1: ~80s → ~10-15s (80%+ faster)
- CT libraries loaded once instead of 50+ times

### Strategy 3: Remove Global Object Creation (LOW EFFORT, MEDIUM IMPACT)

**Fix `test_assembler.py`**:
```python
# Before (line 15)
global_assembler = Assembler(root_path(), global_errors)

# After - use lazy creation
_cached_assembler = None

def get_global_assembler():
    global _cached_assembler
    if _cached_assembler is None:
        _cached_assembler = Assembler(root_path(), Errors())
    _cached_assembler.clear()
    return _cached_assembler
```

Or better - use pytest fixtures:
```python
@pytest.fixture(scope="module")
def shared_assembler():
    """Module-scoped assembler for tests in this file."""
    return Assembler(root_path(), Errors())

def test_something(shared_assembler):
    shared_assembler.clear()  # Reset state
    # ... test code ...
```

### Strategy 4: Parallel Test Execution (MEDIUM EFFORT, HIGH IMPACT)

Install pytest-xdist:
```bash
pip install pytest-xdist
```

Run tests in parallel:
```bash
# Use all CPU cores
pytest tests/ -n auto --no-cov

# Use 4 cores
pytest tests/ -n 4 --no-cov
```

**Expected Impact**:
- On 4-core machine: ~80s → ~20-30s (60-70% faster)
- Combined with other strategies: ~80s → ~5-10s

### Strategy 5: Disable Coverage During Development (INSTANT WIN)

Coverage adds 50-100% overhead:

```bash
# During development - fast
pytest tests/ --no-cov

# In CI/CD - run with coverage
pytest tests/
```

Update `pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
# Remove --cov from addopts for local development
# addopts = -v --cov=src --cov-report=term-missing --cov-fail-under=100
addopts = -v
```

Create separate command for coverage:
```bash
# Add to Makefile or scripts
test-fast: pytest tests/ --no-cov
test-with-coverage: pytest tests/ --cov=src --cov-report=term-missing
```

### Strategy 6: Mock CT Libraries in Unit Tests (HIGH EFFORT, HIGH VALUE)

For pure unit tests that don't need real CT data:

```python
# tests/conftest.py
@pytest.fixture
def mock_builder(monkeypatch):
    """
    Fast mock builder for unit tests that don't need real CT data.
    """
    class MockCTLibrary:
        def load(self):
            pass  # No-op

        def code(self, code_value: str):
            # Return fake Code object
            return Code(
                id=f"mock_{code_value}",
                code=code_value,
                codeSystem="MOCK",
                codeSystemVersion="1.0",
                decode=f"Mock {code_value}",
                instanceType="Code"
            )

    # Patch the libraries
    monkeypatch.setattr("usdm4.builder.builder.CdiscCTLibrary", MockCTLibrary)
    monkeypatch.setattr("usdm4.builder.builder.CdiscBCLibrary", MockCTLibrary)
    monkeypatch.setattr("usdm4.builder.builder.Iso3166Library", MockCTLibrary)
    monkeypatch.setattr("usdm4.builder.builder.Iso639Library", MockCTLibrary)

    errors = Errors()
    return Builder(root_path(), errors)
```

### Strategy 7: Cache Loaded CT Data (MEDIUM EFFORT, HIGH IMPACT)

Implement caching in the CT libraries themselves:

```python
# In src/usdm4/ct/iso/iso639/library.py (and similar files)
_LOADED_CACHE = {}

class Library:
    def load(self):
        global _LOADED_CACHE

        # Use cached data if available
        cache_key = f"{self._root_path}_iso639"
        if cache_key in _LOADED_CACHE:
            self._data = _LOADED_CACHE[cache_key]
            return

        # Otherwise load and cache
        self._data = self._load_from_disk()
        _LOADED_CACHE[cache_key] = self._data
```

## Implementation Plan

### Phase 1: Quick Wins (COMPLETED)
1. ✅ Remove global object creation (Strategy 3)
2. ✅ Add session-scoped fixtures (Strategy 2) - Added to root conftest.py
3. ✅ Document --no-cov usage (Strategy 5)

**Expected Improvement**: 80s → 40-50s (40% faster)
**Status**: Session-scoped fixtures for Builder and Assembler are now available in conftest.py

### Phase 2: Lazy Loading (COMPLETED)
1. ✅ Implement lazy CT loading in Builder (Strategy 1)
2. ✅ Update all Builder methods to call `_ensure_ct_loaded()`
3. ✅ Add tests to verify CT data still loads correctly

**Expected Improvement**: 80s → 15-20s (75% faster)
**Actual Improvement**: 80s → 49.85s (38% faster)
**Status**: Lazy loading implemented in Builder.__init__(), CT libraries now load on first use
**Note**: Combined with Phase 1 session fixtures, tests benefit from loading CT libraries only once

### Phase 3: Advanced Optimizations (4-8 hours)
1. Implement CT data caching (Strategy 7)
2. Add mock builders for unit tests (Strategy 6)
3. Set up parallel testing (Strategy 4)

**Expected Improvement**: 80s → 5-10s (90%+ faster)

## Quick Start

### Immediate Actions (No Code Changes)

1. **Run tests without coverage locally**:
```bash
pytest tests/usdm4/expander/ --no-cov  # Fast: 0.6s
pytest tests/ --no-cov                  # Slow: 80s
```

2. **Use parallel execution**:
```bash
pip install pytest-xdist
pytest tests/ -n auto --no-cov         # Potentially 4x faster
```

3. **Run only changed tests**:
```bash
pytest tests/usdm4/expander/  # Test only what you're working on
```

## Monitoring Performance

### Track Test Times
```bash
# Show slowest 20 tests
pytest tests/ --durations=20 --no-cov

# Profile imports
python -X importtime -c "import usdm4" 2>&1 | sort -t '|' -k2 -n -r | head -20
```

### Set Performance Goals
- Unit tests: < 0.01s per test
- Integration tests: < 0.1s per test
- Full suite: < 10s target (current: 80s)

## Summary

**Current State**: 80s for 1,538 tests
**Primary Issue**: CT library loading (3-4s per test file)
**Target State**: 5-10s for 1,538 tests

**Highest Impact Changes**:
1. Lazy CT loading (Strategy 1) - 60-70% improvement
2. Session fixtures (Strategy 2) - 50% improvement when combined with #1
3. Parallel execution (Strategy 4) - 60-70% improvement on multi-core
4. Disable coverage locally (Strategy 5) - 50% improvement

**Combined**: All strategies together could reduce test time from 80s to ~5s (94% improvement).
