import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "config.example.yaml")


def load_config(path=None):
    path = path or CONFIG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config not found at {path}. Copy config.example.yaml to config.yaml and fill in values."
        )
    with open(path, "r") as f:
        return yaml.safe_load(f)
