"""Web 面板 JSON 导出

为静态 Web 面板提供数据导出功能：
- build_panel_data: 构建带统计摘要的面板数据结构
- export_latest:   写入 latest.json（最新快照）
- export_archive:   写入 archive/{date}.json（历史归档）
"""

import json
import os
from datetime import datetime, timezone


def _compute_distribution(candidates, key, is_list=False):
    dist = {}
    for r in candidates:
        values = r.get(key, []) if is_list else [r.get(key, "unknown")]
        for v in values:
            if v:
                dist[v] = dist.get(v, 0) + 1
    return dict(sorted(dist.items(), key=lambda x: -x[1]))


def build_panel_data(candidates, date_str):
    """构建面板数据，包含候选列表和统计摘要。

    Args:
        candidates: 候选项目列表（每个元素为 dict）。
        date_str:   日期字符串，如 "2026-06-10"。

    Returns:
        包含 date、generated_at、candidates、stats 的 dict。
    """
    top_day = sorted(candidates, key=lambda r: (r.get("star_delta_1d", 0), r.get("stars", 0)), reverse=True)
    top_week = sorted(candidates, key=lambda r: (r.get("star_delta_7d", 0), r.get("stars", 0)), reverse=True)
    new_stars = sorted(
        [r for r in candidates if "🌱新星" in r.get("labels", [])],
        key=lambda r: r.get("score", 0), reverse=True)
    top_stars = sorted(candidates, key=lambda r: r.get("stars", 0), reverse=True)

    stats = {
        "top_day": top_day,
        "top_week": top_week,
        "new_stars": new_stars,
        "top_stars": top_stars,
        "total_candidates": len(candidates),
        "language_distribution": _compute_distribution(candidates, "language"),
        "topic_distribution": _compute_distribution(candidates, "topics", is_list=True),
        "label_statistics": _compute_distribution(candidates, "labels", is_list=True),
    }

    return {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": candidates,
        "stats": stats,
    }


def export_latest(panel_data, web_data_dir):
    """将面板数据写入 {web_data_dir}/latest.json。

    Args:
        panel_data:   build_panel_data 返回的 dict。
        web_data_dir: Web 数据目录，如 "web/data"。
    """
    os.makedirs(web_data_dir, exist_ok=True)
    path = os.path.join(web_data_dir, "latest.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(panel_data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def export_archive(panel_data, web_data_dir):
    """将面板数据写入 {web_data_dir}/archive/{date}.json。

    日期格式要求 YYYY-MM-DD，拒绝含路径分隔符的输入。

    Args:
        panel_data:   build_panel_data 返回的 dict。
        web_data_dir: Web 数据目录，如 "web/data"。
    """
    date_str = panel_data["date"]
    _validate_date_str(date_str)
    archive_dir = os.path.join(web_data_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    path = os.path.join(archive_dir, f"{date_str}.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(panel_data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _validate_date_str(s):
    if any(sep in s for sep in ("/", "\\", "..")):
        raise ValueError(f"Invalid date format: {s}")


def update_archive_index(web_data_dir):
    """扫描 archive 目录，更新 archive/index.json 索引文件。

    GitHub Pages 不支持目录列表，前端需要这个索引来知道有哪些历史日期可用。
    """
    import glob

    archive_dir = os.path.join(web_data_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)

    dates = []
    pattern = os.path.join(archive_dir, "*.json")
    for path in glob.glob(pattern):
        basename = os.path.basename(path)
        if basename == "index.json":
            continue
        date_str = basename.replace(".json", "")
        dates.append(date_str)

    dates.sort(reverse=True)

    index_path = os.path.join(archive_dir, "index.json")
    tmp = index_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"dates": dates, "count": len(dates)}, f)
    os.replace(tmp, index_path)
