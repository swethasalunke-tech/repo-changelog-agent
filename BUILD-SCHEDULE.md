# BUILD SCHEDULE

## Day 1 (this build) — data model, categorizer, GitHub client interface

- `changelog_agent/models.py` — `Commit`, `ChangelogEntry` dataclasses.
- `changelog_agent/categorizer.py` — regex-based `categorize_commit`.
- `changelog_agent/github_client.py` — `GitHubClient` protocol,
  `RealGitHubClient` (request-tested via mocks, not yet run live),
  `FakeGitHubClient` (backed by `data/sample_commits.json`).
- `changelog_agent/build.py` — `build_changelog`, `render_markdown`.
- Full test suite for all of the above (`tests/`).
- `DESIGN.md`, `README.md`, this file.

Status: complete, tests passing (see README.md for the run command and honest
caveats).

## Day 2 (planned) — diff fetching + per-commit summarization

- Extend `GitHubClient` (or add a sibling method) to fetch the actual diff /
  patch content for each commit or for the whole compare range, using the
  real `files` array already present in the GitHub compare API response
  (`patch`, `additions`, `deletions`, `status` per file).
- Add a summarization step that turns a commit + its diff into a slightly
  richer changelog line than the raw commit message alone (e.g., noting
  which files/areas changed), without inventing content not present in the
  diff.
- Extend the fixture data and tests accordingly.
- If sandbox network access to `api.github.com` is available by this point,
  run `RealGitHubClient` (and the new diff-fetching code) against a real
  public repo and record the actual result — only then can this repo say
  "verified live," and only for that specific run.

## Day 3 (planned) — CLI entrypoint + full changelog file generation

- Add a CLI entrypoint (e.g. `python -m changelog_agent <owner>/<repo>
  <base>..<head>`) that wires `RealGitHubClient` → `build_changelog` →
  `render_markdown` → writes a `CHANGELOG.md` (or prints to stdout).
- Handle pagination on the compare endpoint for ranges with many commits.
- Add CLI-level tests (argument parsing, output file writing) using the
  `FakeGitHubClient` / mocked `RealGitHubClient` patterns established on
  Day 1.
- Update `README.md` with real usage instructions and, if a live run has
  happened by then, an honest description of what was actually verified
  (repo, ref range, and what the output looked like).
