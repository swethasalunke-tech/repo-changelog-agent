"""Classifies commits into changelog categories using Conventional Commits style prefixes.

Only the *first line* (subject) of the commit message is inspected, and only a
strict, anchored prefix counts as a match. This deliberately avoids a naive
`"fix" in commit.message` substring check, which would misclassify a commit
like:

    "Refactor the login form\n\nThis does not fix the auth bug yet, that is
    tracked separately."

as a "fix" commit just because the word appears in the body. The regex below
only matches when the *first line* begins with one of the known type tokens,
optionally followed by a parenthesized scope and/or a breaking-change `!`,
followed by a colon and whitespace.
"""

from __future__ import annotations

import re

from changelog_agent.models import Category, ChangelogEntry, Commit

# Conventional Commit subject line:
#   <type>(<optional scope>)(<optional !>): <description>
# Examples that match:
#   "feat: add login"
#   "Fix(auth): handle expired tokens"
#   "docs(readme)!: rewrite quickstart"
# Examples that do NOT match:
#   "fixup some typo"          (no colon right after the type token)
#   "This will fix the bug"    (type token not at the start of the line)
#   "prefixed: not a real type" ("prefixed" is not one of the known types)
_PREFIX_RE = re.compile(
    r"^\s*(?P<type>feat|fix|docs|chore)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<description>.+)$",
    re.IGNORECASE,
)

_KNOWN_CATEGORIES: set[str] = {"feat", "fix", "docs", "chore"}


def categorize_commit(commit: Commit) -> ChangelogEntry:
    """Classify a single commit into a ChangelogEntry.

    Parses the first line of `commit.message` for a Conventional Commits
    style prefix (`feat:`, `fix(scope):`, `docs!:`, etc.), case-insensitively.
    Anything that doesn't match a known prefix falls back to category
    "other", using the full first line as the description.
    """
    subject = commit.message.strip().splitlines()[0].strip() if commit.message.strip() else ""

    if not subject:
        return ChangelogEntry(
            category="other",
            description="(empty commit message)",
            sha=commit.sha,
            author=commit.author,
        )

    match = _PREFIX_RE.match(subject)
    if match:
        commit_type = match.group("type").lower()
        if commit_type in _KNOWN_CATEGORIES:
            category: Category = commit_type  # type: ignore[assignment]
            description = match.group("description").strip()
            return ChangelogEntry(
                category=category,
                description=description,
                sha=commit.sha,
                author=commit.author,
            )

    return ChangelogEntry(
        category="other",
        description=subject,
        sha=commit.sha,
        author=commit.author,
    )
