"""GitHub scanner - finds relevant repositories and discussions."""

import httpx

from pros.src.opportunity.scanners.base import BaseScanner, ScanResult


class GitHubScanner(BaseScanner):
    """Scans GitHub for relevant repositories and issues."""
    
    name = "github"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=30.0,
        )
    
    async def scan(self, user_id: str) -> list[ScanResult]:
        """Scan GitHub for relevant repositories."""
        results = []
        
        # Search for trending repos in relevant topics
        topics = [
            "technology-transfer",
            "deep-tech",
            "biotech",
            "manufacturing",
            "automation",
        ]
        
        for topic in topics:
            try:
                topic_results = await self._search_repos(topic)
                results.extend(topic_results)
            except Exception as e:
                print(f"GitHub search failed for {topic}: {e}")
                continue
        
        return results
    
    async def _search_repos(self, topic: str) -> list[ScanResult]:
        """Search GitHub repos by topic."""
        response = await self.client.get(
            "/search/repositories",
            params={
                "q": f"topic:{topic}",
                "sort": "stars",
                "order": "desc",
                "per_page": 10,
            }
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        results = []
        
        for repo in data.get("items", []):
            results.append(ScanResult(
                url=repo["html_url"],
                title=repo["full_name"],
                description=repo.get("description", ""),
                source="github",
                author=repo["owner"]["login"],
                topics=repo.get("topics", []),
                engagement={
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                },
                metadata={
                    "language": repo.get("language"),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                },
            ))
        
        return results
    
    async def search_issues(self, query: str) -> list[ScanResult]:
        """Search GitHub issues."""
        response = await self.client.get(
            "/search/issues",
            params={
                "q": f"{query} is:issue is:open",
                "sort": "created",
                "order": "desc",
                "per_page": 10,
            }
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        results = []
        
        for issue in data.get("items", []):
            # Extract repo name from URL
            parts = issue["repository_url"].split("/")
            repo_name = f"{parts[-2]}/{parts[-1]}"
            
            results.append(ScanResult(
                url=issue["html_url"],
                title=f"{repo_name}: {issue['title']}",
                description=issue.get("body", "")[:500],
                source="github",
                author=issue["user"]["login"],
                metadata={
                    "repo": repo_name,
                    "labels": [l["name"] for l in issue.get("labels", [])],
                    "comments": issue.get("comments", 0),
                },
            ))
        
        return results
