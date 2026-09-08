"""Tests for changelog_agent.github_client.

FakeGitHubClient is tested directly against the bundled fixture file.

RealGitHubClient is tested by mocking `requests.get` — this exercises the
real request-construction and response-parsing code paths without making
any actual network calls. This sandbox has no outbound network access to
api.github.com, so these tests are the only verification RealGitHubClient
has received so far. See README.md for the honest caveat.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from changelog_agent.github_client import FakeGitHubClient, GitHubClientError, RealGitHubClient
from changelog_agent.models import Commit


# ---------------------------------------------------------------------------
# FakeGitHubClient
# ---------------------------------------------------------------------------


def test_fake_client_returns_all_fixture_commits():
    client = FakeGitHubClient()
    commits = client.list_commits("someowner", "somerepo", "main", "feature-branch")
    assert len(commits) == 10


def test_fake_client_returns_commit_objects_with_expected_shape():
    client = FakeGitHubClient()
    commits = client.list_commits("someowner", "somerepo", "main", "feature-branch")

    first = commits[0]
    assert isinstance(first, Commit)
    assert first.sha
    assert first.message
    assert first.author
    assert first.date


def test_fake_client_ignores_ref_arguments_and_is_deterministic():
    client = FakeGitHubClient()
    commits_a = client.list_commits("owner1", "repo1", "v1.0.0", "v1.1.0")
    commits_b = client.list_commits("owner2", "repo2", "main", "dev")
    assert commits_a == commits_b


# ---------------------------------------------------------------------------
# RealGitHubClient — request construction (mocked)
# ---------------------------------------------------------------------------


def _mock_compare_response(status_code: int = 200, commits: list[dict] | None = None, text: str = ""):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    if commits is not None:
        mock_response.json.return_value = {"commits": commits}
    return mock_response


@patch("changelog_agent.github_client.requests.get")
def test_real_client_builds_correct_compare_url(mock_get):
    mock_get.return_value = _mock_compare_response(commits=[])

    client = RealGitHubClient(token="fake-token-for-test")
    client.list_commits("octo-org", "octo-repo", "v1.0.0", "v1.1.0")

    called_url = mock_get.call_args.args[0]
    assert called_url == "https://api.github.com/repos/octo-org/octo-repo/compare/v1.0.0...v1.1.0"


@patch("changelog_agent.github_client.requests.get")
def test_real_client_sends_auth_header_when_token_provided(mock_get):
    mock_get.return_value = _mock_compare_response(commits=[])

    client = RealGitHubClient(token="my-secret-token")
    client.list_commits("owner", "repo", "base", "head")

    headers = mock_get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer my-secret-token"
    assert headers["Accept"] == "application/vnd.github+json"


@patch("changelog_agent.github_client.requests.get")
def test_real_client_omits_auth_header_when_no_token(mock_get):
    mock_get.return_value = _mock_compare_response(commits=[])

    client = RealGitHubClient(token=None)
    client.list_commits("owner", "repo", "base", "head")

    headers = mock_get.call_args.kwargs["headers"]
    assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# RealGitHubClient — response parsing (mocked)
# ---------------------------------------------------------------------------


@patch("changelog_agent.github_client.requests.get")
def test_real_client_parses_200_response_into_commits(mock_get):
    raw_commits = [
        {
            "sha": "abc123def456",
            "commit": {
                "message": "feat: add login flow",
                "author": {"name": "Jane Doe", "date": "2026-08-01T12:00:00Z"},
            },
            "author": {"login": "janedoe"},
        },
        {
            "sha": "789xyz000111",
            "commit": {
                "message": "fix: correct typo",
                "author": {"name": "John Smith", "date": "2026-08-02T09:30:00Z"},
            },
            "author": None,
        },
    ]
    mock_get.return_value = _mock_compare_response(commits=raw_commits)

    client = RealGitHubClient(token="fake-token-for-test")
    commits = client.list_commits("owner", "repo", "base", "head")

    assert len(commits) == 2

    assert commits[0] == Commit(
        sha="abc123def456",
        message="feat: add login flow",
        author="janedoe",
        date="2026-08-01T12:00:00Z",
    )

    # No linked GitHub "author.login" -> falls back to raw git commit author name.
    assert commits[1] == Commit(
        sha="789xyz000111",
        message="fix: correct typo",
        author="John Smith",
        date="2026-08-02T09:30:00Z",
    )


@patch("changelog_agent.github_client.requests.get")
def test_real_client_raises_clear_error_on_404(mock_get):
    mock_get.return_value = _mock_compare_response(
        status_code=404, text='{"message": "Not Found"}'
    )

    client = RealGitHubClient(token="fake-token-for-test")

    with pytest.raises(GitHubClientError) as exc_info:
        client.list_commits("owner", "repo", "base", "head")

    message = str(exc_info.value)
    assert "404" in message
    assert "owner/repo" in message


@patch("changelog_agent.github_client.requests.get")
def test_real_client_raises_clear_error_on_500(mock_get):
    mock_get.return_value = _mock_compare_response(status_code=500, text="Internal Server Error")

    client = RealGitHubClient()

    with pytest.raises(GitHubClientError) as exc_info:
        client.list_commits("owner", "repo", "base", "head")

    assert "500" in str(exc_info.value)
