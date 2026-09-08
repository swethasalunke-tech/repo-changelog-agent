"""Core data model for repo-changelog-agent.

These dataclasses are intentionally small and dependency-free so they can be
shared between the GitHub client, the categorizer, and the changelog builder
without any of those modules needing to import each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Category = Literal["feat", "fix", "docs", "chore", "other"]


@dataclass(frozen=True)
class Commit:
    """A single commit as returned by the GitHub API (or a fixture)."""

    sha: str
    message: str
    author: str
    date: str  # ISO 8601 string, e.g. "2026-08-20T14:03:00Z"


@dataclass(frozen=True)
class ChangelogEntry:
    """A commit that has been classified into a changelog category."""

    category: Category
    description: str
    sha: str
    author: str
