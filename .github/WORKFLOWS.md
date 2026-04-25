# GitHub Actions Workflows

## CI (`ci.yml`)

**Triggers:** push to `main`, pull requests to `main`, manual dispatch

The main quality gate. All jobs run in parallel; only `lint` and `test` failures block merge.

| Job | What it does | Fails build? |
|---|---|---|
| Lint and Format Check | black, isort, ruff (check-only), mypy (soft) | Yes |
| Test (3.10 / 3.11 / 3.12) | `pytest tests/ -m "not integration"` + Codecov upload | Yes |
| Pre-commit Hooks | Runs all pre-commit hooks (skips mypy, detect-secrets, end-of-file-fixer, markdownlint) | Yes |
| Security Checks | bandit + safety (both soft) | No |
| Docker Build Test | Builds image, does not push | No |
| Dependency Review | Checks new deps for CVEs ≥ moderate | PR only |

Dependencies are installed with `uv sync --all-extras --all-groups` via `astral-sh/setup-uv`.

---

## Release (`release.yml`)

**Triggers:** push of a `v*` tag, manual dispatch (with `version` input)

Builds and pushes the Docker image to the registry, creates a GitHub Release with changelog.

---

## Security Scanning (`security.yml`)

**Triggers:** push to `main`, pull requests to `main`, weekly on Mondays at 00:00 UTC, manual dispatch

Runs bandit, safety, and other security scanners independently of the main CI pipeline.

---

## Claude Code (`claude.yml`)

**Triggers:** issue comments, issue assignments, PR review submissions

Runs Claude Code in response to `@claude` mentions in issues and PRs. Enables automated code changes, explanations, and reviews requested inline.

---

## Bug Report Handler (`bug-report-handler.yml`)

**Triggers:** issues opened, edited, or labeled — only when title starts with `[Bug]`

Uses Claude to analyse bug reports: distinguishes real bugs from usage misunderstandings, posts a diagnostic comment, and opens a fix PR for confirmed bugs.

---

## Issue Triage (`claude-auto-triage.yml`)

**Triggers:** issue opened

Uses Claude to automatically label and prioritise new issues.

---

## Weekly Maintenance (`claude-repo-maintainer.yml`)

**Triggers:** every Sunday at 00:00 UTC, manual dispatch

Uses Claude to perform weekly repo housekeeping: stale issue cleanup, dependency notes, and documentation gap detection.

---

## Gemini Dispatch (`gemini-dispatch.yml`)

**Triggers:** pull requests, issues, issue comments — routes to the appropriate Gemini workflow based on event type.

---

## Gemini Review (`gemini-review.yml`)

**Triggers:** dispatched by Gemini Dispatch on PR events

Runs a Gemini-powered code review on pull requests.

---

## Gemini Triage (`gemini-triage.yml`)

**Triggers:** dispatched by Gemini Dispatch on issue events

Runs Gemini-powered issue triage and labelling.

---

## Gemini Scheduled Triage (`gemini-scheduled-triage.yml`)

**Triggers:** daily at 00:00 UTC, push to `main`, pull requests, manual dispatch

Periodically triages open issues using Gemini.

---

## Gemini Invoke (`gemini-invoke.yml`)

**Triggers:** dispatched internally by other Gemini workflows

Low-level workflow that executes a Gemini model call on behalf of the dispatch/triage workflows.
