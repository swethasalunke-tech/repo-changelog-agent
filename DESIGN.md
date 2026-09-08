# DESIGN

## Goal

`repo-changelog-agent` reads a GitHub repo's commit history between two refs
(branches, tags, or SHAs) and drafts a categorized changelog (feat/fix/docs/chore)
from real commit data — no invented commits, no fabricated output.

## Day 1 scope (this build)

What's implemented and tested in this iteration:

1. **Data model** (`changelog_agent/models.py`) — `Commit` and `ChangelogEntry`
   dataclasses. Small and dependency-free.
2. **Categorizer** (`changelog_agent/categorizer.py`) — `categorize_commit`
   parses a Conventional-Commits-style prefix (`feat:`, `fix(scope):`, `docs!:`,
   etc.) from the first line of a commit message using an anchored, case-insensitive
   regex. Anything that doesn't match falls back to `"other"`. Deliberately
   avoids a naive substring check (`"fix" in message`), which would misfire on
   a commit whose *body* mentions a keyword without it being the actual type.
3. **GitHub client interface** (`changelog_agent/github_client.py`):
   - `GitHubClient` — a `Protocol` with one method, `list_commits(owner, repo,
     base, head) -> list[Commit]`.
   - `RealGitHubClient` — calls the real GitHub REST API compare endpoint
     (`GET /repos/{owner}/{repo}/compare/{base}...{head}`), with correct URL
     construction, `Authorization: Bearer <token>` header handling, JSON
     response parsing into `Commit` objects, and a `GitHubClientError` raised
     with a clear message on any non-200 response.
   - `FakeGitHubClient` — reads `data/sample_commits.json`, a bundled fixture
     of 10 clearly-synthetic commits, for exercising the categorizer and
     changelog builder without any network access.
4. **Changelog builder** (`changelog_agent/build.py`) — `build_changelog`
   groups categorized entries by category; `render_markdown` formats the
   grouped result as a Markdown changelog with one `##` section per non-empty
   category, in a fixed order (feat, fix, docs, chore, other).

## Honest caveat: RealGitHubClient has not been run against the live API

This was built in a sandbox with no outbound network access to
`api.github.com`. `RealGitHubClient`'s request construction and response
parsing are covered by unit tests that mock `requests.get` (see
`tests/test_github_client.py`) — these confirm the URL is built correctly,
the auth header is set correctly, a 200 response is parsed into the right
`Commit` objects, and a 404 raises a clear `GitHubClientError`. That is real
test coverage of real code, but it is **not** the same as a live call having
succeeded. No claim is made anywhere in this repo that `RealGitHubClient` has
been exercised against the live GitHub API — see `README.md` for the same
caveat stated for anyone just skimming this repo.

## Explicitly deferred (not in Day 1)

- Fetching real commit **diffs** (the compare endpoint only gives commit
  metadata + message; diff/patch fetching is separate).
- Per-commit or per-PR **summarization** beyond what the raw commit message
  already says.
- Full **changelog file generation** end-to-end (writing a `CHANGELOG.md` to
  disk, handling pagination on the compare endpoint for large ranges, etc.).
- A **live end-to-end run** against `api.github.com` — deferred until this is
  built/run somewhere with outbound network access, at which point
  `RealGitHubClient` should be exercised against a real public repo and the
  result checked by hand before any claim of "verified live" is made.
- A **CLI entrypoint** (`repo-changelog-agent <owner>/<repo> <base>..<head>`).

See `BUILD-SCHEDULE.md` for how these map to Day 2 / Day 3.
