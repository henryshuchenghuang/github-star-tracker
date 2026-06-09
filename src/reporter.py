def generate_one_liner(repo):
    """生成一句话概括"""
    name = repo.get("repo", repo.get("full_name", "unknown"))
    delta = repo.get("star_delta_7d", 0)
    desc = repo.get("description", "")[:80]
    sign = "+" if delta >= 0 else ""
    return f"{name}：{desc}，本周 {sign}{delta}⭐"


def _repo_name(repo):
    return repo.get("repo", repo.get("full_name", "unknown"))


def _delta_str(delta):
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta}⭐"


def _generate_sections(candidates):
    """生成日报的三个核心段落（不含标题和页脚）"""
    lines = []

    # 今日增速 TOP 10
    lines.append("## 🔥 今日增速 TOP 10")
    lines.append("")
    top_day = sorted(candidates, key=lambda x: x.get("star_delta_1d", 0), reverse=True)[:10]
    for i, r in enumerate(top_day, 1):
        labels = " ".join(r.get("labels", []))
        name = _repo_name(r)
        delta = _delta_str(r.get("star_delta_1d", 0))
        lines.append(f"{i}. **[{name}](https://github.com/{name})** — {delta} 今日  |  {labels}")
        lines.append(f"   {r.get('one_liner', '')}")
        lines.append("")

    # 本周爆发榜
    lines.append("## 💥 本周爆发榜")
    lines.append("")
    top_week = sorted(candidates, key=lambda x: x.get("star_delta_7d", 0), reverse=True)[:10]
    for i, r in enumerate(top_week, 1):
        labels = " ".join(r.get("labels", []))
        name = _repo_name(r)
        delta = _delta_str(r.get("star_delta_7d", 0))
        lines.append(f"{i}. **[{name}](https://github.com/{name})** — {delta} / 周  |  综合 {r.get('score', 0):.1f}分  |  {labels}")
        lines.append(f"   {r.get('one_liner', '')}")
        lines.append("")

    # 潜力新星
    lines.append("## 🌱 潜力新星")
    lines.append("")
    new_stars = [r for r in candidates if "🌱新星" in r.get("labels", [])]
    if new_stars:
        for i, r in enumerate(new_stars[:10], 1):
            name = _repo_name(r)
            lines.append(f"{i}. **[{name}](https://github.com/{name})** — {r.get('one_liner', '')}")
            lines.append("")
    else:
        lines.append("> 暂无新项目入选。")
        lines.append("")

    return lines


def generate_daily_report(candidates, date_str):
    """生成日报 Markdown"""
    lines = [
        f"# GitHub 开源项目日报 — {date_str}",
        "",
    ]

    if not candidates:
        lines.append("> ⚠️ 暂无数据，请稍后重试。")
        return "\n".join(lines)

    lines.extend(_generate_sections(candidates))
    lines.append(f"> 🤖 由 GitHub Star Tracker 自动生成 | {date_str}")
    return "\n".join(lines)


def generate_weekly_report(candidates, date_str, trend_notes=""):
    """生成周报 Markdown"""
    lines = [
        f"# GitHub 开源项目周报 — {date_str}",
        "",
        "## 📊 本周赛道观察",
        "",
        trend_notes or "> 本周各赛道保持活跃，AI Agent 方向持续领跑。",
        "",
        "---",
        "",
        "## 📋 本周数据汇总",
        "",
    ]

    if not candidates:
        lines.append("> ⚠️ 暂无数据，请稍后重试。")
    else:
        lines.extend(_generate_sections(candidates))

    lines.append("")
    lines.append(f"> 🤖 由 GitHub Star Tracker 自动生成 | {date_str}")
    return "\n".join(lines)
