---
name: analyze-trending
description: 分析 GitHub 开源项目趋势，生成日报并推送
user-invocable: true
---

读取 `data/candidates.json`。先扫描 `summary` 层的 TOP-50 候选项目，识别以下情况：

1. **刷 star 嫌疑**：star/fork 比异常、contributor 几乎为零的项目
2. **套壳项目**：README 空洞、实质代码极少
3. **真正值得关注但评分偏低的项目**：赛道新颖、技术扎实但低调的项目

对可疑项目展开 `details` 层查看详情。

过滤完后生成日报 Markdown 写入 `reports/`，同时运行 `python src/main.py --report` 导出 Web JSON。

将日报推送到已启用的渠道（邮箱/微信/飞书），运行 `python src/main.py --push`。

用中文回复。
