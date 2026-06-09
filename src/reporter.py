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


def _compute_distribution(candidates, key, is_list=False):
    dist = {}
    for r in candidates:
        values = r.get(key, []) if is_list else [r.get(key, "unknown")]
        for v in values:
            if v:
                dist[v] = dist.get(v, 0) + 1
    return dict(sorted(dist.items(), key=lambda x: -x[1]))


def _render_repo_item(i, r, metric_key="star_delta_7d", metric_label="/ 周"):
    """渲染单个仓库条目，含语言色标、标签、描述"""
    labels = " ".join(r.get("labels", []))
    name = _repo_name(r)
    delta = _delta_str(r.get(metric_key, 0))
    lang = r.get("language", "unknown")
    desc = r.get("one_liner", "") or ""
    score = r.get("score", 0)
    return (
        f"{i}. **[{name}](https://github.com/{name})** — {delta} {metric_label}  "
        f"| ⭐{r.get('stars', 0):,} | `{lang}`  |  {score:.1f}分  |  {labels}\n"
        f"   {desc}\n"
    )


def _render_stats_header(candidates):
    """渲染统计摘要"""
    total = len(candidates)
    total_stars = sum(r.get("stars", 0) for r in candidates)
    top = max(candidates, key=lambda r: r.get("stars", 0)) if candidates else None
    top_day = max(candidates, key=lambda r: r.get("star_delta_1d", 0)) if candidates else None
    top_week = max(candidates, key=lambda r: r.get("star_delta_7d", 0)) if candidates else None

    lines = [
        "## 📊 数据概览",
        "",
        f"- 追踪项目：{total} 个",
        f"- 累计星数：{total_stars:,} ⭐",
    ]
    if top:
        lines.append(f"- 最高星数：**[{_repo_name(top)}](https://github.com/{_repo_name(top)})** — {top.get('stars', 0):,} ⭐")
    if top_day:
        lines.append(f"- 今日增量冠军：**[{_repo_name(top_day)}](https://github.com/{_repo_name(top_day)})** — +{top_day.get('star_delta_1d', 0)}⭐")
    if top_week:
        lines.append(f"- 本周增量冠军：**[{_repo_name(top_week)}](https://github.com/{_repo_name(top_week)})** — +{top_week.get('star_delta_7d', 0)}⭐")
    lines.append("")
    return lines


def _render_distribution(candidates):
    """渲染分类分布摘要"""
    lang_dist = _compute_distribution(candidates, "language")
    label_dist = _compute_distribution(candidates, "labels", is_list=True)

    lines = ["### 编程语言 TOP 5", ""]
    for lang, count in list(lang_dist.items())[:5]:
        lines.append(f"- {lang}: {count} 个项目")
    lines.append("")

    if label_dist:
        lines.append("### 评分标签分布")
        lines.append("")
        for label, count in label_dist.items():
            lines.append(f"- {label}: {count} 个项目")
        lines.append("")

    return lines


def _generate_sections(candidates):
    """生成日报的核心板块（不含标题和页脚）"""
    lines = []

    # 统计摘要
    lines.extend(_render_stats_header(candidates))
    lines.append("---")
    lines.append("")

    # 今日增速 TOP 10
    lines.append("## 🔥 今日增速 TOP 10")
    lines.append("")
    top_day = sorted(candidates, key=lambda x: (x.get("star_delta_1d", 0), x.get("stars", 0)), reverse=True)[:10]
    for i, r in enumerate(top_day, 1):
        lines.append(_render_repo_item(i, r, "star_delta_1d", "今日"))
    lines.append("")

    # 本周爆发榜
    lines.append("## 💥 本周爆发榜")
    lines.append("")
    top_week = sorted(candidates, key=lambda x: (x.get("star_delta_7d", 0), x.get("stars", 0)), reverse=True)[:10]
    for i, r in enumerate(top_week, 1):
        lines.append(_render_repo_item(i, r, "star_delta_7d", "/ 周"))
    lines.append("")

    # 潜力新星
    lines.append("## 🌱 潜力新星")
    lines.append("")
    new_stars = sorted(
        [r for r in candidates if "🌱新星" in r.get("labels", [])],
        key=lambda r: r.get("score", 0), reverse=True)[:10]
    if new_stars:
        for i, r in enumerate(new_stars, 1):
            lines.append(_render_repo_item(i, r, "star_delta_7d", "/ 周"))
    else:
        lines.append("> 暂无新项目入选。\n")
    lines.append("")

    # 历史星数榜
    lines.append("## 🏆 历史星数榜 TOP 10")
    lines.append("")
    top_stars = sorted(candidates, key=lambda r: r.get("stars", 0), reverse=True)[:10]
    for i, r in enumerate(top_stars, 1):
        name = _repo_name(r)
        labels = " ".join(r.get("labels", []))
        lines.append(
            f"{i}. **[{name}](https://github.com/{name})** — "
            f"⭐{r.get('stars', 0):,} | `{r.get('language', 'unknown')}`  |  {r.get('score', 0):.1f}分  |  {labels}"
        )
        lines.append(f"   {r.get('one_liner', '')}")
        lines.append("")
    lines.append("")

    # 分类统计
    lines.append("## 📈 分类统计")
    lines.append("")
    lines.extend(_render_distribution(candidates))
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
    week_number = __import__("datetime").datetime.now().isocalendar()[1]

    lines = [
        f"# GitHub 开源项目周报 — {date_str} (Week {week_number})",
        "",
        "## 📊 本周赛道观察",
        "",
        trend_notes or "> 本周各赛道保持活跃，AI Agent 方向持续领跑。",
        "",
        "---",
        "",
    ]

    if not candidates:
        lines.append("> ⚠️ 暂无数据，请稍后重试。")
    else:
        lines.extend(_generate_sections(candidates))

    lines.append("")
    lines.append(f"> 🤖 由 GitHub Star Tracker 自动生成 | {date_str}")
    return "\n".join(lines)
