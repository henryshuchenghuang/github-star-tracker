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
        """获取全时段贡献者数量（估算，上限 100 人）"""
        repo = self.client.get_repo(full_name)
        try:
            contributors = repo.get_contributors()
            return sum(1 for _ in contributors[:100])
        except Exception:
            return 0

    def search_all_time_top_repos(self, min_stars=500):
        """搜索全 GitHub 历史星数最高的仓库（不限创建时间）。"""
        query = f"stars:>{min_stars}"
        langs = self.config["tracking"].get("languages", ["all"])
        if "all" not in langs:
            lang_filter = " OR ".join(f"language:{l}" for l in langs)
            query += f" ({lang_filter})"
        repos = self.client.search_repositories(query=query, sort="stars", order="desc")
        return list(repos[:self.config["tracking"]["top_n_candidates"]])

    def get_issue_stats(self, full_name):
        """获取 Issue 统计"""
        repo = self.client.get_repo(full_name)
        open_count = repo.open_issues_count
        return {"open_issues": open_count}
