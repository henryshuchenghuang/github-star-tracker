import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.reporter import generate_daily_report, generate_weekly_report, generate_one_liner


def test_generate_one_liner():
    r = {"repo": "test/proj", "star_delta_7d": 500, "description": "A test project"}
    result = generate_one_liner(r)
    assert "test/proj" in result
    assert "+500" in result


def test_generate_one_liner_negative_delta():
    r = {"repo": "a/b", "star_delta_7d": -10, "description": "declining"}
    result = generate_one_liner(r)
    assert "+-" not in result
    assert "-10" in result


def test_generate_one_liner_fallback_name():
    r = {"full_name": "org/repo", "star_delta_7d": 10, "description": "test"}
    result = generate_one_liner(r)
    assert "org/repo" in result


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


def test_generate_daily_report_missing_repo_key():
    """candidate 缺少 repo 键时使用 full_name 回退，不应抛出 KeyError"""
    candidates = [
        {
            "full_name": "org/proj", "stars": 500,
            "star_delta_1d": 20, "star_delta_7d": 100, "score": 70,
            "labels": [], "one_liner": "no repo key"
        }
    ]
    md = generate_daily_report(candidates, "2026-06-10")
    assert "org/proj" in md


def test_generate_weekly_report():
    candidates = [
        {
            "rank": 1, "repo": "x/y", "stars": 2000,
            "star_delta_1d": 80, "star_delta_7d": 600, "score": 95,
            "labels": ["🔥爆发中", "🌱新星"], "one_liner": "hot new project"
        }
    ]
    md = generate_weekly_report(candidates, "2026-W24", "> AI 赛道火热")
    assert "GitHub 开源项目周报" in md
    assert "2026-W24" in md
    assert "本周赛道观察" in md
    assert "AI 赛道火热" in md
    assert "本周数据汇总" in md
    assert "x/y" in md
    assert "今日增速" in md


def test_generate_weekly_report_empty():
    md = generate_weekly_report([], "2026-W24")
    assert "暂无数据" in md
