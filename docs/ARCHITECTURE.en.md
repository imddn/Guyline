# Guyline Architecture

[中文](ARCHITECTURE.md) · [Back to README](../README.en.md)

This document explains Guyline's main parts using a consistent structure:
the problem each part solves, how it is implemented, the tradeoffs, and where to
find the source and tests. Everything described here reflects the current `main`
branch and can be checked against the code.

- [1. Execution loop](#1-execution-loop)
- [2. Multi-agent and background tasks](#2-multi-agent-and-background-tasks)
- [3. Context, compaction and memory](#3-context-compaction-and-memory)
- [4. Permissions and sandboxing](#4-permissions-and-sandboxing)
- [5. Extensions and model adapters](#5-extensions-and-model-adapters)
- [6. Entry points and channels](#6-entry-points-and-channels)
- [Appendix A: Paths, environment variables and precedence](#appendix-a-paths-environment-variables-and-precedence)
- [Appendix B: Other installation methods](#appendix-b-other-installation-methods)
- [Appendix C: Data and migration rules](#appendix-c-data-and-migration-rules)
- [Appendix D: Third-party provenance](#appendix-d-third-party-provenance)

## 1. Execution loop

**The problem.** A model only returns text or tool-call requests. Completing real work
requires something that feeds tool results back, controls turns and cost, and defines
clear boundaries when things go wrong.

**How it works.** `QueryEngine` (`src/guyline/engine/query_engine.py`) holds the
conversation history, current model, system prompt, tool registry, permission checker,
hook executor and usage accounting. The loop itself lives in
`src/guyline/engine/query.py`:

1. Send conversation messages and tool schemas to the model adapter and stream text
   deltas back.
2. If the model requests tool calls, run permission checks and hook checks, then
   execute the tools.
3. Normalize each result into a `ToolResultBlock` and append it to the conversation
   (the value a tool itself returns is still a `ToolResult`).
4. Call the model again and repeat.

Stop conditions live in the same layer: the model stops requesting tools, `max_turns`
is reached (raising `MaxTurnsExceeded`), an unhandled error surfaces, or a
context/output length boundary is hit. Length boundaries are not immediate failures:
on a prompt-too-long error (`_is_prompt_too_long_error`) Guyline first attempts one
reactive compaction, and the turn is retried only if that compaction succeeded; on a
completion-token-limit error (`_is_completion_token_limit_error`) it lowers
`effective_max_tokens` and retries only when the model reported a lower limit.

Interfaces consume an event stream rather than calling tools directly:
`src/guyline/engine/stream_events.py` defines `AssistantTextDelta`,
`ToolExecutionStarted`, `ToolExecutionCompleted`, `ErrorEvent`, `StatusEvent` and
`CompactProgressEvent`. `QueryEngine` also exposes `has_pending_continuation()` and
`continue_pending()` so an interrupted or compacted turn can be resumed.

**Tradeoffs.**

- Decoupling the loop from the UI lets CLI, `-p`, the React terminal and the Gateway
  share one implementation instead of each growing a divergent agent loop.
- Writing every tool result back into context keeps adding to the context load, which
  is why compaction (section 3) is required.
- Normalizing tool results into structured objects makes them compactable,
  memory-extractable and testable.

**Where to look.** [`src/guyline/engine/query.py`](../src/guyline/engine/query.py),
[`query_engine.py`](../src/guyline/engine/query_engine.py),
[`stream_events.py`](../src/guyline/engine/stream_events.py),
[`cost_tracker.py`](../src/guyline/engine/cost_tracker.py); regressions live in
[`tests/test_engine/`](../tests/test_engine/).

## 2. Multi-agent and background tasks

**The problem.** Complex tasks split into parallel exploration or implementation
branches, and long tasks must not block the main session — they need creation,
inspection, output writing and stopping.

**How it works.** Multi-agent support lives in `src/guyline/swarm/`:

- `registry.py`'s `BackendRegistry` can register/detect several backends: in-process,
  subprocess, and pane backends that require tmux / iTerm2, with
  `mark_in_process_fallback()` when nothing else is available. **A registered backend
  is not the same as the default path**: the built-in `agent` tool
  (`src/guyline/tools/agent_tool.py`) explicitly calls
  `registry.get_executor("subprocess")` for every accepted mode so the spawned teammate
  can be polled by `BackgroundTaskManager`; the in-process, pane and fallback backends
  are used by their own call paths rather than being auto-selected by the `agent` tool.
- `in_process.py` runs teammates as asyncio Tasks in the current process, isolating
  identity and stats per teammate with `contextvars` (`TeammateContext`,
  `TeammateAbortController`).
- `subprocess_backend.py` spawns teammates as separate CLI processes, inheriting the
  required flags and environment.
- `team_lifecycle.py` persists teams to `~/.guyline/teams/<name>/team.json` and manages
  members, allowed paths, member modes and cleanup on exit.
- `mailbox.py` keeps a per-agent inbox directory of individual JSON messages written
  atomically via a temporary file plus `os.replace`. Permission requests and responses
  travel the same channel (`create_permission_request_message`,
  `create_sandbox_permission_request_message`).

Background tasks come from `BackgroundTaskManager` in
`src/guyline/tasks/manager.py`: `create_shell_task`, `create_agent_task`,
`read_task_output`, `write_to_task`, `stop_task`, plus completion listeners so the main
session can keep interacting.

**Tradeoffs.**

- Coordination and persistence use the local filesystem: persisted team and mailbox
  metadata is observable and recoverable after a restart, but this does not guarantee
  recovery of a teammate process that was still running, there is no distributed
  semantics, and cross-machine collaboration is out of scope.
- The in-process backend is cheapest and easiest to debug but shares process
  resources; subprocess or pane backends are worth their cost only when stronger
  isolation or an independent lifecycle is needed.

**Where to look.** [`src/guyline/swarm/`](../src/guyline/swarm/),
[`src/guyline/tasks/`](../src/guyline/tasks/); regressions live in
[`tests/test_swarm/`](../tests/test_swarm/) and
[`tests/test_tasks/`](../tests/test_tasks/).

## 3. Context, compaction and memory

**The problem.** Long tasks exhaust the context window, and information produced in one
session needs to remain usable in later ones.

**How it works.** Compaction lives in `src/guyline/services/compact/`:

- **microcompact** clears older tool-result content cheaply and does not call a model;
- **full compact** asks the model for a structured summary;
- **auto-compact** triggers when the estimated token count crosses a threshold;
- compaction boundaries preserve `tool_use` / `tool_result` pairs
  (`_split_preserving_tool_pairs`) so the message sequence stays valid, and rendered
  attachments (`render_compact_attachment`) carry history forward.

Token counts come from the rough character heuristic in
`src/guyline/services/token_estimation.py`, not from an exact tokenizer.

Memory is split in two:

- **Session memory** (`src/guyline/services/session_memory/`) is written per session
  under the data directory and exists to keep a compacted conversation coherent.
- **Persistent memory** (`src/guyline/memory/`) lives under the data root's
  `memory/<project>-<hash>/`, with `MEMORY.md` as the entry point and entries carrying
  frontmatter. `services/memory_extract/` extracts durable entries from completed
  turns, and `services/autodream/` consolidates them in the background with backup,
  diff and rollback support.

**Tradeoffs.**

- Estimation and LLM summaries are lossy: compaction does not guarantee that every
  detail survives, so hard constraints belong in persistent memory or should be
  restated by the user.
- Microcompact is cheap but only shrinks tool output; real semantic compaction costs
  an extra model call and latency, so the automatic path triggers on the token
  threshold, while manual compaction and the reactive compaction on a length-limit
  error are separate paths.

**Where to look.** [`src/guyline/services/compact/`](../src/guyline/services/compact/),
[`services/session_memory/`](../src/guyline/services/session_memory/),
[`services/memory_extract/`](../src/guyline/services/memory_extract/),
[`services/autodream/`](../src/guyline/services/autodream/),
[`src/guyline/memory/`](../src/guyline/memory/); regressions live in
[`tests/test_services/`](../tests/test_services/) and
[`tests/test_memory/`](../tests/test_memory/).

## 4. Permissions and sandboxing

**The problem.** Letting a model work on a real filesystem needs an explainable
decision layer, while stronger isolation is a different capability and must not be
conflated with it.

**How it works.** The permission layer lives in `src/guyline/permissions/`:

- `modes.py` defines the `default`, `plan` and `full_auto` modes;
- `checker.py`'s `PermissionChecker.evaluate` decides based on path rules
  (`PathRule`), command hints and the current mode; application credential paths are
  always refused (`_is_application_credential_path`);
- pre-tool hooks can also block execution and let the model switch tools afterwards.

Sandboxing is separate: `src/guyline/sandbox/adapter.py` wraps the external `srt`
(sandbox-runtime) CLI and reports enablement, availability and the reason through
`SandboxAvailability`; `sandbox/docker_backend.py` adds a Docker backend and
`path_validator.py` handles path validation. Both backends allow running without the
sandbox when enabled, the runtime is unavailable and failure is not requested, but they
differ: the `srt` path has
`wrap_command_for_sandbox` return the original command (no warning), while the Docker
path has `start_docker_sandbox` log a warning and start no session.
`SandboxUnavailableError` is raised only when `sandbox.fail_if_unavailable` is true.

**Enablement and boundaries.** Sandboxing is off by default (`sandbox.enabled=False`);
whether it is enabled, and whether an unavailable runtime is a hard failure, are
controlled by `sandbox.enabled` and `sandbox.fail_if_unavailable`, overridable through
`GUYLINE_SANDBOX_ENABLED` and `GUYLINE_SANDBOX_FAIL_IF_UNAVAILABLE`. Sandboxing needs an
external runtime, and platform availability depends on the actual environment (CI runs
sandbox tests only on the platforms it configures).

**Tradeoffs.**

- Permission rules are an application-layer decision and **are not system
  isolation**: they constrain what Guyline itself does, while real process and file
  isolation comes from the external sandbox runtime.
- The default mode favors explainability and review; fully opening up requires
  explicitly choosing `full_auto` or `--dangerously-skip-permissions`, which should
  only be used in a controlled environment.

**Where to look.** [`src/guyline/permissions/`](../src/guyline/permissions/),
[`src/guyline/sandbox/`](../src/guyline/sandbox/); regressions live in
[`tests/test_permissions/`](../tests/test_permissions/) and
[`tests/test_sandbox/`](../tests/test_sandbox/).

## 5. Extensions and model adapters

**The problem.** Runtime capabilities should extend without touching the core loop, and
provider differences should collapse into one adapter layer.

**How it works.**

- **Skills** (`src/guyline/skills/loader.py`) are discovered from bundled, user,
  compatibility and project directories, including project `.guyline/skills`,
  `.agents/skills` and `.claude/skills`.
- **Hooks** ([`src/guyline/hooks/`](../src/guyline/hooks/)) load definitions from
  settings and fire on events; hot reload is wired only into the runtime path that
  already uses it (`HookReloader` in `src/guyline/ui/runtime.py`), so not every entry
  point watches for config changes automatically.
- **Plugins** (`src/guyline/plugins/`) are discovered and imported, with an installer
  and bundled plugins.
- **MCP** (`src/guyline/mcp/`) connects stdio or HTTP MCP servers and exposes their
  tools.
- **Model adapters** (`src/guyline/api/`): `PROVIDERS` in `registry.py` is the single
  source of provider metadata, with `backend_type` distinguishing `anthropic`,
  `openai_compat` and `copilot`; `client.py`, `openai_client.py`,
  `copilot_client.py` and `codex_client.py` provide the implementations.
- **Provider profiles** (`src/guyline/config/settings.py`): `ProviderProfile` describes
  the provider, model and `api_format`, while `api/provider.py` handles detection and
  auth-status display. The CLI adds `--api-format`, `--base-url`, `--api-key` and the
  `guyline provider` / `guyline auth` command groups.

**Tradeoffs.**

- A single registry means adding a provider touches one place, at the cost of more
  configuration combinations that need runtime validation — which is what `--dry-run`
  previews.
- **A registered provider spec is not an end-to-end verification**: this repository's
  automated tests do not issue real calls to every provider. Real calls are opt-in
  (see the
  [real-API and platform limits in CONTRIBUTING](../CONTRIBUTING.md#real-api-and-platform-limits)).

**Where to look.** [`src/guyline/skills/`](../src/guyline/skills/),
[`hooks/`](../src/guyline/hooks/), [`plugins/`](../src/guyline/plugins/),
[`mcp/`](../src/guyline/mcp/), [`api/`](../src/guyline/api/); regressions live in
[`tests/test_skills/`](../tests/test_skills/),
[`tests/test_hooks/`](../tests/test_hooks/),
[`tests/test_plugins/`](../tests/test_plugins/),
[`tests/test_mcp/`](../tests/test_mcp/) and
[`tests/test_api/`](../tests/test_api/).

## 6. Entry points and channels

**How it works.** Every entry point converges on the loop from section 1:

- **Coding CLI** (`src/guyline/cli.py`): the root command starts an interactive coding
  session, `-p/--print` provides non-interactive output, and `--output-format` supports
  `text`, `json` and `stream-json`.
- **React terminal** (`src/guyline/ui/`, `frontend/terminal/`): an optional front end
  that talks to the Python backend over a structured protocol (`ui/protocol.py`,
  `ui/backend_host.py`).
- **Personal agent and Gateway** (`src/guyline/agent/`): `guyline agent` runs the
  long-lived personal agent; `gateway` manages its lifecycle, and
  `agent/gateway/bridge.py` connects channel messages to the Guyline runtime.
- **Channels** (`src/guyline/channels/`): IM channel implementations and the message
  bus, derived from nanobot (see Appendix D).
- **User scheduled tasks**: `guyline cron` manages the user's own scheduler and jobs
  (`src/guyline/services/cron_scheduler.py`) and is a product capability, unrelated to
  repository maintenance.
- **Maintainer tooling**: `guyline autopilot` targets repository maintenance and is not
  part of the default product run; the autopilot workflows trigger manually on a
  self-hosted runner.

**Where to look.** [`src/guyline/cli.py`](../src/guyline/cli.py),
[`src/guyline/ui/`](../src/guyline/ui/), [`src/guyline/agent/`](../src/guyline/agent/),
[`src/guyline/channels/`](../src/guyline/channels/); regressions live in
[`tests/test_entrypoints/`](../tests/test_entrypoints/),
[`tests/test_ui/`](../tests/test_ui/), [`tests/test_agent/`](../tests/test_agent/),
[`tests/test_channels/`](../tests/test_channels/) and
[`tests/test_bridge/`](../tests/test_bridge/).

## Appendix A: Paths, environment variables and precedence

| Purpose | Default | Environment variable |
| --- | --- | --- |
| Global configuration, skills, plugins | `~/.guyline/` | `GUYLINE_CONFIG_DIR` |
| Data, sessions, coding memory | `~/.guyline/data/` | `GUYLINE_DATA_DIR` |
| Logs | `~/.guyline/logs/` | `GUYLINE_LOGS_DIR` |
| Personal workspace | `~/.guyline/agent/` | `GUYLINE_AGENT_WORKSPACE` |
| Channel attachments | `<agent workspace>/attachments/<channel>/` | `GUYLINE_CHANNEL_MEDIA_DIR/<channel>/` |

- Data and logs follow the effective configuration root unless overridden separately.
- Project settings and skills use the project's `.guyline/`; project skill discovery
  also supports `.agents/skills` and `.claude/skills`, and project plugins stay opt-in.
- Coding memory lives under the data root at `memory/<project>-<hash>/`; personal
  memory lives in the agent workspace's `memory/`.
- Workspace precedence: an explicit `--workspace` beats `GUYLINE_AGENT_WORKSPACE`,
  which beats the default. For the Gateway, relative explicit/env workspace paths
  resolve against the requested working directory, and the effective workspace is
  frozen for the lifecycle.

## Appendix B: Other installation methods

```bash
# Local source or an explicit wheel; creates .guyline-venv and registers only the
# guyline launcher by default
bash scripts/install.sh --source "/path/to/local checkout"
bash scripts/install.sh --wheel "/path/to/guyline-0.2.0-py3-none-any.whl"
bash scripts/install_dev.sh                 # editable venv for this checkout
bash scripts/install_dev.sh --global-venv   # use ~/.guyline-venv

# Install a wheel directly
uv build --wheel
python -m pip install /path/to/guyline-0.2.0-py3-none-any.whl
```

PowerShell takes the same local paths through `-Source` / `-Wheel`. The wheel bundles
the terminal sources and the npm lockfile; the installer discovers them with its own
interpreter and runs `npm ci`, while custom development layouts without a lockfile
fall back to `npm install`. Installers exit non-zero when installation or verification
fails; source installs do not guarantee rollback of an environment that was already
created or partially written.

## Appendix C: Data and migration rules

- Guyline's own paths and configuration use only `.guyline`, `~/.guyline/` and
  `GUYLINE_*`; it does not auto-copy or read legacy application directories or legacy
  variable names, and does not auto-migrate legacy naming.
- Beyond its own config, Guyline reads existing provider environment variables (such as
  `ANTHROPIC_*` and `OPENAI_*`) and discovers skills from project directories like
  `.agents/skills` and `.claude/skills` (section 5).
- Memory files have their own schema migration entry point:
  `src/guyline/memory/migrate.py` migrates schema-v1 frontmatter to the current format,
  supports a dry run and backs up before writing.

## Appendix D: Third-party provenance

- The channel components are derived from
  [nanobot-ai/nanobot](https://github.com/nanobot-ai/nanobot) (MIT). Provenance is
  recorded in `src/guyline/channels/UPSTREAM`, and the license text is kept in
  `src/guyline/channels/LICENSE.nanobot`.
- The project itself is released under the MIT license (`LICENSE`, copyright imddn).
