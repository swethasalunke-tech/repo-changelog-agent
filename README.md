# repo-changelog-agent

An agent that reads a GitHub repo's commit history between two refs and
drafts a categorized changelog (feat/fix/docs/chore) from real commit data.

This is Day 1 of a multi-day build. See `DESIGN.md` for scope and
`BUILD-SCHEDULE.md` for the day-by-day plan.

## What's implemented (Day 1)

- **`changelog_agent/models.py`** — `Commit` and `ChangelogEntry` dataclasses.
- **`changelog_agent/categorizer.py`** — `categorize_commit(commit) ->
  ChangelogEntry`. Parses a Conventional-Commits-style prefix (`feat:`,
  `fix(scope):`, `docs!:`, case-insensitive) from the first line of the
  commit message using an anchored regex, falling back to `"other"` for
  anything that doesn't match. Specifically avoids misclassifying a commit
  whose *body* happens to mention a keyword like "fix" without it actually
  being a `fix:`-prefixed commit — see
  `tests/test_categorizer.py::test_body_mentions_fix_but_not_prefixed_is_other`.
- **`changelog_agent/github_client.py`**:
  - `GitHubClient` — a `Protocol` (`list_commits(owner, repo, base, head) ->
    list[Commit]`).
  - `RealGitHubClient` — calls the real GitHub REST API compare endpoint
    (`GET /repos/{owner}/{repo}/compare/{base}...{head}`) via `requests.get`,
    with `Authorization: Bearer <token>` header handling and JSON response
    parsing into `Commit` objects. Raises `GitHubClientError` with a clear
    message on any non-200 response.
  - `FakeGitHubClient` — returns `Commit` objects from the bundled fixture
    `data/sample_commits.json` (10 clearly-synthetic commits spanning
    feat/fix/docs/chore/other), for exercising the categorizer and builder
    offline.
- **`changelog_agent/build.py`** — `build_changelog(commits) ->
  dict[str, list[ChangelogEntry]]` (grouped by category) and
  `render_markdown(grouped) -> str` (renders a Markdown changelog with one
  section per non-empty category, in feat/fix/docs/chore/other order).

## Honest caveat: `RealGitHubClient` has NOT been run against the live GitHub API

This repo was built in a sandbox with **no outbound network access to
`api.github.com`**. `RealGitHubClient`'s URL construction, auth header
handling, and response parsing are covered by unit tests in
`tests/test_github_client.py` that mock `requests.get` with
`unittest.mock.patch`. Those tests confirm, against the real code:

- the compare URL is built correctly from `owner`, `repo`, `base`, `head`;
- the `Authorization` header is set (or correctly omitted) based on whether
  a token was provided;
- a mocked 200 response with realistic GitHub API JSON shape parses into the
  expected `Commit` objects;
- a mocked 404 (and 500) raises a `GitHubClientError` with a clear message.

That is real, meaningful test coverage of real code — but it is **not** the
same as a successful live call. No file in this repo claims
`RealGitHubClient` has been exercised against the live GitHub API, and no
sample output anywhere in this repo is presented as having come from a real
API response. `data/sample_commits.json` is explicitly a fixture (author
handles are named `fixture-dev-1`, `fixture-dev-2`, `fixture-dev-3`, and the
SHAs are synthetic placeholders, not real commit hashes from any repo).

Once this is run somewhere with network access to `api.github.com`,
`RealGitHubClient` should be exercised against a real public repo, the
result checked by hand, and only then can a "verified live" claim be added —
see `BUILD-SCHEDULE.md` (Day 2).

## Running the tests

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

Last local run: **37 passed** (see below for the exact output).

```
tests/test_build.py::test_build_changelog_groups_by_category PASSED
tests/test_build.py::test_build_changelog_preserves_commit_order_within_category PASSED
tests/test_build.py::test_build_changelog_entries_have_correct_sha_and_author PASSED
tests/test_build.py::test_build_changelog_omits_empty_categories PASSED
tests/test_build.py::test_build_changelog_empty_input_returns_empty_dict PASSED
tests/test_build.py::test_render_markdown_known_structure PASSED
tests/test_build.py::test_render_markdown_section_order_is_feat_fix_docs_chore_other PASSED
tests/test_build.py::test_render_markdown_entry_line_content PASSED
tests/test_build.py::test_render_markdown_omits_sections_with_no_entries PASSED
tests/test_build.py::test_render_markdown_empty_grouped_dict PASSED
tests/test_categorizer.py::test_feat_prefix PASSED
tests/test_categorizer.py::test_fix_prefix PASSED
tests/test_categorizer.py::test_docs_prefix PASSED
tests/test_categorizer.py::test_chore_prefix PASSED
tests/test_categorizer.py::test_prefix_with_scope PASSED
tests/test_categorizer.py::test_fix_prefix_with_scope PASSED
tests/test_categorizer.py::test_prefix_with_scope_and_breaking_marker PASSED
tests/test_categorizer.py::test_case_insensitive_uppercase PASSED
tests/test_categorizer.py::test_case_insensitive_mixed_case_with_scope PASSED
tests/test_categorizer.py::test_case_insensitive_docs PASSED
tests/test_categorizer.py::test_body_mentions_fix_but_not_prefixed_is_other PASSED
tests/test_categorizer.py::test_word_that_starts_with_a_type_token_is_not_a_false_positive PASSED
tests/test_categorizer.py::test_unknown_prefix_falls_back_to_other PASSED
tests/test_categorizer.py::test_prefix_without_space_after_colon_still_requires_whitespace_boundary PASSED
tests/test_categorizer.py::test_empty_message PASSED
tests/test_categorizer.py::test_whitespace_only_message PASSED
tests/test_categorizer.py::test_only_first_line_is_used_for_description PASSED
tests/test_categorizer.py::test_entry_preserves_sha_and_author PASSED
tests/test_github_client.py::test_fake_client_returns_all_fixture_commits PASSED
tests/test_github_client.py::test_fake_client_returns_commit_objects_with_expected_shape PASSED
tests/test_github_client.py::test_fake_client_ignores_ref_arguments_and_is_deterministic PASSED
tests/test_github_client.py::test_real_client_builds_correct_compare_url PASSED
tests/test_github_client.py::test_real_client_sends_auth_header_when_token_provided PASSED
tests/test_github_client.py::test_real_client_omits_auth_header_when_no_token PASSED
tests/test_github_client.py::test_real_client_parses_200_response_into_commits PASSED
tests/test_github_client.py::test_real_client_raises_clear_error_on_404 PASSED
tests/test_github_client.py::test_real_client_raises_clear_error_on_500 PASSED

37 passed in 0.08s
```

## Not yet implemented

- Real diff/patch fetching per commit.
- Per-commit summarization beyond the raw commit message.
- A CLI entrypoint and full `CHANGELOG.md` file generation.
- A live end-to-end run against `api.github.com`.

See `DESIGN.md` and `BUILD-SCHEDULE.md` for details and the Day 2 / Day 3 plan.
