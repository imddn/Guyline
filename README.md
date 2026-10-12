# Guyline 0.2.0

Guyline is a local coding and personal agent harness with tools, skills, memory,
permissions, background tasks and chat gateways.

See [简体中文说明](README.zh-CN.md), [contributing](CONTRIBUTING.md),
[workflow examples](docs/SHOWCASE.md) and the [security policy](SECURITY.md).

## Install

Requires Python 3.10+ and Node.js 18+ with npm for the React terminal.
Clone [imddn/Guyline](https://github.com/imddn/Guyline) and install from the
checkout. A published PyPI package is not required.

```bash
git clone https://github.com/imddn/Guyline.git
cd Guyline
uv sync --extra dev
cd frontend/terminal
npm ci
cd ../..
uv run guyline --version
uv run guyline
```

With pip, create a virtual environment and run `python -m pip install -e .`.
The local installers create `.guyline-venv` and register only `guyline`:

```bash
bash scripts/install.sh
bash scripts/install.sh --source "/path/to/local checkout"
bash scripts/install_dev.sh                 # checkout-local editable venv
bash scripts/install_dev.sh --global-venv   # ~/.guyline-venv
```

PowerShell uses matching local arguments:

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -Source "C:\path\local checkout"
```

Build and install a local wheel:

```bash
uv build --wheel
python -m pip install /path/to/guyline-0.2.0-py3-none-any.whl
bash scripts/install.sh --wheel "/path/to/guyline-0.2.0-py3-none-any.whl"
```

On Windows use `-Wheel "C:\path\guyline-0.2.0-py3-none-any.whl"`.
The wheel includes terminal sources and the npm lockfile. The installer discovers
them using its installed interpreter and runs `npm ci`; direct first launch also
installs missing frontend dependencies. Custom development layouts without a
lock use `npm install`. Installers stop when installation or verification fails.

## First Run

Verify the install and preview the resolved runtime without any provider
credentials:

```bash
uv run guyline --version
uv run guyline --dry-run -p "/help"   # resolves config/skills/commands/tools; no model call
```

`--dry-run` only prints what Guyline would use; it never calls a model or runs
tools, so it works before any provider is configured. To actually get an answer,
configure one provider first and then send a prompt:

```bash
uv run guyline setup          # interactive: choose workflow, authenticate, pick model
uv run guyline provider list  # list configured provider profiles
uv run guyline auth status    # show the active auth source
uv run guyline -p "Explain this repository"   # needs a configured provider
```

`guyline -p` calls the configured model and may incur provider cost; it cannot
answer without a provider. Prefer the interactive `guyline setup` or
`guyline auth login` flows so credentials are entered at a prompt instead of
being typed into shell history or committed to a repository. Do not paste real
tokens into scripts, issues or examples; use placeholders only.

The React terminal is optional. A Python-only install can use the CLI, `-p`,
`python -m guyline` and `gateway`; installing `frontend/terminal` adds the React
TUI.

## Commands

```bash
guyline                       # coding CLI
guyline setup
guyline provider list
guyline auth status
guyline -p "Explain this repository"
guyline --dry-run -p "/help"   # no model or tool execution
guyline -p "Summarize this repository" --output-format json
guyline agent init
guyline agent config
guyline agent                 # personal Agent
guyline gateway run           # foreground
guyline gateway start
guyline gateway status
guyline gateway restart
guyline gateway stop
```

`python -m guyline` provides the same command tree. Only the `guyline` console
script is exported. Provider interfaces such as `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY` and `CODEX_HOME` retain their external meanings.

## Directories And Overrides

| Purpose | Default | Override |
| --- | --- | --- |
| Global configuration, skills, plugins | `~/.guyline/` | `GUYLINE_CONFIG_DIR` |
| Runtime data, sessions, project memory | `~/.guyline/data/` | `GUYLINE_DATA_DIR` |
| Logs | `~/.guyline/logs/` | `GUYLINE_LOGS_DIR` |
| Personal Agent workspace | `~/.guyline/agent/` | `GUYLINE_AGENT_WORKSPACE` |
| Channel downloads | `<agent workspace>/attachments/<channel>/` | `GUYLINE_CHANNEL_MEDIA_DIR/<channel>/` |

Data and logs follow the effective configuration root unless overridden.
Project settings and skills live in `<project>/.guyline/`; project skill discovery
also supports `.agents/skills` and `.claude/skills`. Project plugins remain opt-in.
Persistent coding memory lives under the data root's `memory/<project>-<hash>`.
Personal memory lives in the Agent workspace's `memory/`.

An explicit `--workspace` wins over `GUYLINE_AGENT_WORKSPACE`, then the default.
Relative explicit/env workspace paths resolve against the requested working
directory for Gateway; Gateway freezes its effective workspace for the lifecycle.

## Development And Validation

```bash
uv run pytest -q
uv run ruff check src tests scripts
cd frontend/terminal
npm ci
npm run typecheck
npm test
cd ../../autopilot-dashboard
npm ci
npm run build
```

The Dashboard build regenerates `docs/autopilot`. Its public snapshot is sample
data, not an export of a user's current workspace. Native Windows CI targets
Windows Python 3.10 and 3.11; the Linux adapter tests do not substitute for that run.
Vendored channel provenance remains in `src/guyline/channels/UPSTREAM`.

Real-API tests are opt-in and skipped by default: set `GUYLINE_RUN_REAL_API=1`,
a non-empty `ANTHROPIC_API_KEY`, and `GUYLINE_REAL_WORKSPACE` (a local checkout)
to enable them. The default `pytest` run does not contact a model.

## Known Limitations

- There is no credential-free model path: a real prompt needs a configured
  provider with valid credentials.
- Real-API and Docker sandbox tests need extra local prerequisites and are not
  part of the default offline test run.
- The autopilot workflows run on a self-hosted runner and only trigger manually;
  treat them as privileged maintainer automation. See [SECURITY.md](SECURITY.md).
- Platform support is limited to the CI matrix that actually runs; Windows
  native file-storage behavior is covered only by the Windows CI job.
