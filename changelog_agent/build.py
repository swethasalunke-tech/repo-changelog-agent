"""Builds a categorized changelog from a list of commits."""

from __future__ import annotations

from changelog_agent.categorizer import categorize_commit
from changelog_agent.models import Category, ChangelogEntry, Commit

# Fixed display order and section headings. "other" is deliberately listed
# last since it's the catch-all bucket for anything that doesn't match a
# known Conventional Commits prefix.
CATEGORY_ORDER: list[Category] = ["feat", "fix", "docs", "chore", "other"]

CATEGORY_HEADINGS: dict[Category, str] = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Documentation",
    "chore": "Chores",
    "other": "Other",
}


def build_changelog(commits: list[Commit]) -> dict[str, list[ChangelogEntry]]:
    """Categorize each commit and group the resulting entries by category.

    Returns a dict keyed by category name ("feat", "fix", "docs", "chore",
    "other"). Only categories that have at least one entry are included.
    Within each category, entries preserve the order of the input commits.
    """
    grouped: dict[str, list[ChangelogEntry]] = {}

    for commit in commits:
        entry = categorize_commit(commit)
        grouped.setdefault(entry.category, []).append(entry)

    return grouped


def render_markdown(grouped: dict[str, list[ChangelogEntry]]) -> str:
    """Render a grouped changelog dict as a Markdown document.

    Produces one `## <Heading>` section per non-empty category, in a fixed
    order (feat, fix, docs, chore, other), with each entry rendered as a
    bullet: `- <description> (<sha short>) — <author>`.
    """
    lines: list[str] = ["# Changelog", ""]

    any_section = False
    for category in CATEGORY_ORDER:
        entries = grouped.get(category)
        if not entries:
            continue

        any_section = True
        lines.append(f"## {CATEGORY_HEADINGS[category]}")
        lines.append("")
        for entry in entries:
            short_sha = entry.sha[:7] if entry.sha else "unknown"
            lines.append(f"- {entry.description} ({short_sha}) — {entry.author}")
        lines.append("")

    if not any_section:
        lines.append("_No changes._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
