import re
from datetime import datetime, timezone

WEIGHTS = {
    "growth": 0.35,
    "novelty": 0.20,
    "community": 0.25,
    "authority": 0.10,
    "quality": 0.10,
}


def score_growth(repo, prev_snapshot):
    """增长信号评分 (0-100)"""
    delta_1d = repo.get("star_delta_1d", 0)
    delta_7d = repo.get("star_delta_7d", 0)
    acceleration = 1.0
    if prev_snapshot and prev_snapshot.get("star_delta_7d", 0) > 0:
        acceleration = delta_7d / max(prev_snapshot["star_delta_7d"], 1)

    day_score = min(delta_1d / 10, 10) * 4  # 日增量 100 满分
    week_score = min(delta_7d / 100, 10) * 4  # 周增量 1000 满分
    accel_score = min(acceleration, 3.0) / 3.0 * 20  # 加速度
    return min(day_score + week_score + accel_score, 100)


def score_novelty(repo, all_topics):
    """新颖度评分 (0-100)"""
    score = 0
    # 创建时间
    created = datetime.fromisoformat(repo.get("created_at", "2020-01-01T00:00:00Z"))
    days_ago = (datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)).days
    if days_ago <= 30:
        score += 40
    elif days_ago <= 90:
        score += 25
    elif days_ago <= 180:
        score += 10

    # 新项目且 star 高
    if days_ago <= 90 and repo.get("stars", 0) >= 500:
        score += 30

    # Topic 稀有度
    topics = repo.get("topics", [])
    if topics:
        rare_count = sum(1 for t in topics if t not in all_topics)
        score += min(rare_count * 5, 20)

    return min(score, 100)


def score_community(repo):
    """社区健康度评分 (0-100)"""
    score = 0
    contributors = repo.get("contributors_30d", 0)
    score += min(contributors / 3, 10) * 5  # 15 个以上满分 50

    response_h = repo.get("issue_response_h", 72)
    if response_h <= 4:
        score += 25
    elif response_h <= 24:
        score += 15

    pr_rate = repo.get("pr_merge_rate", 0)
    score += pr_rate * 25

    return min(score, 100)


def score_authority(repo, config):
    """权威背书评分 (0-100)"""
    score = 0
    full_name = repo.get("full_name", "").lower()
    org = full_name.split("/")[0] if "/" in full_name else ""
    whitelist = config.get("tracking", {}).get("org_whitelist", [])
    if org in [o.lower() for o in whitelist]:
        score += 50

    if repo.get("owner_type") == "org":
        score += 20

    return min(score, 100)


def score_quality(repo):
    """内容质量评分 (0-100)"""
    score = 0
    readme_score = repo.get("readme_score", 0)
    score += readme_score * 0.7

    if repo.get("license") and repo["license"] != "NOASSERTION":
        score += 30

    return min(score, 100)


def compute_readme_score(readme_text):
    """根据 README 文本计算质量分 (0-100)"""
    if not readme_text:
        return 0
    score = 0
    word_count = len(readme_text.split())
    score += min(word_count / 10, 50)  # 500 词满分

    has_chinese = bool(re.search(r"[一-鿿]", readme_text))
    if has_chinese:
        score += 10  # 多语言加分

    has_images = "![" in readme_text or "<img" in readme_text
    if has_images:
        score += 15  # 有截图/Demo

    has_badge = "https://img.shields.io" in readme_text or "badge" in readme_text.lower()
    if has_badge:
        score += 5

    sections = ["install", "usage", "getting started", "quick start", "demo", "documentation"]
    match_count = sum(1 for s in sections if s in readme_text.lower())
    score += min(match_count * 3, 20)

    return min(score, 100)


def compute_composite(dimensions):
    """计算综合评分"""
    return round(sum(dimensions[k] * WEIGHTS[k] for k in WEIGHTS), 1)


def compute_labels(dimensions, repo):
    """生成标签"""
    labels = []
    if dimensions.get("growth", 0) >= 70:
        labels.append("🔥爆发中")
    if dimensions.get("novelty", 0) >= 60:
        labels.append("🌱新星")
    if dimensions.get("quality", 0) >= 70:
        labels.append("✅高质量")
    if dimensions.get("authority", 0) >= 50:
        labels.append("🏢大厂背书")
    return labels
