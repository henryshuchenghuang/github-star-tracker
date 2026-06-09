import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.store import append_snapshot, read_snapshots, save_json, load_json


def test_append_and_read_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "snapshots.jsonl")
        snap = {"repo": "test/repo", "time": "2026-06-10T14:00:00Z", "stars": 100}
        append_snapshot(path, snap)
        append_snapshot(path, snap)
        results = read_snapshots(path)
        assert len(results) == 2
        assert results[0]["stars"] == 100


def test_save_and_load_json():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.json")
        data = {"key": "value"}
        save_json(path, data)
        loaded = load_json(path)
        assert loaded == data


def test_read_nonexistent_file_returns_empty():
    assert read_snapshots("/nonexistent/path.jsonl") == []


def test_load_nonexistent_json_returns_none():
    assert load_json("/nonexistent/path.json") is None
