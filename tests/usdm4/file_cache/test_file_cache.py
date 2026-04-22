"""Direct tests for FileCache (yaml-backed on-disk cache).

Uses ``tmp_path`` so no real user directories are touched.
"""

import os

import pytest

from src.usdm4.file_cache.file_cache import FileCache


def test_exists_returns_false_when_missing(tmp_path):
    fc = FileCache(str(tmp_path), "no-such.yml")
    assert fc.exists() is False


def test_save_then_read_roundtrip(tmp_path):
    fc = FileCache(str(tmp_path), "cache.yml")
    data = {"a": 1, "b": [1, 2, 3]}

    fc.save(data)
    assert fc.exists() is True
    assert fc.read() == data


def test_save_does_not_overwrite_existing_file(tmp_path):
    """save() is a 'write if missing' operation — existing content is preserved."""
    fc = FileCache(str(tmp_path), "cache.yml")
    fc.save({"initial": 1})
    fc.save({"overwrite": 2})  # no-op because file exists
    assert fc.read() == {"initial": 1}


def test_save_raises_on_disk_error(tmp_path, monkeypatch):
    """If yaml.dump blows up the cache wraps in its own Exception."""
    fc = FileCache(str(tmp_path), "cache.yml")

    def bomb(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr("src.usdm4.file_cache.file_cache.yaml.dump", bomb)

    with pytest.raises(Exception) as ex:
        fc.save({"x": 1})
    assert "Failed to save file" in str(ex.value)


def test_read_raises_when_missing(tmp_path):
    fc = FileCache(str(tmp_path), "missing.yml")
    with pytest.raises(Exception) as ex:
        fc.read()
    assert "does not exist" in str(ex.value)


def test_read_raises_on_parse_error(tmp_path, monkeypatch):
    fc = FileCache(str(tmp_path), "bad.yml")
    fc.save({"x": 1})

    def bomb(*args, **kwargs):
        raise RuntimeError("bad yaml")

    monkeypatch.setattr("src.usdm4.file_cache.file_cache.yaml.safe_load", bomb)

    with pytest.raises(Exception) as ex:
        fc.read()
    assert "Failed to read file" in str(ex.value)


def test_delete_removes_file(tmp_path):
    fc = FileCache(str(tmp_path), "cache.yml")
    fc.save({"x": 1})
    assert fc.exists()
    fc.delete()
    assert not fc.exists()


def test_delete_silently_ignores_missing_file(tmp_path):
    fc = FileCache(str(tmp_path), "never-there.yml")
    # Should not raise
    fc.delete()


def test_full_filepath_joins_components(tmp_path):
    fc = FileCache(str(tmp_path), "x.yml")
    assert fc._full_filepath() == os.path.join(str(tmp_path), "x.yml")
