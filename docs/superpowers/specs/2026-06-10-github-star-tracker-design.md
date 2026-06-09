# GitHub 开源项目追踪系统 — 设计文档

**日期**: 2026-06-10  
**状态**: 草案（已修订）

## 概述

一套半自动化的 GitHub 开源项目追踪系统。从五个维度（增长信号、新颖度、社区健康度、权威背书、内容质量）评估项目价值，通过邮箱/微信/飞书推送结构化日报，并提供静态 Web 面板支持历史浏览和趋势探索。

阶段一由 GitHub Actions 定时抓取评分，数据通过 Git 传递；阶段二由用户在本地 Claude Code 中手动触发复核并推送。

## 架构

```
阶段一（GitHub Actions，永不停机）                阶段二（本地 Claude Code，手动触发）

┌──────────────────┐    ┌──────────┐
│  GitHub Actions   │───▶│  Python  │───┐
│  每 6 小时触发     │    │  脚本     │   │
└──────────────────┘    └──────────┘   │
                                       │ git commit + push
                                       ▼
                                ┌──────────────┐          ┌──────────────┐
                                │ data/*.jsonl │          │  Claude Code  │
                                │ candidates   │───────▶│  复核分析      │
                                │ profiles     │ git pull│  生成日报      │
                                └──────────────┘  用户    └──────┬───────┘
                                   拉取最新数据                    │
                                                   ┌─────────────┼─────────────┐
                                                   ▼             ▼             ▼
                                                ┌──────┐    ┌──────┐    ┌──────┐
                                                │ 邮箱  │    │ 微信  │    │ 飞书  │
                                                └──────┘    └──────┘    └──────┘
```

- **阶段一（自动）**：GitHub Actions 每 6 小时触发。Python 脚本从 GitHub API 抓取数据，计算定量评分，写入 `data/snapshots.jsonl`（快照）、`data/profiles.json`（项目档案）、`data/candidates.json`（TOP-50 候选）。最后 `git commit & push` 到仓库。
- **阶段二（手动）**：用户开机后 `git pull` 拉取最新数据，在 Claude Code 中运行分析命令。Claude 读取候选列表进行定性复核，生成日报并推送到三个渠道。

## 为什么用 JSONL 而非 SQLite

放弃 SQLite，改用 JSON 文本文件：

- **Git 友好**：JSONL 逐行追加，`git diff` 清晰可读；SQLite 二进制文件无法 diff
- **追加无冲突**：GitHub Actions 多个 run 之间不会出现写入冲突
- **Python 读写简单**：逐行追加/读取，无需 ORM
- **Claude 直读**：`candidates.json` 直接给 Claude 消费，无需额外转换

## 项目目录结构

```
004_Github-star-search/
├── .claude/                       # Claude Code 配置
├── .github/workflows/
│   └── track.yml                  # GitHub Actions 定时调度
├── data/
│   ├── snapshots.jsonl            # 仓库快照（每行一个 JSON 对象，逐行追加）
│   ├── profiles.json              # 项目档案（JSON 对象，缓慢变化）
│   ├── candidates.json            # 阶段一产出，阶段二输入
│   └── reports_index.json         # 日报索引
├── reports/
│   ├── 2026-06/
│   │   ├── 2026-06-10.md
│   │   └── weekly-2026-W24.md
│   └── archive/
├── web/
│   ├── index.html                 # 静态 Web 面板
│   └── data/
│       ├── latest.json
│       └── archive/
│           ├── 2026-06-10.json
│           └── ...
├── src/
│   ├── main.py                    # 入口脚本
│   ├── fetcher.py                 # GitHub API 数据抓取
│   ├── scorer.py                  # 五维度评分引擎
│   ├── reporter.py                # Markdown 日报生成
│   ├── pusher.py                  # 推送（邮箱/微信/飞书）
│   ├── web_exporter.py            # 导出 JSON 供 Web 面板使用
│   └── config.example.yaml        # 配置模板
├── requirements.txt
├── .gitignore
└── CLAUDE.md
```

## 五维度评分体系

### 一、增长信号（权重 0.35）

- 日/周/月 star 增量排行
- star 加速度（本周增量 vs 上周增量），识别二次爆发
- fork 增量

### 二、新颖度（权重 0.20）

- 创建时间 ≤ 90 天 且 已破 500 star → 标记为「潜力新星」
- GitHub Topic 标签稀有度（新赛道信号）
- 创建者是否首次开源

### 三、社区健康度（权重 0.25）

- 近 30 天独立贡献者数量
- Issue 首次回复中位时间
- PR 合并率
- Bus Factor：是否有 ≥3 个高活跃贡献者（避免单人项目突然弃坑）

### 四、权威背书（权重 0.10）

- 仓库属于知名组织（Google、Meta、Anthropic、ByteDance 等维护的可配置白名单）
- 出现在 GitHub Collections 中
- Hacker News 提及次数（通过 Algolia HN Search API，免费，不计 GitHub API 配额）

### 五、内容质量（权重 0.10）

- README 完善度（字数、是否多语言、是否有 Demo/截图）
- 近期 commit 连续性（排除「一周爆火然后停更」的项目）
- License 是否为真正的开源协议（排除无 License 的假开源）

### 综合评分

```
Score = 增长信号×0.35 + 新颖度×0.20 + 社区健康×0.25 + 权威背书×0.10 + 内容质量×0.10
```

日报中每个项目附带综合评分和精简标签：`🔥爆发中` `🌱新星` `✅高质量` `🏢大厂背书`。

## 数据结构

### snapshots.jsonl — 仓库快照（每行一条）

```json
{
  "repo": "anthropics/skills",
  "time": "2026-06-10T14:00:00Z",
  "stars": 101200,
  "star_delta_1d": 320,
  "star_delta_7d": 2400,
  "star_acceleration": 1.35,
  "forks": 5200,
  "fork_delta_1d": 15,
  "open_issues": 42,
  "contributors_30d": 28,
  "issue_response_h": 3.2,
  "pr_merge_rate": 0.88,
  "score": 87.5,
  "labels": ["🔥爆发中", "🏢大厂背书"]
}
```

关键字段全部由 Python 预计算，Claude 直接读取不做算术。

### profiles.json — 项目档案

```json
{
  "anthropics/skills": {
    "created_at": "2025-03-15T00:00:00Z",
    "owner_type": "org",
    "topics": ["ai", "agent", "claude"],
    "license": "MIT",
    "readme_score": 85,
    "language": "Python",
    "first_seen_at": "2025-11-01T00:00:00Z"
  }
}
```

### candidates.json — 候选列表（分层结构，Token 优先设计）

```
摘要层（Claude 一次性加载，50 项目约 5-6K token）
┌──────────────────────────────────────────────────────────┐
│ {                                                        │
│   "generated_at": "2026-06-10T14:00:00Z",                │
│   "candidates": [                                        │
│     {                                                    │
│       "rank": 1,                                         │
│       "repo": "bytedance/deer-flow",                     │
│       "stars": 41200,                                    │
│       "star_delta_7d": 5200,                             │
│       "score": 92.3,                                     │
│       "labels": ["🔥爆发中","🏢大厂背书","🌱新星"],         │
│       "one_liner": "字节开源的 SuperAgent 框架，           │
│                     本周 star 增速 320%，7 天破 5000"      │
│     },                                                   │
│     ... (共 50 条)                                        │
│   ]                                                      │
│ }                                                        │
└──────────────────────────────────────────────────────────┘
                              │
       用户要求深入看某个项目时  │
                              ▼
┌─ 详情层（按需读取，单项目约 300-500 token）─────────────────┐
│ {                                                          │
│   "repo": "bytedance/deer-flow",                           │
│   "readme_summary": "DeerFlow 是一个基于多 Agent 协作的     │
│       工作流自动化框架，支持可视化编排和代码级扩展...",         │
│   "commit_trend": "近 30 天日均 8.3 commits，12 位活跃贡献者",│
│   "community": {                                           │
│     "issue_response_h": 2.1,                               │
│     "pr_merge_rate": 0.92,                                 │
│     "bus_factor": 5                                        │
│   },                                                       │
│   "risk_note": "项目仅创建 45 天，API 仍在变动中"            │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
```

Claude 默认只读摘要层扫描全局。发现可疑项目或排名异常时，才展开详情层深入分析。比一次性塞 50 个完整项目节省 70%+ token。

## 数据文件格式

### candidates.json 顶层结构

```json
{
  "generated_at": "ISO 8601",
  "total_candidates": 50,
  "summary": [
    {
      "rank": 1,
      "repo": "owner/name",
      "stars": 12345,
      "star_delta_1d": 120,
      "star_delta_7d": 850,
      "score": 92.3,
      "labels": ["🔥爆发中", "🏢大厂背书"],
      "one_liner": "一句话概括项目内容和本周表现"
    }
  ],
  "details": {
    "owner/name": {
      "readme_summary": "≤200 字 README 摘要",
      "commit_trend": "commit 活跃度描述",
      "community": {
        "issue_response_h": 2.1,
        "pr_merge_rate": 0.92,
        "bus_factor": 5
      },
      "risk_note": "注意事项或留空"
    }
  }
}
```

## API 调用预算

GitHub API 免费额度为 5000 次/小时。单轮抓取估算：

| 环节 | 次数 | 说明 |
|------|:----:|------|
| 搜索（多条件组合） | 10 | 按时间+语言+star 范围搜索 |
| 仓库详情（批量） | 10 | 每批 20 个，补充 stars/forks/topics |
| 社区指标 | 15 | Issues/PR/contributors 统计 |
| 已有项目增量更新 | 10 | 更新之前关注的仓库最新数据 |
| **合计/轮** | **45** | |

每天 4 轮（每 6 小时）共约 180 次，远低于每小时的 5000 次上限。

HN 检测通过 Algolia HN Search API（`hn.algolia.com/api`），免费且不计 GitHub API 配额。

## 推送渠道

| 渠道 | 实现方式 | 成本 |
|------|---------|------|
| **邮箱** | Resend API 或 SMTP | 免费额度 |
| **微信** | Server酱 / PushPlus / WxPusher | 免费 |
| **飞书** | 机器人 Webhook API | 免费 |

## 配置结构

```yaml
# GitHub
github_token: "ghp_xxx"

# 追踪配置
tracking:
  languages: ["all"]             # 关注的语言，具体列表如 ["python","go","rust","typescript"]
  min_stars: 100                 # 最低 star 门槛
  new_repo_days: 90              # 多久以内算"新项目"
  new_repo_min_stars: 500        # 新项目最低 star 阈值
  top_n_candidates: 50           # 候选列表数量
  org_whitelist:                 # 权威背书：知名组织名单
    - google
    - meta
    - anthropic
    - bytedance
    - alibaba
    - microsoft
    - apple

# 推送渠道
push:
  email:
    enabled: true
    provider: resend             # resend | smtp
    api_key: ""
    from: "tracker@example.com"
    to: "your@email.com"
  wechat:
    enabled: true
    provider: serverchan         # serverchan | pushplus | wxpusher
    token: ""
  feishu:
    enabled: true
    webhook_url: ""
```

## 数据保留策略

| 数据类型 | 保留周期 | 清理方式 |
|---------|---------|---------|
| `snapshots.jsonl` | 180 天 | Python 脚本每次运行后裁剪超期行 |
| `profiles.json` | 永久（很小） | 不主动清理 |
| `candidates.json` | 只保留最新 | 每次覆盖 |
| `reports/*.md` | 永久 | 超过 12 个月的移入 `archive/` |
| `web/data/archive/*.json` | 90 天 | 超过的自动删除 |

## 错误降级策略

```
单次抓取失败？
├── GitHub API 限流（429）
│   → 等待 60 秒重试，最多 3 次
│   → 仍失败则跳过本轮，保留上一次 candidates.json
│
├── 单个仓库详情获取失败
│   → 跳过该仓库，在 candidates.json 中标记 "detail_error": true
│   → Claude 阶段收到提示「该条目数据不完整」
│
├── 某个维度数据不可用（如 issue API 无权限）
│   → 该维度权重临时置 0，其余维度权重等比放大
│   → 确保仍能产出有效评分
│
└── 全部不可用（网络故障等）
    → 跳过本轮，推送一条简短「今日数据未更新」通知到渠道
```

核心原则：**降级但不中断**，一次失败不影响整体流程。

## Web 面板

纯静态 HTML + JSON，可部署到 GitHub Pages 或本地浏览器直接打开。

功能：
- **今日总览** — 加载 `latest.json`，展示最新一期三个板块（最热 / 增速最快 / 潜力新星）
- **历史浏览** — 左侧日期列表，点击切换加载对应 `archive/` 下的 JSON
- **趋势对比** — 选择两个日期，对比同一项目的 star 排名变化
- **搜索** — 按项目名或标签搜索，跨所有存档聚合结果

## 日报与周报

### 日报板块

| 板块 | 内容 |
|------|------|
| 今日增速 TOP 10 | 过去 24h star 增量最高的项目 |
| 本周爆发榜 | 过去 7 天 star 增量最高的项目 |
| 潜力新星 | 新创建且增长强劲的项目（Claude 精选点评） |
| 里程碑关注 | 接近或突破 1K/10K/50K/100K 里程碑的项目 |

### 周报（周日生成，日报的超集）

| 周报独有板块 | 说明 |
|-------------|------|
| 本周 TOP 10 增速榜 | 带增速曲线简述 |
| 本周最值得关注 | Claude 精选 3-5 个项目做深度点评 |
| 赛道趋势观察 | 什么方向在升温、什么在降温 |
| 下周期待 | 接近爆发点的项目值得提前关注 |

## 调度与部署

### 阶段一：GitHub Actions（自动）

```yaml
# .github/workflows/track.yml
on:
  schedule:
    - cron: '0 */6 * * *'   # 每 6 小时：抓取 + 评分
    - cron: '0 1 * * *'     # 每天北京时间 9 点：生成待复核数据

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python src/main.py --fetch
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "data: auto snapshot $(date -Iminutes)"
          git push
```

### 阶段二：Claude Code（手动）

用户日流程：
```
1. git pull（拉取阶段一最新数据）
2. Claude Code 中运行 /analyze-trending
3. Claude 读取 candidates.json → 复核 → 生成日报 → 推送三渠道
```

也可以运行 `/analyze-trending --weekly` 生成周报。

## Git 管理

- `data/`、`reports/`、`web/data/` → `.gitignore`（自动生成内容，不提交）
- `src/`、`.github/`、`web/index.html` → 提交
- `config.yaml` → `.gitignore`，提供 `config.example.yaml` 模板提交

> **注意**：`data/` 用于阶段一产出和阶段二输入，如果不放在 Git 里，可以通过 GitHub Actions 直接 push data 文件到一个独立分支或使用 Artifacts。但上面设计是 commit data 到仓库，所以 data/ 不加入 .gitignore。

## 迁移与可移植性

整个项目自包含在目录内，无外部数据库服务或云依赖。拷贝目录、安装依赖即可运行。
