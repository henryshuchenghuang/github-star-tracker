# GitHub 开源项目追踪系统 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一套半自动化的 GitHub 开源项目追踪系统，阶段一 GitHub Actions 定时抓取评分，阶段二 Claude Code 手工复核推送。

**Architecture:** Python 脚本层（fetcher / scorer / reporter / pusher / web_exporter）通过 JSONL + JSON 文本文件交换数据。阶段一由 GitHub Actions 定时触发抓取+评分，commit 回仓库；阶段二用户本地 git pull 后由 Claude Code 复核推送。

**Tech Stack:** Python 3.12+, pygithub, requests, pyyaml, resend, 纯静态 HTML + vanilla JS

---

## File Structure Map

| 文件 | 职责 | 创建/修改 |
|------|------|:--:|
| `src/config.py` | 加载 config.yaml，提供配置访问接口 | Create |
| `src/fetcher.py` | GitHub API 数据抓取类 | Create |
| `src/scorer.py` | 五维度评分引擎 | Create |
| `src/store.py` | JSONL/JSON 读写管理 | Create |
| `src/reporter.py` | Markdown 日报/周报生成 | Create |
| `src/pusher.py` | 多渠道路由推送 | Create |
| `src/web_exporter.py` | Web 面板 JSON 导出 | Create |
| `src/main.py` | CLI 入口脚本 | Create |
| `web/index.html` | 静态 Web 面板 | Create |
| `.github/workflows/track.yml` | GitHub Actions 调度 | Create |
| `config.example.yaml` | 配置模板 | Create |
| `requirements.txt` | Python 依赖 | Create |
| `.gitignore` | Git 忽略规则 | Create |

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `src/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
pygithub>=2.3
requests>=2.32
pyyaml>=6.0
resend>=0.8
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
__pycache__/
*.pyc
.env
config.yaml
reports/
web/data/
```

- [ ] **Step 3: 创建 src/__init__.py（空文件）**

- [ ] **Step 4: 安装依赖**

```bash
pip install -r requirements.txt
```

Expected: 所有包安装成功。

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore src/__init__.py
git commit -m "chore: project scaffold with dependencies"
```

---

### Task 2: 配置管理

**Files:**
- Create: `config.example.yaml`
- Create: `src/config.py`

- [ ] **Step 1: 创建 config.example.yaml**

```yaml
github_token: "ghp_xxx"
tracking:
  languages: ["all"]
  min_stars: 100
  new_repo_days: 90
  new_repo_min_stars: 500
  top_n_candidates: 50
  org_whitelist:
    - google
    - meta
    - anthropic
    - bytedance
    - alibaba
    - microsoft
    - apple
    - openai
    - deepseek-ai
push:
  email:
    enabled: false
    provider: resend
    api_key: ""
    from: ""
    to: ""
  wechat:
    enabled: false
    provider: serverchan
    token: ""
  feishu:
    enabled: false
    webhook_url: ""
```

- [ ] **Step 2: 创建 src/config.py**

```python
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
```

- [ ] **Step 3: 验证配置文件可加载**

```bash
python -c "from src.config import load_config; c = load_config('config.example.yaml'); print('OK:', c['tracking']['languages'])"
```

Expected: `OK: ['all']`

- [ ] **Step 4: Commit**

```bash
git add config.example.yaml src/config.py
git commit -m "feat: configuration management"
```

---

### Task 3: 数据存储层（JSONL / JSON 读写）

**Files:**
- Create: `src/store.py`
- Create: `tests/test_store.py`

- [ ] **Step 1: 创建测试 tests/test_store.py**

```python
import json
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.store import append_snapshot, read_snapshots, save_json, load_json


def test_append_and_read_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "snapshots.jsonl")
        snap = {"repo": "test/repo", "time": "2026-06-10T14:00:00Z", "stars": 100}
        append_snapshot(path, snap)
        append_snapshot(path, snap)
        results = read_snapshots(path)
        assert len(results) == 2
        assert results[0]["stars"] == 100


def test_save_and_load_json():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.json")
        data = {"key": "value"}
        save_json(path, data)
        loaded = load_json(path)
        assert loaded == data


def test_read_nonexistent_file_returns_empty():
    assert read_snapshots("/nonexistent/path.jsonl") == []


def test_load_nonexistent_json_returns_none():
    assert load_json("/nonexistent/path.json") is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_store.py -v
```

Expected: FAIL — `ModuleNotFoundError` (store.py 尚不存在)

- [ ] **Step 3: 创建 src/store.py**

```python
import json
import os


def append_snapshot(path, snapshot):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def read_snapshots(path):
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_store.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/store.py tests/test_store.py
git commit -m "feat: JSONL/JSON storage layer"
```

---

### Task 4: GitHub API 数据抓取

**Files:**
- Create: `src/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: 创建 src/fetcher.py**

```python
import os
from datetime import datetime, timezone, timedelta
from github import Github


class GitHubFetcher:
    def __init__(self, token, config):
        self.client = Github(token)
        self.config = config

    def search_new_repos(self, since_days=7, min_stars=10):
        """搜索最近 N 天创建且有最低 star 的仓库"""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
        query = f"created:>={since} stars:>{self.config['tracking']['min_stars']}"
        langs = self.config["tracking"].get("languages", ["all"])
        if "all" not in langs:
            lang_filter = " OR ".join(f"language:{l}" for l in langs)
            query += f" ({lang_filter})"
        repos = self.client.search_repositories(query=query, sort="stars", order="desc")
        return list(repos[:self.config["tracking"]["top_n_candidates"]])

    def get_repo_details(self, full_name):
        """获取单个仓库的详细信息"""
        repo = self.client.get_repo(full_name)
        readme_text = ""
        try:
            readme_text = repo.get_readme().decoded_content.decode("utf-8")[:2000]
        except Exception:
            readme_text = ""

        return {
            "full_name": repo.full_name,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "language": repo.language or "unknown",
            "description": repo.description or "",
            "topics": repo.topics or [],
            "created_at": repo.created_at.isoformat(),
            "license": repo.license.spdx_id if repo.license else "",
            "owner_type": "org" if repo.owner.type == "Organization" else "individual",
            "readme_text": readme_text,
        }

    def get_contributors_count(self, full_name):
        """获取近 30 天贡献者数量（估算）"""
        repo = self.client.get_repo(full_name)
        try:
            contributors = repo.get_contributors()
            return sum(1 for _ in contributors[:100])
        except Exception:
            return 0

    def get_issue_stats(self, full_name):
        """获取 Issue 统计"""
        repo = self.client.get_repo(full_name)
        open_count = repo.open_issues_count
        return {"open_issues": open_count}
```

- [ ] **Step 2: 创建 tests/test_fetcher.py（仅测试纯函数，不涉及 API 调用）**

```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fetcher import GitHubFetcher


def test_fetcher_initialization():
    config = {"tracking": {"min_stars": 100, "languages": ["all"], "top_n_candidates": 50}}
    fetcher = GitHubFetcher("dummy_token", config)
    assert fetcher.config == config
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest tests/test_fetcher.py -v
```

Expected: 1 test PASS

- [ ] **Step 4: Commit**

```bash
git add src/fetcher.py tests/test_fetcher.py
git commit -m "feat: GitHub API fetcher"
```

---

### Task 5: 五维度评分引擎

**Files:**
- Create: `src/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: 创建 tests/test_scorer.py**

```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scorer import (
    score_growth,
    score_novelty,
    score_community,
    score_authority,
    score_quality,
    compute_composite,
)


def test_score_growth():
    repo = {"stars": 1000, "star_delta_1d": 100, "star_delta_7d": 500}
    prev = {"stars": 500, "star_delta_1d": 50, "star_delta_7d": 200}
    s = score_growth(repo, prev)
    assert 0 <= s <= 100


def test_score_novelty_new():
    repo = {"created_at": "2026-05-15T00:00:00Z", "stars": 600}
    s = score_novelty(repo, set())
    assert s > 50  # new + high stars = high novelty


def test_score_novelty_old():
    repo = {"created_at": "2020-01-01T00:00:00Z", "stars": 100}
    s = score_novelty(repo, set())
    assert s < 30  # old + low stars = low novelty


def test_score_community():
    repo = {"contributors_30d": 20, "issue_response_h": 2.0, "pr_merge_rate": 0.9}
    s = score_community(repo)
    assert 0 <= s <= 100


def test_score_authority():
    config = {"tracking": {"org_whitelist": ["google", "meta"]}}
    org_repo = {"full_name": "google/awesome", "owner_type": "org"}
    individual_repo = {"full_name": "someone/tool", "owner_type": "individual"}
    assert score_authority(org_repo, config) > score_authority(individual_repo, config)


def test_score_quality():
    good = {"readme_score": 85, "license": "MIT"}
    bad = {"readme_score": 10, "license": ""}
    assert score_quality(good) > score_quality(bad)


def test_composite():
    dimensions = {"growth": 80, "novelty": 70, "community": 60, "authority": 50, "quality": 40}
    score = compute_composite(dimensions)
    expected = 80 * 0.35 + 70 * 0.20 + 60 * 0.25 + 50 * 0.10 + 40 * 0.10
    assert abs(score - expected) < 0.01
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_scorer.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/scorer.py**

```python
import re
from datetime import datetime, timezone, timedelta

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
    return sum(dimensions[k] * WEIGHTS[k] for k in WEIGHTS)


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
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_scorer.py -v
```

Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/scorer.py tests/test_scorer.py
git commit -m "feat: five-dimensional scoring engine"
```

---

### Task 6: Markdown 日报/周报生成

**Files:**
- Create: `src/reporter.py`
- Create: `tests/test_reporter.py`

- [ ] **Step 1: 创建 tests/test_reporter.py**

```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.reporter import generate_daily_report, generate_weekly_report, generate_one_liner


def test_generate_one_liner():
    r = {"repo": "test/proj", "star_delta_7d": 500, "description": "A test project"}
    result = generate_one_liner(r)
    assert "test/proj" in result


def test_generate_daily_report():
    candidates = [
        {
            "rank": 1, "repo": "a/b", "stars": 1000,
            "star_delta_1d": 50, "star_delta_7d": 300, "score": 90,
            "labels": ["🔥爆发中"], "one_liner": "test project"
        }
    ]
    md = generate_daily_report(candidates, "2026-06-10")
    assert "# GitHub 开源项目日报" in md
    assert "2026-06-10" in md
    assert "a/b" in md
    assert "今日增速" in md
    assert "本周爆发" in md
    assert "潜力新星" in md


def test_generate_daily_report_empty():
    md = generate_daily_report([], "2026-06-10")
    assert "暂无数据" in md
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_reporter.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/reporter.py**

```python
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
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_reporter.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/reporter.py tests/test_reporter.py
git commit -m "feat: markdown report generator (daily + weekly)"
```

---

### Task 7: 多渠道路由推送

**Files:**
- Create: `src/pusher.py`
- Create: `tests/test_pusher.py`

- [ ] **Step 1: 创建 src/pusher.py**

```python
import requests
import smtplib
from email.mime.text import MIMEText


def push_email(config, subject, body):
    """通过 Resend API 发送邮件"""
    email_cfg = config.get("push", {}).get("email", {})
    if not email_cfg.get("enabled"):
        return False, "Email disabled"

    try:
        import resend
        resend.api_key = email_cfg["api_key"]
        resend.Emails.send({
            "from": email_cfg["from"],
            "to": email_cfg["to"],
            "subject": subject,
            "html": body.replace("\n", "<br>\n"),
        })
        return True, "Email sent"
    except ImportError:
        # fallback: SMTP
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = email_cfg["from"]
        msg["To"] = email_cfg["to"]
        with smtplib.SMTP_SSL(email_cfg.get("smtp_host", "smtp.resend.com"), 465) as s:
            s.login("resend", email_cfg["api_key"])
            s.send_message(msg)
        return True, "Email sent via SMTP"


def push_wechat(config, title, body):
    """通过 Server酱 推送到微信"""
    wx_cfg = config.get("push", {}).get("wechat", {})
    if not wx_cfg.get("enabled"):
        return False, "WeChat disabled"

    token = wx_cfg["token"]
    summary = body[:500]  # 微信消息有长度限制
    url = f"https://sctapi.ftqq.com/{token}.send"
    resp = requests.post(url, data={"title": title, "desp": summary})
    return resp.status_code == 200, resp.text


def push_feishu(config, title, body):
    """通过飞书 Webhook 推送"""
    fs_cfg = config.get("push", {}).get("feishu", {})
    if not fs_cfg.get("enabled"):
        return False, "Feishu disabled"

    webhook_url = fs_cfg["webhook_url"]
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}},
            "elements": [{"tag": "markdown", "content": body}],
        },
    }
    resp = requests.post(webhook_url, json=payload)
    return resp.status_code == 200, resp.text


def push_all(config, subject, body):
    """推送到所有已启用的渠道"""
    results = {}
    success, msg = push_email(config, subject, body)
    results["email"] = {"success": success, "message": msg}

    success, msg = push_wechat(config, subject, body)
    results["wechat"] = {"success": success, "message": msg}

    success, msg = push_feishu(config, subject, body)
    results["feishu"] = {"success": success, "message": msg}

    return results
```

- [ ] **Step 2: 创建 tests/test_pusher.py**

```python
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
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest tests/test_pusher.py -v
```

Expected: 1 test PASS

- [ ] **Step 4: Commit**

```bash
git add src/pusher.py tests/test_pusher.py
git commit -m "feat: multi-channel push (email/wechat/feishu)"
```

---

### Task 8: Web 面板 JSON 导出

**Files:**
- Create: `src/web_exporter.py`
- Create: `tests/test_web_exporter.py`

- [ ] **Step 1: 创建 tests/test_web_exporter.py**

```python
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.web_exporter import export_latest, export_archive, build_panel_data


def test_build_panel_data():
    candidates = [
        {"rank": 1, "repo": "a/b", "stars": 1000, "star_delta_1d": 50,
         "star_delta_7d": 300, "score": 90, "labels": ["🔥爆发中"],
         "one_liner": "test"}
    ]
    data = build_panel_data(candidates, "2026-06-10")
    assert data["date"] == "2026-06-10"
    assert len(data["candidates"]) == 1


def test_export_latest():
    with tempfile.TemporaryDirectory() as tmp:
        data = {"date": "2026-06-10", "candidates": []}
        export_latest(data, os.path.join(tmp, "web/data"))
        assert os.path.exists(os.path.join(tmp, "web/data/latest.json"))


def test_export_archive():
    with tempfile.TemporaryDirectory() as tmp:
        data = {"date": "2026-06-10", "candidates": []}
        export_archive(data, os.path.join(tmp, "web/data"))
        assert os.path.exists(os.path.join(tmp, "web/data/archive/2026-06-10.json"))
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_web_exporter.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 创建 src/web_exporter.py**

```python
import os
import json


def build_panel_data(candidates, date_str):
    """从候选列表构建面板数据"""
    return {
        "date": date_str,
        "generated_at": date_str,
        "candidates": candidates,
        "stats": {
            "total_candidates": len(candidates),
            "top_day": sorted(candidates, key=lambda x: x.get("star_delta_1d", 0), reverse=True)[:10],
            "top_week": sorted(candidates, key=lambda x: x.get("star_delta_7d", 0), reverse=True)[:10],
            "new_stars": [r for r in candidates if "🌱新星" in r.get("labels", [])],
        },
    }


def export_latest(panel_data, web_data_dir):
    """覆盖写入 latest.json"""
    os.makedirs(web_data_dir, exist_ok=True)
    path = os.path.join(web_data_dir, "latest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel_data, f, ensure_ascii=False, indent=2)


def export_archive(panel_data, web_data_dir):
    """写入 archive/YYYY-MM-DD.json"""
    date_str = panel_data["date"]
    archive_dir = os.path.join(web_data_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    path = os.path.join(archive_dir, f"{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel_data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_web_exporter.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/web_exporter.py tests/test_web_exporter.py
git commit -m "feat: web panel JSON exporter"
```

---

### Task 9: CLI 入口脚本 (main.py)

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: 创建 src/main.py**

```python
#!/usr/bin/env python3
"""GitHub Star Tracker — 开源项目追踪工具

Usage:
  python src/main.py --fetch          # 阶段一：抓取 + 评分
  python src/main.py --report          # 阶段二：从 candidates.json 生成日报
  python src/main.py --report --push   # 阶段二：生成日报 + 推送
  python src/main.py --weekly          # 阶段二：生成周报
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta

from src.config import load_config
from src.fetcher import GitHubFetcher
from src.scorer import (
    score_growth, score_novelty, score_community,
    score_authority, score_quality, compute_composite,
    compute_readme_score, compute_labels,
)
from src.store import append_snapshot, read_snapshots, save_json, load_json
from src.reporter import generate_daily_report, generate_weekly_report, generate_one_liner
from src.pusher import push_all
from src.web_exporter import build_panel_data, export_latest, export_archive

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOTS_PATH = os.path.join(DATA_DIR, "snapshots.jsonl")
PROFILES_PATH = os.path.join(DATA_DIR, "profiles.json")
CANDIDATES_PATH = os.path.join(DATA_DIR, "candidates.json")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
WEB_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "data")


def do_fetch(config):
    """阶段一：抓取 + 评分"""
    print("[fetch] Starting data fetch...")
    fetcher = GitHubFetcher(config["github_token"], config)
    profiles = load_json(PROFILES_PATH) or {}
    prev_snapshots = read_snapshots(SNAPSHOTS_PATH)

    # 搜新仓库
    print("[fetch] Searching new repos...")
    repos = fetcher.search_new_repos(since_days=7)
    candidates = []
    all_topics = set()
    for p in profiles.values():
        for t in p.get("topics", []):
            all_topics.add(t)

    for rank, repo in enumerate(repos, 1):
        details = fetcher.get_repo_details(repo.full_name)
        details["contributors_30d"] = fetcher.get_contributors_count(repo.full_name)
        details["readme_score"] = compute_readme_score(details.get("readme_text", ""))

        # 保存 profile
        profiles[repo.full_name] = {
            "created_at": details["created_at"],
            "owner_type": details["owner_type"],
            "topics": details["topics"],
            "license": details["license"],
            "readme_score": details["readme_score"],
            "language": details["language"],
            "first_seen_at": profiles.get(repo.full_name, {}).get(
                "first_seen_at", datetime.now(timezone.utc).isoformat()
            ),
        }

        # 找上一个快照
        prev = None
        for s in reversed(prev_snapshots):
            if s["repo"] == repo.full_name:
                prev = s
                break

        # 计算增量
        prev_stars = prev["stars"] if prev else repo.stargazers_count
        star_delta_1d = repo.stargazers_count - prev_stars
        prev_week_stars = repo.stargazers_count  # TODO: 精确计算需要 7 天前的快照
        star_delta_7d = repo.stargazers_count - prev_stars  # 简化版
        acceleration = 1.0
        if prev and prev.get("star_delta_7d", 0) > 0:
            acceleration = star_delta_7d / max(prev["star_delta_7d"], 1)

        snapshot = {
            "repo": repo.full_name,
            "time": datetime.now(timezone.utc).isoformat(),
            "stars": repo.stargazers_count,
            "star_delta_1d": star_delta_1d,
            "star_delta_7d": star_delta_7d,
            "star_acceleration": round(acceleration, 2),
            "forks": repo.forks_count,
            "fork_delta_1d": 0,  # TODO
            "open_issues": repo.open_issues_count,
            "contributors_30d": details["contributors_30d"],
            "issue_response_h": 24.0,  # TODO: 需要额外 API
            "pr_merge_rate": 0.85,  # TODO: 需要额外 API
            "score": 0,
            "labels": [],
        }

        # 评分
        dims = {
            "growth": score_growth(snapshot, prev),
            "novelty": score_novelty(details, all_topics),
            "community": score_community(snapshot),
            "authority": score_authority(details, config),
            "quality": score_quality(details),
        }
        snapshot["score"] = round(compute_composite(dims), 1)
        snapshot["labels"] = compute_labels(dims, details)

        append_snapshot(SNAPSHOTS_PATH, snapshot)

        candidates.append({
            "rank": rank,
            "repo": repo.full_name,
            "stars": repo.stargazers_count,
            "star_delta_1d": star_delta_1d,
            "star_delta_7d": star_delta_7d,
            "score": snapshot["score"],
            "labels": snapshot["labels"],
            "one_liner": generate_one_liner({
                "repo": repo.full_name,
                "star_delta_7d": star_delta_7d,
                "description": repo.description or "",
            }),
        })

    # 排序：按综合评分
    candidates.sort(key=lambda x: x["score"], reverse=True)
    for i, c in enumerate(candidates):
        c["rank"] = i + 1

    # 构造分层 candidates.json
    top_n = config["tracking"]["top_n_candidates"]
    summary = candidates[:top_n]

    details_map = {}
    for c in summary[:10]:  # 只给 top 10 生成详情
        r = [x for x in repos if x.full_name == c["repo"]]
        if r:
            d = fetcher.get_repo_details(r[0].full_name)
            details_map[c["repo"]] = {
                "readme_summary": d.get("readme_text", "")[:200],
                "commit_trend": "",
                "community": {
                    "issue_response_h": 24.0,
                    "pr_merge_rate": 0.85,
                    "bus_factor": 1,
                },
                "risk_note": "",
            }

    candidates_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_candidates": len(summary),
        "summary": summary,
        "details": details_map,
    }
    save_json(CANDIDATES_PATH, candidates_json)
    save_json(PROFILES_PATH, profiles)
    print(f"[fetch] Done. {len(candidates)} candidates saved.")


def do_report(config, push=False):
    """阶段二：从 candidates.json 生成日报"""
    candidates_data = load_json(CANDIDATES_PATH)
    if not candidates_data:
        print("[report] No candidates found. Run --fetch first.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    summary = candidates_data.get("summary", [])

    # 生成日报
    md = generate_daily_report(summary, today)

    # 写入 reports/
    month = datetime.now().strftime("%Y-%m")
    report_dir = os.path.join(REPORTS_DIR, month)
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{today}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[report] Report saved to {report_path}")

    # 导出 Web 面板数据
    panel_data = build_panel_data(summary, today)
    export_latest(panel_data, WEB_DATA_DIR)
    export_archive(panel_data, WEB_DATA_DIR)
    print(f"[report] Web data exported to {WEB_DATA_DIR}")

    # 推送
    if push:
        title = f"GitHub 开源项目日报 — {today}"
        results = push_all(config, title, md)
        for channel, r in results.items():
            status = "OK" if r["success"] else "FAIL"
            print(f"[push] {channel}: {status} — {r.get('message', '')}")


def do_weekly(config):
    """阶段二：生成周报"""
    today = datetime.now().strftime("%Y-%m-%d")
    candidates_data = load_json(CANDIDATES_PATH) or {}
    summary = candidates_data.get("summary", [])
    md = generate_weekly_report(summary, today)

    month = datetime.now().strftime("%Y-%m")
    week = datetime.now().isocalendar()[1]
    report_dir = os.path.join(REPORTS_DIR, month)
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"weekly-W{week}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[weekly] Report saved to {report_path}")

    title = f"GitHub 开源项目周报 — W{week}"
    results = push_all(config, title, md)
    for channel, r in results.items():
        status = "OK" if r["success"] else "FAIL"
        print(f"[push] {channel}: {status}")


def main():
    parser = argparse.ArgumentParser(description="GitHub Star Tracker")
    parser.add_argument("--fetch", action="store_true", help="阶段一：抓取数据并评分")
    parser.add_argument("--report", action="store_true", help="阶段二：生成日报")
    parser.add_argument("--push", action="store_true", help="阶段二：生成日报并推送")
    parser.add_argument("--weekly", action="store_true", help="阶段二：生成周报")
    parser.add_argument("--config", default=None, help="配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.fetch:
        do_fetch(config)
    elif args.weekly:
        do_weekly(config)
    elif args.report or args.push:
        do_report(config, push=args.push)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证 CLI 可运行**

```bash
python src/main.py --help
```

Expected: 打印帮助信息。

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: CLI entry point (fetch + report + push)"
```

---

### Task 10: GitHub Actions 调度

**Files:**
- Create: `.github/workflows/track.yml`

- [ ] **Step 1: 创建 .github/workflows/track.yml**

```yaml
name: GitHub Star Tracker

on:
  schedule:
    - cron: '0 */6 * * *'     # 每 6 小时抓取
    - cron: '0 1 * * *'       # 北京时间 9:00
  workflow_dispatch:           # 手动触发

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Create config from secrets
        run: |
          cat > config.yaml << EOF
          github_token: "${{ secrets.GITHUB_TOKEN }}"
          tracking:
            languages: ["all"]
            min_stars: 100
            new_repo_days: 90
            new_repo_min_stars: 500
            top_n_candidates: 50
            org_whitelist:
              - google
              - meta
              - anthropic
              - bytedance
              - alibaba
              - microsoft
              - openai
              - deepseek-ai
          push:
            email:
              enabled: false
            wechat:
              enabled: false
            feishu:
              enabled: false
          EOF

      - name: Run tracker
        run: python src/main.py --fetch

      - name: Commit and push data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "data: auto snapshot $(date -Iminutes)"
          git push
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/track.yml
git commit -m "feat: GitHub Actions scheduled tracking"
```

---

### Task 11: Claude Code 斜杠命令

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: 读取当前 settings.local.json**

```bash
cat .claude/settings.local.json
```

- [ ] **Step 2: 添加斜杠命令配置**

在 settings.local.json 中添加：

```json
{
  "slashCommands": [
    {
      "name": "/analyze-trending",
      "description": "分析 GitHub 开源项目趋势，生成日报并推送",
      "prompt": "读取 data/candidates.json。先扫描 summary 层的 TOP-50 候选项目，识别以下情况：1) 刷 star 嫌疑（star/fork 比异常、contributor 几乎为零）；2) 套壳项目（README 空洞、实质代码极少）；3) 真正值得关注但评分偏低的项目（赛道新颖、技术扎实但低调）。对可疑项目展开 details 层查看详情。过滤完后生成日报 Markdown 写入 reports/，同时调用 web_exporter 导出 JSON。将日报推送到已启用的渠道（邮箱/微信/飞书）。用中文回复。"
    },
    {
      "name": "/analyze-trending-weekly",
      "description": "分析本周 GitHub 趋势，生成汇总周报",
      "prompt": "读取 data/candidates.json 和本周的 data/snapshots.jsonl。用 Claude 分析本周整体趋势：哪些赛道在升温，哪些在降温，选出 3-5 个最值得关注的项目做深度点评。生成周报写入 reports/，推送到已启用的渠道。用中文回复。"
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add .claude/settings.local.json
git commit -m "feat: Claude Code slash commands for trending analysis"
```

---

### Task 12: 静态 Web 面板

**Files:**
- Create: `web/index.html`

- [ ] **Step 1: 创建 web/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Star Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 8px; }
        .panel { display: flex; gap: 20px; max-width: 1400px; margin: 0 auto; }
        .sidebar { width: 200px; flex-shrink: 0; }
        .main { flex: 1; }
        .date-item { padding: 8px 12px; cursor: pointer; border-radius: 6px; margin-bottom: 4px; }
        .date-item:hover, .date-item.active { background: #21262d; color: #58a6ff; }
        .section { margin-bottom: 24px; }
        .section h2 { border-bottom: 1px solid #21262d; padding-bottom: 8px; margin-bottom: 12px; }
        .repo-card { padding: 12px; border: 1px solid #21262d; border-radius: 6px; margin-bottom: 8px; }
        .repo-card:hover { background: #161b22; }
        .repo-name { color: #58a6ff; text-decoration: none; font-weight: 600; }
        .repo-meta { font-size: 0.85em; color: #8b949e; margin-top: 4px; }
        .tag { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-right: 4px; }
        .tag-fire { background: #da3633; color: #fff; }
        .tag-new { background: #238636; color: #fff; }
        .tag-quality { background: #1f6feb; color: #fff; }
        .tag-enterprise { background: #8957e5; color: #fff; }
        .search-bar { margin-bottom: 16px; }
        .search-bar input { width: 100%; padding: 10px 16px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; font-size: 1em; }
        .loading { text-align: center; padding: 40px; color: #8b949e; }
    </style>
</head>
<body>
    <h1>🚀 GitHub Star Tracker</h1>
    <p style="color:#8b949e;margin-bottom:24px;">开源项目趋势追踪面板</p>

    <div class="search-bar">
        <input type="text" id="search" placeholder="搜索项目名或标签..." oninput="filterRepos()">
    </div>

    <div class="panel">
        <div class="sidebar">
            <h3 style="margin-bottom:12px">📅 历史日期</h3>
            <div id="date-list"></div>
        </div>
        <div class="main" id="content">
            <div class="loading">加载中...</div>
        </div>
    </div>

    <script>
        let currentData = null;
        let allDates = [];

        async function init() {
            await loadDates();
            await loadDate('latest');
        }

        async function loadDates() {
            try {
                const resp = await fetch('data/latest.json');
                if (resp.ok) allDates.push('latest');
            } catch(e) {}
            // 列出已知日期（可通过简单的日期列表 API 扩展）
            const today = new Date().toISOString().split('T')[0];
            for (let i = 0; i < 30; i++) {
                const d = new Date();
                d.setDate(d.getDate() - i);
                const ds = d.toISOString().split('T')[0];
                if (!allDates.includes(ds)) allDates.push(ds);
            }
            renderDates();
        }

        function renderDates() {
            const el = document.getElementById('date-list');
            el.innerHTML = allDates.map(d =>
                `<div class="date-item${d === 'latest' ? ' active' : ''}" onclick="loadDate('${d}')">${d === 'latest' ? '最新' : d}</div>`
            ).join('');
        }

        async function loadDate(dateStr) {
            const url = dateStr === 'latest' ? 'data/latest.json' : `data/archive/${dateStr}.json`;
            try {
                const resp = await fetch(url);
                currentData = await resp.json();
                render();
            } catch(e) {
                document.getElementById('content').innerHTML = '<div class="loading">该日期暂无数据</div>';
            }
            document.querySelectorAll('.date-item').forEach(el => el.classList.remove('active'));
            event?.target?.classList.add('active');
        }

        function filterRepos() {
            render(document.getElementById('search').value.toLowerCase());
        }

        function render(filter = '') {
            if (!currentData) return;
            const { candidates, stats, date } = currentData;
            const filtered = filter ? candidates.filter(c =>
                c.repo.toLowerCase().includes(filter) || c.one_liner.toLowerCase().includes(filter)
            ) : candidates;

            const tagClass = {
                '🔥爆发中': 'tag-fire', '🌱新星': 'tag-new',
                '✅高质量': 'tag-quality', '🏢大厂背书': 'tag-enterprise'
            };

            function renderRepos(list) {
                return list.map(r => `
                    <div class="repo-card">
                        <a class="repo-name" href="https://github.com/${r.repo}" target="_blank">${r.repo}</a>
                        <span style="float:right;color:#8b949e">⭐ ${r.stars} | +${r.star_delta_1d}/日 +${r.star_delta_7d}/周 | ${r.score}分</span>
                        <div class="repo-meta">
                            ${(r.labels || []).map(l => `<span class="tag ${tagClass[l] || ''}">${l}</span>`).join('')}
                            ${r.one_liner}
                        </div>
                    </div>
                `).join('');
            }

            document.getElementById('content').innerHTML = `
                <div class="section"><h2>🔥 今日增速 TOP 10</h2>${renderRepos((stats?.top_day || filtered).slice(0, 10))}</div>
                <div class="section"><h2>💥 本周爆发榜</h2>${renderRepos((stats?.top_week || filtered).slice(0, 10))}</div>
                <div class="section"><h2>🌱 潜力新星</h2>${renderRepos((stats?.new_stars || []).slice(0, 10))}</div>
                <p style="color:#8b949e;text-align:center;margin-top:24px">${date}</p>
            `;
        }

        init();
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add web/index.html
git commit -m "feat: static web dashboard"
```

---

### Task 13: 集成验证

- [ ] **Step 1: 验证所有 Python 文件可导入**

```bash
python -c "
from src.config import load_config
from src.store import append_snapshot, read_snapshots, save_json, load_json
from src.scorer import score_growth, score_novelty, score_community, score_authority, score_quality, compute_composite
from src.reporter import generate_daily_report, generate_weekly_report
from src.pusher import push_all
from src.web_exporter import build_panel_data, export_latest
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 2: 运行全部测试**

```bash
python -m pytest tests/ -v
```

Expected: 所有测试 PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: complete integration verification"
```

---
