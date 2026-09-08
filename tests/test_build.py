"""Tests for changelog_agent.build (build_changelog, render_markdown)."""

from __future__ import annotations

from changelog_agent.build import build_changelog, render_markdown
from changelog_agent.models import Commit


def _commit(sha: str, message: str, author: str = "someone") -> Commit:
    return Commit(sha=sha, message=message, author=author, date="2026-08-20T00:00:00Z")


SAMPLE_COMMITS = [
    _commit("1111111aaaa", "feat: add login flow", author="janedoe"),
    _commit("2222222bbbb", "fix: correct null pointer in parser", author="johnsmith"),
    _commit("3333333cccc", "docs: update quickstart guide", author="janedoe"),
    _commit("4444444dddd", "chore: bump requests version", author="botuser"),
    _commit("5555555eeee", "Merge branch 'main' into feature/x", author="johnsmith"),
    _commit("6666666ffff", "feat(api): add rate limiting", author="janedoe"),
]


def test_build_changelog_groups_by_category():
    grouped = build_changelog(SAMPLE_COMMITS)

    assert set(grouped.keys()) == {"feat", "fix", "docs", "chore", "other"}
    assert len(grouped["feat"]) == 2
    assert len(grouped["fix"]) == 1
    assert len(grouped["docs"]) == 1
    assert len(grouped["chore"]) == 1
    assert len(grouped["other"]) == 1


def test_build_changelog_preserves_commit_order_within_category():
    grouped = build_changelog(SAMPLE_COMMITS)

    feat_descriptions = [entry.description for entry in grouped["feat"]]
    assert feat_descriptions == ["add login flow", "add rate limiting"]


def test_build_changelog_entries_have_correct_sha_and_author():
    grouped = build_changelog(SAMPLE_COMMITS)

    fix_entry = grouped["fix"][0]
    assert fix_entry.sha == "2222222bbbb"
    assert fix_entry.author == "johnsmith"
    assert fix_entry.description == "correct null pointer in parser"


def test_build_changelog_omits_empty_categories():
    commits = [_commit("aaa", "feat: only one commit")]
    grouped = build_changelog(commits)
    assert set(grouped.keys()) == {"feat"}
    assert "fix" not in grouped
    assert "other" not in grouped


def test_build_changelog_empty_input_returns_empty_dict():
    assert build_changelog([]) == {}


def test_render_markdown_known_structure():
    grouped = build_changelog(SAMPLE_COMMITS)
    markdown = render_markdown(grouped)

    assert markdown.startswith("# Changelog\n")
    assert "## Features" in markdown
    assert "## Fixes" in markdown
    assert "## Documentation" in markdown
    assert "## Chores" in markdown
    assert "## Other" in markdown


def test_render_markdown_section_order_is_feat_fix_docs_chore_other():
    grouped = build_changelog(SAMPLE_COMMITS)
    markdown = render_markdown(grouped)

    feat_idx = markdown.index("## Features")
    fix_idx = markdown.index("## Fixes")
    docs_idx = markdown.index("## Documentation")
    chore_idx = markdown.index("## Chores")
    other_idx = markdown.index("## Other")

    assert feat_idx < fix_idx < docs_idx < chore_idx < other_idx


def test_render_markdown_entry_line_content():
    grouped = build_changelog(SAMPLE_COMMITS)
    markdown = render_markdown(grouped)

    # "- add login flow (1111111) — janedoe"
    assert "- add login flow (1111111) — janedoe" in markdown


def test_render_markdown_omits_sections_with_no_entries():
    grouped = build_changelog([_commit("aaa", "docs: fix typo in README")])
    markdown = render_markdown(grouped)

    assert "## Documentation" in markdown
    assert "## Features" not in markdown
    assert "## Fixes" not in markdown
    assert "## Chores" not in markdown
    assert "## Other" not in markdown


def test_render_markdown_empty_grouped_dict():
    markdown = render_markdown({})
    assert markdown.startswith("# Changelog")
    assert "_No changes._" in markdown
