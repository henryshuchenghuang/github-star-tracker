---
name: analyze-trending-weekly
description: 分析本周 GitHub 趋势，生成汇总周报
user-invocable: true
---

读取 `data/candidates.json` 和本周的 `data/snapshots.jsonl`。

用 Claude 分析本周整体趋势：

1. **赛道分析**：哪些赛道在升温，哪些在降温
2. **深度点评**：选出 3-5 个最值得关注的项目做深度点评
3. **风险评估**：标记可疑项目

生成周报写入 `reports/`，运行 `python src/main.py --weekly` 推送。

用中文回复。
