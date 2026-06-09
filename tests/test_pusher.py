import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pusher import push_all


def test_push_all_disabled():
    config = {
        "push": {
            "email": {"enabled": False},
            "wechat": {"enabled": False},
            "feishu": {"enabled": False},
        }
    }
    results = push_all(config, "test", "test body")
    assert all(not v["success"] for v in results.values())
