import os
from github import Github
from datetime import datetime
from .base import BaseCollector

class GitHubCollector(BaseCollector):
    def __init__(self, product_name, repo_name):
        super().__init__(product_name)
        self.repo_name = repo_name
        self.token = os.getenv('GITHUB_TOKEN')

    def collect(self):
        g = Github(self.token) if self.token else Github()
        repo = g.get_repo(self.repo_name)
        
        updates = []
        
        # Collect Releases
        releases = repo.get_releases()
        for release in releases[:10]: # Fetch last 10 releases
            updates.append(self.standardize_update(
                title=f"Release: {release.tag_name} - {release.title}",
                content=release.body,
                source_type='github',
                source_url=release.html_url,
                publish_time=release.created_at,
                raw_data={
                    "tag_name": release.tag_name,
                    "target_commitish": release.target_commitish,
                    "draft": release.draft,
                    "prerelease": release.prerelease
                }
            ))
            
        # Collect recent commits to main branch if no releases recently
        if not updates:
            commits = repo.get_commits()
            for commit in commits[:5]:
                commit_data = commit.commit
                updates.append(self.standardize_update(
                    title=f"Commit: {commit_data.message.splitlines()[0]}",
                    content=commit_data.message,
                    source_type='github',
                    source_url=commit.html_url,
                    publish_time=commit_data.author.date,
                    raw_data={
                        "sha": commit.sha,
                        "author": commit_data.author.name
                    }
                ))
                
        return updates
