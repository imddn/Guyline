from __future__ import annotations

from types import SimpleNamespace

from typer.testing import CliRunner

import guyline.agent.cli as agent_cli
from guyline.cli import app


def test_root_invocation_keeps_core_cli_default(monkeypatch):
    captured = {}

    async def fake_run_repl(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("guyline.ui.app.run_repl", fake_run_repl)
    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0, result.output
    assert captured["prompt"] is None


def test_agent_command_defaults_to_personal_agent(monkeypatch):
    captured = {}

    def fake_run_agent_default(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(agent_cli, "run_agent_default", fake_run_agent_default, raising=False)
    result = CliRunner().invoke(app, ["agent"])

    assert result.exit_code == 0, result.output
    assert captured["workspace"] is None


def test_agent_subcommand_exposes_existing_setup_commands():
    result = CliRunner().invoke(app, ["agent", "--help"])

    assert result.exit_code == 0, result.output
    for command in ("init", "config", "doctor", "memory", "soul", "user"):
        assert command in result.output


def test_gateway_commands_are_available_at_the_root(tmp_path, monkeypatch):
    workspace = tmp_path / ".guyline-home"
    monkeypatch.setattr(
        agent_cli,
        "gateway_status",
        lambda cwd, workspace: SimpleNamespace(model_dump_json=lambda indent: '{"running":false}'),
    )
    result = CliRunner().invoke(
        app,
        ["gateway", "status", "--cwd", str(tmp_path), "--workspace", str(workspace)],
    )

    assert result.exit_code == 0, result.output
    assert '"running":false' in result.output
