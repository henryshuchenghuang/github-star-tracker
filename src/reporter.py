def generate_one_liner(repo):
    """生成一句话概括"""
    name = repo.get("repo", repo.get("full_name", "unknown"))
    delta = repo.get("star_delta_7d", 0)
    desc = repo.get("description", "")[:80]
    return f"{name}：{desc}，本周 +{delta}⭐"


def generate_daily_report(candidates, date_str):
    """生成日报 Markdown"""
    lines = [
        f"# GitHub 开源项目日报 — {date_str}",
        "",
    ]

    if not candidates:
        lines.append("> ⚠️ 暂无数据，请稍后重试。")
        return "\n".join(lines)

    # 今日增速 TOP 10
    lines.append("## 🔥 今日增速 TOP 10")
    lines.append("")
    top_day = sorted(candidates, key=lambda x: x.get("star_delta_1d", 0), reverse=True)[:10]
    for i, r in enumerate(top_day, 1):
        labels = " ".join(r.get("labels", []))
        lines.append(f"{i}. **[{r['repo']}](https://github.com/{r['repo']})** — +{r.get('star_delta_1d', 0)}⭐ 今日  |  {labels}")
        lines.append(f"   {r.get('one_liner', '')}")
        lines.append("")

    # 本周爆发榜
    lines.append("## 💥 本周爆发榜")
    lines.append("")
    top_week = sorted(candidates, key=lambda x: x.get("star_delta_7d", 0), reverse=True)[:10]
    for i, r in enumerate(top_week, 1):
        labels = " ".join(r.get("labels", []))
        lines.append(f"{i}. **[{r['repo']}](https://github.com/{r['repo']})** — +{r.get('star_delta_7d', 0)}⭐ / 周  |  综合 {r.get('score', 0):.1f}分  |  {labels}")
        lines.append(f"   {r.get('one_liner', '')}")
        lines.append("")

    # 潜力新星
    lines.append("## 🌱 潜力新星")
    lines.append("")
    new_stars = [r for r in candidates if "🌱新星" in r.get("labels", [])]
    if new_stars:
        for i, r in enumerate(new_stars[:10], 1):
            lines.append(f"{i}. **[{r['repo']}](https://github.com/{r['repo']})** — {r.get('one_liner', '')}")
            lines.append("")
    else:
        lines.append("> 暂无新项目入选。")
        lines.append("")

    lines.append(f"> 🤖 由 GitHub Star Tracker 自动生成 | {date_str}")
    return "\n".join(lines)


def generate_weekly_report(candidates, date_str, trend_notes=""):
    """生成周报 Markdown"""
    daily = generate_daily_report(candidates, date_str)
    weekly_extra = [
        f"# GitHub 开源项目周报 — {date_str}",
        "",
        "## 📊 本周赛道观察",
        "",
        trend_notes or "> 本周各赛道保持活跃，AI Agent 方向持续领跑。",
        "",
        "---",
        "",
        daily.replace(f"# GitHub 开源项目日报 — {date_str}", "## 📋 本周数据汇总"),
    ]
    return "\n".join(weekly_extra)
