import os
import json
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.web_exporter import export_latest, export_archive, build_panel_data


def test_build_panel_data():
    candidates = [
        {"rank": 1, "repo": "a/b", "stars": 1000, "star_delta_1d": 50,
         "star_delta_7d": 300, "score": 90, "labels": ["🔥爆发中"],
         "one_liner": "test"}
    ]
    data = build_panel_data(candidates, "2026-06-10")
    assert data["date"] == "2026-06-10"
    assert len(data["candidates"]) == 1
    assert "generated_at" in data
    assert "stats" in data
    assert data["stats"]["total_candidates"] == 1


def test_build_panel_data_sections():
    candidates = [
        {"rank": 1, "repo": "fast/daily", "stars": 1000, "star_delta_1d": 80,
         "star_delta_7d": 200, "score": 60, "labels": [], "one_liner": "fast daily"},
        {"rank": 2, "repo": "fast/weekly", "stars": 2000, "star_delta_1d": 10,
         "star_delta_7d": 900, "score": 70, "labels": [], "one_liner": "fast weekly"},
        {"rank": 3, "repo": "new/star", "stars": 500, "star_delta_1d": 20,
         "star_delta_7d": 100, "score": 50, "labels": ["🌱新星"], "one_liner": "new star"},
    ]
    data = build_panel_data(candidates, "2026-06-10")
    assert data["stats"]["top_day"][0]["repo"] == "fast/daily"
    assert data["stats"]["top_week"][0]["repo"] == "fast/weekly"
    assert len(data["stats"]["new_stars"]) == 1
    assert data["stats"]["new_stars"][0]["repo"] == "new/star"


def test_build_panel_data_empty():
    data = build_panel_data([], "2026-06-10")
    assert data["date"] == "2026-06-10"
    assert data["candidates"] == []
    assert data["stats"]["total_candidates"] == 0
    assert data["stats"]["top_day"] == []
    assert data["stats"]["top_week"] == []
    assert data["stats"]["new_stars"] == []


def test_export_latest():
    with tempfile.TemporaryDirectory() as tmp:
        web_dir = os.path.join(tmp, "web/data")
        data = {"date": "2026-06-10", "candidates": []}
        export_latest(data, web_dir)
        assert os.path.exists(os.path.join(web_dir, "latest.json"))
        with open(os.path.join(web_dir, "latest.json")) as f:
            loaded = json.load(f)
        assert loaded["date"] == "2026-06-10"


def test_export_archive():
    with tempfile.TemporaryDirectory() as tmp:
        web_dir = os.path.join(tmp, "web/data")
        data = {"date": "2026-06-10", "candidates": []}
        export_archive(data, web_dir)
        assert os.path.exists(os.path.join(web_dir, "archive/2026-06-10.json"))
        with open(os.path.join(web_dir, "archive/2026-06-10.json")) as f:
            loaded = json.load(f)
        assert loaded["date"] == "2026-06-10"
