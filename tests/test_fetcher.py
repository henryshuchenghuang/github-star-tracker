import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fetcher import GitHubFetcher


def test_fetcher_initialization():
    config = {"tracking": {"min_stars": 100, "languages": ["all"], "top_n_candidates": 50}}
    fetcher = GitHubFetcher("dummy_token", config)
    assert fetcher.config == config
