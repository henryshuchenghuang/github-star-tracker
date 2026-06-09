import json
import os


def append_snapshot(path, snapshot):
    """Append a JSON snapshot as a new line in a JSONL file.

    Creates parent directories if they do not exist.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def read_snapshots(path):
    """Read all snapshot lines from a JSONL file.

    Returns an empty list if the file does not exist.
    """
    if not os.path.exists(path):
        return []
    results = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def save_json(path, data):
    """Write data as formatted JSON to path.

    Creates parent directories if they do not exist.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path):
    """Read and parse a JSON file.

    Returns None if the file does not exist.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
