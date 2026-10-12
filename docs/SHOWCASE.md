# Guyline Showcase

Small examples for Guyline 0.2.0, using the commands installed from this checkout
or a local wheel. Configure a provider before examples that call a model.

See also the [architecture document](ARCHITECTURE.md) ([English](ARCHITECTURE.en.md))
and the [README](../README.en.md) for installation and configuration.

## 0. Credential-free checks (no provider needed)

These run before any provider is configured and never call a model:

```bash
uv run guyline --version
uv run guyline --dry-run -p "/help"    # resolves config/skills/commands/tools; no model call
uv run python -m guyline provider list # list configured profiles (local)
```

`--dry-run` only previews the resolved runtime; it does not execute the command
handler or any tool. Examples that call a model need a configured provider.
Configure credentials interactively with `guyline setup` or `guyline auth login`
so they are not written to shell history, and use placeholders only — never put a
real token into a command or example.

## 1. Repository-aware coding assistant

Use Guyline as a lightweight local coding agent for reading code, making edits, and running validation commands.

```bash
uv run guyline
```

Example prompt:

```text
Review this repo, identify the highest-risk bug, patch it, and run the relevant tests.
```

## 2. Headless automation for scripts and CI

The print mode is useful when you want structured output in shell pipelines or automation jobs.

```bash
uv run guyline -p "Summarize the purpose of this repository" --output-format json
uv run guyline -p "List files that define the permission system" --output-format stream-json
```

## 3. Skill and plugin playground

Guyline can load Markdown skills and Claude-style plugin layouts, which makes it useful for experimentation with custom workflows.

Examples:

- Put a custom skill in `~/.guyline/skills/`.
- Install a plugin into `~/.guyline/plugins/`.
- Use the same workflow conventions across multiple local projects.

## 4. Multi-agent and background task experiments

The repo includes team coordination primitives, background task management, and task inspection tools.

Example prompts:

```text
Spawn a worker to audit the test suite while you inspect the CLI command registry.
```

```text
Create a background task that runs the slow integration script and report back when it finishes.
```

## 5. Provider compatibility testbed

Guyline is useful when you need to compare Anthropic-compatible backends behind one harness.

Typical scenarios:

- Default Anthropic setup.
- Moonshot/Kimi through an Anthropic-compatible endpoint.
- Vertex-compatible and Bedrock-compatible gateways.
- Internal proxies that expose an Anthropic-style API surface.

Use `guyline setup` and `guyline provider list` to inspect supported profiles.

## 6. Documentation-first onboarding

If you are evaluating the project rather than contributing code, start here:

- [`README.md`](../README.md) for install, usage, and architecture.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) for contributor workflow.
- [`CHANGELOG.md`](../CHANGELOG.md) for visible repo changes.

## How to contribute a showcase entry

Good showcase additions are:

- Based on a real workflow you ran.
- Short enough to reproduce locally.
- Honest about prerequisites and limitations.
- Focused on what Guyline makes easier, not on generic LLM claims.
