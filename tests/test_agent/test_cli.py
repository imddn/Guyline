import json
import logging
from pathlib import Path

from typer.testing import CliRunner

from guyline.agent.cli import _build_gateway_logging_handlers, app


def test_agent_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Personal-agent app" in result.output
    for command in ("init", "config", "doctor", "memory", "soul", "user"):
        assert command in result.output
    # Gateway is a root command, not an Agent subcommand.
    assert runner.invoke(app, ["gateway", "--help"]).exit_code != 0

    from guyline.cli import app as root_app

    root = runner.invoke(root_app, ["gateway", "--help"])
    assert root.exit_code == 0, root.output
    for command in ("run", "start", "stop", "restart", "status"):
        assert command in root.output


def test_agent_init_and_doctor(tmp_path: Path):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    result = runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    assert result.exit_code == 0
    assert str(workspace) in result.output

    doctor = runner.invoke(app, ["doctor", "--cwd", str(tmp_path), "--workspace", str(workspace)])
    assert doctor.exit_code == 0
    assert "guyline doctor:" in doctor.output
    assert "workspace: ok" in doctor.output


def test_agent_init_existing_workspace_points_to_config(tmp_path: Path):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    first = runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    assert first.exit_code == 0

    second = runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    assert second.exit_code == 0
    assert "guyline workspace already exists." in second.output
    assert "Use `guyline config`" in second.output


def test_agent_init_noninteractive_defaults_to_deny_all_remote_access(tmp_path: Path):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    result = runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    assert result.exit_code == 0
    config = json.loads((workspace / "gateway.json").read_text(encoding="utf-8"))
    assert config["channel_configs"] == {}


def test_gateway_logging_handlers_write_gateway_log_file(tmp_path: Path):
    workspace = tmp_path / ".guyline-home"
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    assert result.exit_code == 0

    handlers = _build_gateway_logging_handlers(workspace, console=True, log_file=True)
    try:
        file_handlers = [handler for handler in handlers if isinstance(handler, logging.FileHandler)]
        console_handlers = [
            handler
            for handler in handlers
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert len(console_handlers) == 1

        record = logging.LogRecord(
            name="guyline.agent.gateway.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="GATEWAY_LOG_OK",
            args=(),
            exc_info=None,
        )
        file_handlers[0].emit(record)
        file_handlers[0].flush()

        log_path = workspace / "logs" / "gateway.log"
        assert "GATEWAY_LOG_OK" in log_path.read_text(encoding="utf-8")
    finally:
        for handler in handlers:
            handler.close()


def test_agent_init_interactive_writes_gateway_config(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    user_input = "1\ny\n123456\ntelegram-token\ny\nn\nn\nn\ny\ny\nn"
    result = runner.invoke(app, ["init", "--workspace", str(workspace)], input=user_input)
    assert result.exit_code == 0
    config = json.loads((workspace / "gateway.json").read_text(encoding="utf-8"))
    assert config["enabled_channels"] == ["telegram"]
    assert config["channel_configs"]["telegram"]["token"] == "telegram-token"
    assert config["channel_configs"]["telegram"]["allow_from"] == ["123456"]


def test_agent_init_interactive_allows_blank_allow_from_for_secure_default(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    user_input = "1\ny\n\ntelegram-token\ny\nn\nn\nn\ny\ny\nn"
    result = runner.invoke(app, ["init", "--workspace", str(workspace)], input=user_input)
    assert result.exit_code == 0
    config = json.loads((workspace / "gateway.json").read_text(encoding="utf-8"))
    assert config["channel_configs"]["telegram"]["allow_from"] == []
    assert "Remote access denied until allow_from is configured for: telegram" in result.output


def test_agent_init_interactive_writes_feishu_gateway_config(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    user_input = "1\nn\nn\nn\ny\nfeishu-user-1\n1\ncli_app\ncli_secret\nenc_key\nverify_me\nOK\n1\nguyline,openclaw\n\ny\nn\nn"
    result = runner.invoke(app, ["init", "--workspace", str(workspace)], input=user_input)
    assert result.exit_code == 0
    config = json.loads((workspace / "gateway.json").read_text(encoding="utf-8"))
    assert config["enabled_channels"] == ["feishu"]
    assert config["channel_configs"]["feishu"]["domain"] == "https://open.feishu.cn"
    assert config["channel_configs"]["feishu"]["app_id"] == "cli_app"
    assert config["channel_configs"]["feishu"]["app_secret"] == "cli_secret"
    assert config["channel_configs"]["feishu"]["encrypt_key"] == "enc_key"
    assert config["channel_configs"]["feishu"]["verification_token"] == "verify_me"
    assert config["channel_configs"]["feishu"]["react_emoji"] == "OK"
    assert config["channel_configs"]["feishu"]["group_policy"] == "managed_or_mention"
    assert config["channel_configs"]["feishu"]["bot_names"] == ["guyline", "openclaw"]


def test_agent_config_interactive_can_restart_gateway(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("guyline.agent.cli.gateway_status", lambda cwd, workspace: type("State", (), {"running": True})())
    monkeypatch.setattr("guyline.agent.cli.stop_gateway_process", lambda cwd, workspace: True)
    monkeypatch.setattr("guyline.agent.cli.start_gateway_process", lambda cwd, workspace: 4321)
    user_input = "4\nn\nn\nn\ny\nfeishu-user-1\n2\ncli_app\ncli_secret\n\nverify_me\nOK\n1\nguyline,openclaw\n\ny\ny\nn\ny"
    result = runner.invoke(app, ["config", "--workspace", str(workspace)], input=user_input)
    assert result.exit_code == 0
    assert "guyline gateway restarted (pid=4321)" in result.output
    config = json.loads((workspace / "gateway.json").read_text(encoding="utf-8"))
    assert config["provider_profile"] == "codex"
    assert config["enabled_channels"] == ["feishu"]
    assert config["channel_configs"]["feishu"]["domain"] == "https://open.larksuite.com"


def test_agent_config_keeps_existing_channel_when_not_reconfigured(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / ".guyline-home"
    runner.invoke(app, ["init", "--workspace", str(workspace), "--no-interactive"])
    gateway_path = workspace / "gateway.json"
    config = json.loads(gateway_path.read_text(encoding="utf-8"))
    config["enabled_channels"] = ["feishu"]
    config["channel_configs"]["feishu"] = {
        "allow_from": ["feishu-user-1"],
        "app_id": "old_app",
        "app_secret": "old_secret",
        "encrypt_key": "",
        "verification_token": "old_verify",
        "react_emoji": "OK",
    }
    gateway_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("guyline.agent.cli.gateway_status", lambda cwd, workspace: type("State", (), {"running": False})())
    user_input = "4\nn\nn\nn\nn\ny\ny\nn"
    result = runner.invoke(app, ["config", "--workspace", str(workspace)], input=user_input)
    assert result.exit_code == 0
    updated = json.loads(gateway_path.read_text(encoding="utf-8"))
    assert updated["enabled_channels"] == ["feishu"]
    assert updated["channel_configs"]["feishu"]["app_id"] == "old_app"
    assert updated["channel_configs"]["feishu"]["app_secret"] == "old_secret"
