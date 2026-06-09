import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.reporter import generate_daily_report, generate_weekly_report, generate_one_liner


def test_generate_one_liner():
    r = {"repo": "test/proj", "star_delta_7d": 500, "description": "A test project"}
    result = generate_one_liner(r)
    assert "test/proj" in result


def test_generate_daily_report():
    candidates = [
        {
            "rank": 1, "repo": "a/b", "stars": 1000,
            "star_delta_1d": 50, "star_delta_7d": 300, "score": 90,
            "labels": ["🔥爆发中"], "one_liner": "test project"
        }
    ]
    md = generate_daily_report(candidates, "2026-06-10")
    assert "# GitHub 开源项目日报" in md
    assert "2026-06-10" in md
    assert "a/b" in md
    assert "今日增速" in md
    assert "本周爆发" in md
    assert "潜力新星" in md


def test_generate_daily_report_empty():
    md = generate_daily_report([], "2026-06-10")
    assert "暂无数据" in md
