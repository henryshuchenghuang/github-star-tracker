# CLAUDE.md

## ⚠️ 最高优先级：称呼规则

**每次回复的开头必须称呼用户为「老大」。** 无论回复内容长短，第一个词必须是「老大。」。
如果忘记称呼就是失焦了，用户会手动重置上下文焦点。

---

## 项目概述

半自动化追踪 GitHub 上最热、增长最快、最有价值的开源项目。阶段一由 GitHub Actions + Python 定时抓取评分，阶段二由 Claude Code 手工复核并生成日报。

## 核心架构

```
阶段一（GitHub Actions，云端永续）          阶段二（本地 Claude Code，手动触发）
Actions 每 6h → Python fetcher/scorer     git pull → Claude 读 candidates.json
    → 写 data/*.jsonl                       → 定性复核
    → git commit + push                     → 生成日报 + 推送三渠道
```

## 目录结构

```
├── .claude/                  # Claude Code 配置
├── .github/workflows/        # GitHub Actions 定时调度
├── data/                     # JSONL 快照 + 候选 JSON（Git 追踪，阶段间数据桥）
├── reports/                  # 日报 Markdown（不提交 Git）
├── web/                      # 静态 Web 面板
│   ├── index.html
│   └── data/                 # JSON 快照（不提交 Git）
└── src/                      # Python 源码
    ├── main.py               # 入口
    ├── fetcher.py            # GitHub API 数据抓取
    ├── scorer.py             # 五维度评分引擎
    ├── reporter.py           # Markdown 日报生成
    ├── pusher.py             # 推送（邮箱/微信/飞书）
    ├── web_exporter.py       # 导出 JSON 供 Web 面板
    └── config.yaml           # 敏感配置（不提交 Git）
```

## 五维度评分

| 维度 | 权重 | 说明 |
|------|------|------|
| 增长信号 | 0.35 | star 增量/加速度、fork 增量 |
| 新颖度 | 0.20 | 新项目发现、Topic 稀有度 |
| 社区健康 | 0.25 | 贡献者活跃度、Issue 响应、PR 合并率 |
| 权威背书 | 0.10 | 知名组织、GitHub Collections |
| 内容质量 | 0.10 | README 完善度、commit 连续性、License |

## 推送渠道

- 邮箱：Resend API
- 微信：Server酱 / PushPlus
- 飞书：机器人 Webhook

## 技术栈

- Python（数据抓取、评分、推送）
- JSONL 文本存储（Git 友好、可 diff）
- GitHub Actions（云端定时调度，永不停机）
- Claude Code（AI 复核分析）
- 纯静态 HTML（Web 面板，GitHub Pages 部署）

## 日常操作流程

```
早上开机 → git pull → Claude Code: /analyze-trending → 复核推送
每周日 → /analyze-trending --weekly → 生成周报
```

## candidates.json 分层读取策略（Token 优化）

Claude 阶段二只读摘要层扫描全局（50 项目约 5-6K token）。发现可疑项目时按需展开详情层。比一次性读全部完整数据节省 70%+ token。
