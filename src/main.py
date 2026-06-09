#!/usr/bin/env python3
"""GitHub Star Tracker — CLI 入口脚本

Usage:
    python src/main.py --fetch          # 阶段一：抓取 + 评分
    python src/main.py --report         # 阶段二：生成日报（不推送）
    python src/main.py --push           # 阶段二：生成日报 + 推送
    python src/main.py --weekly         # 阶段二：生成周报 + 推送
    python src/main.py --config path    # 指定配置文件路径
"""

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import load_config
from src.fetcher import GitHubFetcher
from src.scorer import (
    score_growth,
    score_novelty,
    score_community,
    score_authority,
    score_quality,
    compute_composite,
    compute_readme_score,
    compute_labels,
)
from src.store import append_snapshot, read_snapshots, save_json, load_json
from src.reporter import generate_daily_report, generate_weekly_report, generate_one_liner
from src.pusher import push_all
from src.web_exporter import build_panel_data, export_latest, export_archive, update_archive_index

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOTS_PATH = os.path.join(DATA_DIR, "snapshots.jsonl")
PROFILES_PATH = os.path.join(DATA_DIR, "profiles.json")
CANDIDATES_PATH = os.path.join(DATA_DIR, "candidates.json")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
WEB_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")


def _find_snapshot_n_days_ago(snapshots, full_name, days=7):
    """在历史快照中查找最接近 N 天前的一条快照。

    Args:
        snapshots: 所有历史快照列表
        full_name: 仓库全名，如 "owner/repo"
        days: 目标天数，默认 7

    Returns:
        最接近目标日期的快照 dict，未找到时返回 None
    """
    from datetime import timedelta

    target = datetime.now(timezone.utc) - timedelta(days=days)
    best = None
    best_diff = None
    for s in snapshots:
        if s.get("repo") == full_name:
            try:
                st = datetime.fromisoformat(s["time"])
                diff = abs((st - target).total_seconds())
                if best_diff is None or diff < best_diff:
                    best = s
                    best_diff = diff
            except (ValueError, KeyError):
                continue
    return best


def do_fetch(config):
    """阶段一：抓取仓库数据并评分"""
    print("=" * 50)
    print("🚀 GitHub Star Tracker — 阶段一：抓取 + 评分")
    print("=" * 50)

    token = config.get("github_token", "")
    if not token or token == "ghp_xxx":
        print("❌ 错误：请先配置 github_token")
        return

    fetcher = GitHubFetcher(token, config)
    profiles = load_json(PROFILES_PATH) or {}
    print(f"📂 已加载 {len(profiles)} 个已收录仓库")

    prev_snapshots = read_snapshots(SNAPSHOTS_PATH)
    print(f"📊 已有 {len(prev_snapshots)} 条历史快照")

    print("🔍 搜索最近 7 天新仓库...")
    new_repos = fetcher.search_new_repos(since_days=7)
    print(f"   找到 {len(new_repos)} 个新仓库")

    print("🔍 搜索全 GitHub 历史最高星数仓库...")
    try:
        all_time_repos = fetcher.search_all_time_top_repos(min_stars=500)
        print(f"   找到 {len(all_time_repos)} 个历史高星仓库")
    except Exception as e:
        print(f"   ⚠️ 历史搜索失败: {e}，将仅使用新仓库")
        all_time_repos = []

    # 合并去重（优先保留 new_repos 中的版本，因为它们数据更新）
    seen = set()
    repos = []
    for r in new_repos:
        seen.add(r.full_name.lower())
        repos.append(r)
    for r in all_time_repos:
        if r.full_name.lower() not in seen:
            seen.add(r.full_name.lower())
            repos.append(r)

    print(f"✅ 合并后共 {len(repos)} 个候选仓库")

    all_topics = set()
    for p in profiles.values():
        all_topics.update(p.get("topics", []))
    print(f"🏷️  合并 {len(all_topics)} 个 Topic")

    candidates = []
    tracked = profiles.copy()

    for i, repo in enumerate(repos, 1):
        full_name = repo.full_name
        try:
            print(f"  [{i}/{len(repos)}] {full_name} ", end="", flush=True)

            details = fetcher.get_repo_details(full_name)
            contributors_30d = fetcher.get_contributors_count(full_name)
            readme_score = compute_readme_score(details["readme_text"])

            # 更新 profiles
            tracked[full_name] = {
                "full_name": full_name,
                "stars": details["stars"],
                "forks": details["forks"],
                "language": details["language"],
                "description": details["description"],
                "topics": details["topics"],
                "created_at": details["created_at"],
                "license": details["license"],
                "owner_type": details["owner_type"],
                "last_fetched": datetime.now(timezone.utc).isoformat(),
                "contributors_30d": contributors_30d,
                "open_issues": details["open_issues"],
            }

            # 找上一次快照（倒序搜索最近一条）
            prev = None
            for s in reversed(prev_snapshots):
                if s.get("repo") == full_name:
                    prev = s
                    break

            prev_7d = _find_snapshot_n_days_ago(prev_snapshots, full_name, days=7)

            prev_stars = prev["stars"] if prev else repo.stargazers_count
            star_delta_1d = repo.stargazers_count - prev_stars
            star_delta_7d = repo.stargazers_count - (prev_7d["stars"] if prev_7d else prev_stars)

            prev_forks = prev["forks"] if prev else details["forks"]
            fork_delta_1d = details["forks"] - prev_forks

            star_acceleration = 0.0
            if prev_7d and prev_7d.get("star_delta_7d", 0) > 0:
                star_acceleration = star_delta_7d / max(prev_7d["star_delta_7d"], 1)

            now_iso = datetime.now(timezone.utc).isoformat()

            snapshot = {
                "repo": full_name,
                "time": now_iso,
                "stars": repo.stargazers_count,
                "star_delta_1d": star_delta_1d,
                "star_delta_7d": star_delta_7d,
                "star_acceleration": star_acceleration,
                "forks": details["forks"],
                "fork_delta_1d": fork_delta_1d,
                "open_issues": details["open_issues"],
                "contributors_30d": contributors_30d,
                "issue_response_h": 24.0,
                "pr_merge_rate": 0.85,
                # 评分依赖字段
                "full_name": full_name,
                "created_at": details["created_at"],
                "topics": details["topics"],
                "owner_type": details["owner_type"],
                "license": details["license"],
                "readme_score": readme_score,
            }

            # 五维度评分
            dimensions = {
                "growth": score_growth(snapshot, prev),
                "novelty": score_novelty(snapshot, all_topics),
                "community": score_community(snapshot),
                "authority": score_authority(snapshot, config),
                "quality": score_quality(snapshot),
            }
            composite = compute_composite(dimensions)
            labels = compute_labels(dimensions, snapshot)

            snapshot["score"] = composite
            snapshot["labels"] = labels

            append_snapshot(SNAPSHOTS_PATH, snapshot)

            one_liner = generate_one_liner({
                "repo": full_name,
                "star_delta_7d": star_delta_7d,
                "description": details["description"],
            })

            candidates.append({
                "rank": 0,
                "repo": full_name,
                "stars": repo.stargazers_count,
                "star_delta_1d": star_delta_1d,
                "star_delta_7d": star_delta_7d,
                "score": composite,
                "labels": labels,
                "one_liner": one_liner,
                "language": details.get("language", "unknown"),
                "topics": details.get("topics", []),
            })

            print(f"→ 综合 {composite:.1f} 分, {' '.join(labels) if labels else '未分类'}")

        except Exception as e:
            print(f"→ ⚠️ 失败: {e}")

    # 按分数降序排序
    candidates.sort(key=lambda x: x["score"], reverse=True)
    for rank, c in enumerate(candidates, 1):
        c["rank"] = rank

    # 构建分层 candidates.json
    top_n = config.get("tracking", {}).get("top_n_candidates", 50)
    summary = candidates[:top_n]
    details = []
    for c in candidates[:10]:
        full_name = c["repo"]
        p = tracked.get(full_name, {})
        d = dict(c)
        d["readme_summary"] = (p.get("description", "") or "")[:200]
        d["community"] = {
            "contributors_30d": p.get("contributors_30d", 0),
            "open_issues": p.get("open_issues", 0),
        }
        d["risk_note"] = ""
        details.append(d)

    now_iso = datetime.now(timezone.utc).isoformat()
    candidates_data = {
        "generated_at": now_iso,
        "summary": summary,
        "details": details,
    }

    save_json(CANDIDATES_PATH, candidates_data)
    save_json(PROFILES_PATH, tracked)

    print(f"✅ 完成！已处理 {len(repos)} 个仓库")
    print(f"  📁 快照 → {SNAPSHOTS_PATH}")
    print(f"  📁 候选 → {CANDIDATES_PATH}")
    print(f"  📁 档案 → {PROFILES_PATH}")


def do_report(config, push=False):
    """阶段二：生成日报（可选推送）"""
    print("=" * 50)
    print("📝 GitHub Star Tracker — 阶段二：生成日报")
    print("=" * 50)

    candidates_data = load_json(CANDIDATES_PATH)
    if candidates_data is None:
        print("❌ 错误：未找到 candidates.json，请先运行 --fetch")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    summary = candidates_data.get("summary", [])
    print(f"📊 候选项目数: {len(summary)}")

    md = generate_daily_report(summary, today)

    year_month = today[:7]
    report_dir = os.path.join(REPORTS_DIR, year_month)
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{today}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ 日报已写入 → {report_path}")

    # 导出 Web 面板数据
    print("🌐 导出 Web 面板数据...")
    panel = build_panel_data(summary, today)
    export_latest(panel, WEB_DATA_DIR)
    export_archive(panel, WEB_DATA_DIR)
    update_archive_index(WEB_DATA_DIR)
    print(f"✅ Web 面板已更新")

    if push:
        title = f"GitHub 开源项目日报 — {today}"
        print(f"📨 推送中...")
        results = push_all(config, title, md)
        for channel, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {channel}: {result['message']}")

    print("=" * 50)
    print(f"✅ 日报生成完成")
    print("=" * 50)


def do_weekly(config):
    """阶段二：生成周报并推送"""
    print("=" * 50)
    print("📝 GitHub Star Tracker — 周报生成")
    print("=" * 50)

    candidates_data = load_json(CANDIDATES_PATH)
    if candidates_data is None:
        print("❌ 错误：未找到 candidates.json，请先运行 --fetch")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    week_number = datetime.now().isocalendar()[1]
    summary = candidates_data.get("summary", [])
    print(f"📊 候选项目数: {len(summary)}")

    md = generate_weekly_report(summary, today)

    year_month = today[:7]
    report_dir = os.path.join(REPORTS_DIR, year_month)
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"weekly-W{week_number}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ 周报已写入 → {report_path}")

    title = f"GitHub 开源项目周报 — {today} (Week {week_number})"
    print(f"📨 推送中...")
    results = push_all(config, title, md)
    for channel, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {channel}: {result['message']}")

    print("=" * 50)
    print(f"✅ 周报生成完成")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Star Tracker — 开源项目追踪 CLI",
    )
    parser.add_argument("--fetch", action="store_true", help="阶段一：抓取 + 评分")
    parser.add_argument("--report", action="store_true", help="阶段二：生成日报（不推送）")
    parser.add_argument("--push", action="store_true", help="阶段二：生成日报 + 推送")
    parser.add_argument("--weekly", action="store_true", help="阶段二：生成周报 + 推送")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径（可选）")

    args = parser.parse_args()

    config = load_config(args.config)

    if args.fetch:
        do_fetch(config)
    elif args.report:
        do_report(config, push=False)
    elif args.push:
        do_report(config, push=True)
    elif args.weekly:
        do_weekly(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
