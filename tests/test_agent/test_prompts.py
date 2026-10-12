from pathlib import Path

from guyline.agent.memory import add_memory_entry as add_agent_memory_entry
from guyline.agent.memory import list_memory_files as list_agent_memory_files
from guyline.agent.memory import remove_memory_entry as remove_agent_memory_entry
from guyline.agent.prompts import build_agent_system_prompt
from guyline.agent.workspace import (
    get_bootstrap_path,
    get_identity_path,
    get_soul_path,
    get_user_path,
    initialize_workspace,
)
from guyline.config.settings import Settings
from guyline.memory import add_memory_entry as add_project_memory_entry
from guyline.prompts import build_runtime_system_prompt


def test_agent_prompt_includes_persona_and_memory(tmp_path: Path):
    workspace = tmp_path / ".guyline-home"
    initialize_workspace(workspace)
    get_soul_path(workspace).write_text("# soul\nSpeak like a calm operator.\n", encoding="utf-8")
    get_identity_path(workspace).write_text("# identity\nName: guyline\n", encoding="utf-8")
    get_user_path(workspace).write_text("# user\nPrefers terse answers.\n", encoding="utf-8")
    get_bootstrap_path(workspace).write_text("# bootstrap\nAsk a few high-value questions.\n", encoding="utf-8")
    add_agent_memory_entry(workspace, "timezone", "The user prefers UTC timestamps.")

    prompt = build_agent_system_prompt(tmp_path, workspace=workspace)

    assert "You are Guyline" in prompt
    assert "Speak like a calm operator." in prompt
    assert "Name: guyline" in prompt
    assert "Prefers terse answers." in prompt
    assert "Ask a few high-value questions." in prompt
    assert "timezone.md" in prompt
    assert "UTC timestamps" in prompt


def test_agent_runtime_prompt_can_exclude_project_memory(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_COORDINATOR_MODE", raising=False)
    monkeypatch.setenv("GUYLINE_DATA_DIR", str(tmp_path / "data"))
    workspace = tmp_path / ".guyline-home"
    initialize_workspace(workspace)
    add_agent_memory_entry(workspace, "personal", "guyline-only personal fact")
    add_project_memory_entry(tmp_path, "project", "project memory should not leak")

    base_prompt = build_agent_system_prompt(tmp_path, workspace=workspace)
    runtime_prompt = build_runtime_system_prompt(
        Settings(system_prompt=base_prompt),
        cwd=tmp_path,
        latest_user_prompt="hello",
        include_project_memory=False,
    )

    assert "guyline-only personal fact" in runtime_prompt
    assert "project memory should not leak" not in runtime_prompt


def test_agent_memory_uses_schema_and_soft_delete(tmp_path: Path):
    workspace = tmp_path / ".guyline-home"
    initialize_workspace(workspace)

    path = add_agent_memory_entry(workspace, "timezone", "The user prefers UTC timestamps.")

    text = path.read_text(encoding="utf-8")
    assert "schema_version: 1" in text
    assert "type: \"personal\"" in text

    assert remove_agent_memory_entry(workspace, "timezone") is True
    assert path.exists()
    assert list_agent_memory_files(workspace) == []
    assert "disabled: true" in path.read_text(encoding="utf-8")
