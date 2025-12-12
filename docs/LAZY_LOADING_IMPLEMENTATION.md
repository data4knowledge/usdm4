# Lazy CT Library Loading Implementation

## Overview
Implemented lazy loading of Controlled Terminology (CT) libraries in the Builder class to significantly improve test performance.

## Performance Impact
- **Before**: ~80 seconds for 1,539 tests
- **After**: ~50 seconds for 1,539 tests
- **Improvement**: 38% faster (30 seconds saved)

## Changes Made

### 1. Modified Builder.__init__() ([src/usdm4/builder/builder.py](src/usdm4/builder/builder.py:34-49))
**Before:**
```python
def __init__(self, root_path: str, errors: Errors):
    # ... other initialization ...
    self.cdisc_ct_library = CdiscCTLibrary(root_path)
    self.cdisc_bc_library = CdiscBCLibrary(root_path, self.cdisc_ct_library)
    self.iso3166_library = Iso3166Library(root_path)
    self.iso639_library = Iso639Library(root_path)
    # ... more setup ...
    self.cdisc_ct_library.load()  # 3+ second penalty!
    self.cdisc_bc_library.load()
    self.iso3166_library.load()
    self.iso639_library.load()
    self._cdisc_code_system = self.cdisc_ct_library.system
    self._cdisc_code_system_version = self.cdisc_ct_library.version
```

**After:**
```python
def __init__(self, root_path: str, errors: Errors):
    # ... other initialization ...
    self.cdisc_ct_library = CdiscCTLibrary(root_path)
    self.cdisc_bc_library = CdiscBCLibrary(root_path, self.cdisc_ct_library)
    self.iso3166_library = Iso3166Library(root_path)
    self.iso639_library = Iso639Library(root_path)
    # ... more setup ...
    self._data_store = None

    # Lazy loading: Track if CT libraries have been loaded
    self._ct_loaded = False
    self._cdisc_code_system = None
    self._cdisc_code_system_version = None
```

### 2. Added _ensure_ct_loaded() Method ([src/usdm4/builder/builder.py](src/usdm4/builder/builder.py:51-60))
```python
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
```

### 3. Updated All Methods That Access CT Libraries
Added `self._ensure_ct_loaded()` call to the following methods:
- `minimum()` - line 109
- `klass_and_attribute()` - line 211
- `klass_and_attribute_value()` - line 215
- `cdisc_code()` - line 234
- `cdisc_unit_code()` - line 251
- `bc()` - line 272
- `iso3166_code_or_decode()` - line 283
- `iso3166_code()` - line 299
- `iso639_code_or_decode()` - line 315
- `iso639_code()` - line 332
- `iso3166_region_code()` - line 348
- `sponsor()` - line 372

## How It Works

1. **Initialization**: When a Builder is created, CT library objects are instantiated but NOT loaded
2. **First Use**: When any method that needs CT data is called, `_ensure_ct_loaded()` is triggered
3. **One-time Load**: The `_ct_loaded` flag ensures libraries are loaded exactly once
4. **Session Sharing**: Combined with pytest session-scoped fixtures in [conftest.py](conftest.py), CT libraries are loaded once per test session

## Benefits

### For Tests
- **Tests without CT usage**: Run instantly (no 3-second penalty)
- **Tests with CT usage**: Load libraries only once per session
- **Faster development**: Tests run 38% faster during development

### For Production Code
- **Lower memory footprint**: Applications that don't use CT features don't load the data
- **Faster startup**: Builder instantiation is near-instant
- **Same functionality**: All existing code continues to work unchanged

## Verification

All 1,539 tests pass successfully:
```bash
pytest tests/ --no-cov -q
# Result: 1539 passed, 2 skipped, 4 warnings in 49.85s
```

## Future Optimizations

Additional strategies documented in [tests/PERFORMANCE_OPTIMIZATION_GUIDE.md](tests/PERFORMANCE_OPTIMIZATION_GUIDE.md):
- Parallel test execution with pytest-xdist (estimated 60-70% faster)
- CT data caching (cache loaded data globally)
- Mock builders for pure unit tests
- Disable coverage during local development

## Backward Compatibility

✅ **Fully backward compatible** - No changes required to existing code. All tests pass without modification.
