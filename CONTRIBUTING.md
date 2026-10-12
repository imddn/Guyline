# Contributing To Guyline

Guyline 0.2.0 development covers the runtime, CLI, Agent, Gateway and product docs
in this repository. Use the repository's own issue templates for reports.

## Setup

From a local checkout:

```bash
uv sync --extra dev
cd frontend/terminal
npm ci
cd ../..
uv run python -m guyline --version
```

`bash scripts/install_dev.sh` installs this checkout into its `.guyline-venv`.
Use `--global-venv` for the home-directory venv; `--source` and `--wheel`
select explicit local installation targets. See [README](README.md).

## Validation

```bash
uv run pytest -q
uv run ruff check src tests scripts
cd frontend/terminal
npm run typecheck
npm test
cd ../../autopilot-dashboard
npm ci
npm run build
```

The basic Python syntax/undefined-name gate is
`uv run ruff check --select E4,E7,E9,F src tests scripts`.
The full inherited Ruff gate remains enabled in CI; inherited findings are not
permission to weaken it or mix unrelated lint refactors into feature work.
Whole-repository strict mypy is not currently a required green check.

Native Windows CI uses Python 3.10/3.11 and runs the native path, workspace and
install-alias tests; POSIX chmod/RLIMIT/socket fixtures are not Windows
acceptance. PowerShell installer parsing also runs there.

## Changes And Reports

Keep changes scoped, add behavioral regressions for fixes, and state the command
and actual result of validation. Update docs when commands, configuration or
path contracts change. Add user-visible entries to [CHANGELOG](CHANGELOG.md).
Report exact commands, environment and error output without credentials.

[SHOWCASE](docs/SHOWCASE.md) accepts small reproducible examples.
Bundled and local skills should use Guyline modules, commands and paths.
Preserve genuine third-party provenance and licenses, including
`src/guyline/channels/UPSTREAM`. Do not rewrite user data for branding cleanup.

Update user-facing docs when commands, configuration or path contracts change:
keep `README.md` and `README.zh-CN.md` aligned, note new examples in
[SHOWCASE](docs/SHOWCASE.md), and add a short user-visible entry to
[CHANGELOG](CHANGELOG.md). Do not describe behavior you have not verified.

## Real API And Platform Limits

The default test run is offline. Real-API scripts in `tests/` are opt-in and
skip unless all of these are set:

- `GUYLINE_RUN_REAL_API=1`
- a non-empty `ANTHROPIC_API_KEY`
- `GUYLINE_REAL_WORKSPACE` pointing at an existing local checkout

Never put a real key in a script, fixture or committed default. Docker sandbox
end-to-end tests need a working Docker daemon; the React TUI checks need the
frontend dependencies. Native Windows file-storage behavior is verified only by
the Windows CI job, so a passing POSIX run is not Windows acceptance. Report the
exact command and its actual result, and do not mark checks you could not run as
passing.

## Security And Credentials

Do not paste real API keys, tokens, session files or personal absolute paths
into issues, pull requests, logs or examples; redact them and use placeholders.
Report suspected vulnerabilities privately as described in
[SECURITY.md](SECURITY.md) instead of opening a public issue.
