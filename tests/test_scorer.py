import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scorer import (
    score_growth,
    score_novelty,
    score_community,
    score_authority,
    score_quality,
    compute_composite,
)


def test_score_growth():
    repo = {"stars": 1000, "star_delta_1d": 100, "star_delta_7d": 500}
    prev = {"stars": 500, "star_delta_1d": 50, "star_delta_7d": 200}
    s = score_growth(repo, prev)
    assert 0 <= s <= 100


def test_score_novelty_new():
    repo = {"created_at": "2026-05-15T00:00:00Z", "stars": 600}
    s = score_novelty(repo, set())
    assert s > 50  # new + high stars = high novelty


def test_score_novelty_old():
    repo = {"created_at": "2020-01-01T00:00:00Z", "stars": 100}
    s = score_novelty(repo, set())
    assert s < 30  # old + low stars = low novelty


def test_score_community():
    repo = {"contributors_30d": 20, "issue_response_h": 2.0, "pr_merge_rate": 0.9}
    s = score_community(repo)
    assert 0 <= s <= 100


def test_score_authority():
    config = {"tracking": {"org_whitelist": ["google", "meta"]}}
    org_repo = {"full_name": "google/awesome", "owner_type": "org"}
    individual_repo = {"full_name": "someone/tool", "owner_type": "individual"}
    assert score_authority(org_repo, config) > score_authority(individual_repo, config)


def test_score_quality():
    good = {"readme_score": 85, "license": "MIT"}
    bad = {"readme_score": 10, "license": ""}
    assert score_quality(good) > score_quality(bad)


def test_composite():
    dimensions = {"growth": 80, "novelty": 70, "community": 60, "authority": 50, "quality": 40}
    score = compute_composite(dimensions)
    expected = 80 * 0.35 + 70 * 0.20 + 60 * 0.25 + 50 * 0.10 + 40 * 0.10
    assert abs(score - expected) < 0.01
