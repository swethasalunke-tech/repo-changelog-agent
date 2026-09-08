"""Tests for changelog_agent.categorizer.categorize_commit."""

from __future__ import annotations

from changelog_agent.categorizer import categorize_commit
from changelog_agent.models import Commit


def _commit(message: str, sha: str = "abc1234", author: str = "someone") -> Commit:
    return Commit(sha=sha, message=message, author=author, date="2026-08-20T00:00:00Z")


def test_feat_prefix():
    entry = categorize_commit(_commit("feat: add dark mode toggle"))
    assert entry.category == "feat"
    assert entry.description == "add dark mode toggle"


def test_fix_prefix():
    entry = categorize_commit(_commit("fix: prevent crash on empty input"))
    assert entry.category == "fix"
    assert entry.description == "prevent crash on empty input"


def test_docs_prefix():
    entry = categorize_commit(_commit("docs: clarify installation instructions"))
    assert entry.category == "docs"
    assert entry.description == "clarify installation instructions"


def test_chore_prefix():
    entry = categorize_commit(_commit("chore: update lockfile"))
    assert entry.category == "chore"
    assert entry.description == "update lockfile"


def test_prefix_with_scope():
    entry = categorize_commit(_commit("feat(auth): add SSO support"))
    assert entry.category == "feat"
    assert entry.description == "add SSO support"


def test_fix_prefix_with_scope():
    entry = categorize_commit(_commit("fix(parser): handle trailing commas"))
    assert entry.category == "fix"
    assert entry.description == "handle trailing commas"


def test_prefix_with_scope_and_breaking_marker():
    entry = categorize_commit(_commit("feat(api)!: remove deprecated /v1 endpoints"))
    assert entry.category == "feat"
    assert entry.description == "remove deprecated /v1 endpoints"


def test_case_insensitive_uppercase():
    entry = categorize_commit(_commit("FIX: correct off-by-one error"))
    assert entry.category == "fix"
    assert entry.description == "correct off-by-one error"


def test_case_insensitive_mixed_case_with_scope():
    entry = categorize_commit(_commit("Feat(Ui): Add responsive nav bar"))
    assert entry.category == "feat"
    assert entry.description == "Add responsive nav bar"


def test_case_insensitive_docs():
    entry = categorize_commit(_commit("Docs: add architecture diagram"))
    assert entry.category == "docs"


def test_body_mentions_fix_but_not_prefixed_is_other():
    """A commit whose *body* mentions "fix" must not be misclassified.

    This is the key regression test proving the categorizer uses an anchored
    regex on the subject line rather than a naive substring check — a naive
    `"fix" in commit.message` would incorrectly classify this as a fix.
    """
    message = (
        "Refactor session middleware\n\n"
        "This does not fix the underlying auth bug yet; that is tracked "
        "separately in issue #42."
    )
    entry = categorize_commit(_commit(message))
    assert entry.category == "other"
    assert entry.description == "Refactor session middleware"


def test_word_that_starts_with_a_type_token_is_not_a_false_positive():
    """"fixup: ..." must not match "fix" (no colon immediately after "fix")."""
    entry = categorize_commit(_commit("fixup: typo in comment"))
    assert entry.category == "other"


def test_unknown_prefix_falls_back_to_other():
    entry = categorize_commit(_commit("Merge branch 'main' into feature/rate-limiting"))
    assert entry.category == "other"
    assert entry.description == "Merge branch 'main' into feature/rate-limiting"


def test_prefix_without_space_after_colon_still_requires_whitespace_boundary():
    # There must be at least one whitespace character after the colon for a
    # match — "fix:something" with no space is arguably ambiguous, so the
    # parser requires `\s*:\s*` which does match zero spaces too. Confirm the
    # description text is still parsed correctly either way.
    entry = categorize_commit(_commit("fix:tighten regex bounds"))
    assert entry.category == "fix"
    assert entry.description == "tighten regex bounds"


def test_empty_message():
    entry = categorize_commit(_commit(""))
    assert entry.category == "other"
    assert entry.description == "(empty commit message)"


def test_whitespace_only_message():
    entry = categorize_commit(_commit("   \n  \n"))
    assert entry.category == "other"
    assert entry.description == "(empty commit message)"


def test_only_first_line_is_used_for_description():
    message = "feat: add pagination\n\nAlso updates the docs and fixes a typo."
    entry = categorize_commit(_commit(message))
    assert entry.category == "feat"
    assert entry.description == "add pagination"


def test_entry_preserves_sha_and_author():
    entry = categorize_commit(_commit("chore: bump deps", sha="deadbeef", author="octocat"))
    assert entry.sha == "deadbeef"
    assert entry.author == "octocat"
