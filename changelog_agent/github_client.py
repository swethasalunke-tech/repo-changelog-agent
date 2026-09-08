"""GitHub commit-history clients.

Two implementations share the `GitHubClient` Protocol:

- `RealGitHubClient` calls the real GitHub REST API
  (`GET /repos/{owner}/{repo}/compare/{base}...{head}`) via `requests.get`.
  Its request construction and response parsing are covered by unit tests
  that mock `requests.get` (see tests/test_github_client.py). IMPORTANT:
  as of this writing, `RealGitHubClient` has NOT been exercised against the
  live GitHub API from this build sandbox, which has no outbound network
  access to api.github.com. See README.md for details.

- `FakeGitHubClient` returns `Commit` objects built from a bundled fixture
  file (`data/sample_commits.json`) so the categorizer and build logic can
  be tested end-to-end without any network access at all.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import requests

from changelog_agent.models import Commit

GITHUB_API_BASE_URL = "https://api.github.com"

_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_commits.json"


class GitHubClientError(RuntimeError):
    """Raised when a GitHub API request fails or returns an unexpected response."""


class GitHubClient(Protocol):
    """Interface both the real and fake GitHub clients implement."""

    def list_commits(self, owner: str, repo: str, base: str, head: str) -> list[Commit]:
        """Return the commits between `base` and `head` on `owner/repo`."""
        ...


class RealGitHubClient:
    """GitHubClient backed by the real GitHub REST API.

    Uses the "compare" endpoint so commit history between two refs (branches,
    tags, or SHAs) can be fetched in a single request:

        GET /repos/{owner}/{repo}/compare/{base}...{head}

    NOTE: this class has not been exercised against api.github.com in this
    build sandbox (no outbound network access here). Its URL construction,
    auth header handling, and response parsing are covered by tests that
    mock `requests.get` — see tests/test_github_client.py.
    """

    def __init__(self, token: str | None = None, base_url: str = GITHUB_API_BASE_URL, timeout: float = 30.0) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-changelog-agent",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def list_commits(self, owner: str, repo: str, base: str, head: str) -> list[Commit]:
        url = f"{self.base_url}/repos/{owner}/{repo}/compare/{base}...{head}"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)

        if response.status_code != 200:
            raise GitHubClientError(
                f"GitHub API request failed: GET {url} returned "
                f"{response.status_code}: {response.text}"
            )

        payload = response.json()
        raw_commits = payload.get("commits", [])

        commits: list[Commit] = []
        for raw in raw_commits:
            sha = raw.get("sha", "")
            git_commit = raw.get("commit", {}) or {}
            message = git_commit.get("message", "")

            # Prefer the linked GitHub username when available, otherwise
            # fall back to the raw git commit author name.
            github_author = raw.get("author") or {}
            author = github_author.get("login") or git_commit.get("author", {}).get("name", "unknown")

            date = git_commit.get("author", {}).get("date", "")

            commits.append(Commit(sha=sha, message=message, author=author, date=date))

        return commits


class FakeGitHubClient:
    """GitHubClient backed by a bundled JSON fixture, for offline testing.

    Ignores owner/repo/base/head (the fixture is not ref-aware) and simply
    returns every commit recorded in data/sample_commits.json.
    """

    def __init__(self, fixture_path: Path | str = _FIXTURE_PATH) -> None:
        self.fixture_path = Path(fixture_path)

    def list_commits(self, owner: str, repo: str, base: str, head: str) -> list[Commit]:
        with open(self.fixture_path, encoding="utf-8") as f:
            raw_commits = json.load(f)

        return [
            Commit(
                sha=entry["sha"],
                message=entry["message"],
                author=entry["author"],
                date=entry["date"],
            )
            for entry in raw_commits
        ]
