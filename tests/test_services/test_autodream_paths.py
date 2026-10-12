from pathlib import Path

import pytest

from guyline.config.settings import Settings
from guyline.services.autodream import service
from guyline.tasks.types import TaskRecord


@pytest.fixture
def dream_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("GUYLINE_AGENT_WORKSPACE", raising=False)
    monkeypatch.delenv("GUYLINE_AUTODREAM_CHILD", raising=False)
    for name in ("CONFIG", "DATA", "LOGS"):
        monkeypatch.setenv(f"GUYLINE_{name}_DIR", str(tmp_path / name.lower()))
    captured = []

    class Manager:
        def register_completion_listener(self, listener):
            pass

        async def create_shell_task(self, **kwargs):
            captured.append(kwargs)
            return TaskRecord(
                id="paths", type="dream", status="running",
                description=kwargs["description"], cwd=str(kwargs["cwd"]),
                output_file=tmp_path / "dream.log", argv=kwargs["argv"], env=kwargs["env"],
            )

    monkeypatch.setattr(service, "get_task_manager", lambda: Manager())
    return {
        "cwd": tmp_path, "settings": Settings(), "force": True, "preview": True,
        "memory_dir": tmp_path / "custom-agent" / "memory",
        "session_dir": tmp_path / "custom-agent" / "sessions",
    }, captured


@pytest.mark.parametrize("runner_entry", ["agent", "core"])
async def test_dream_resolves_native_workspace_and_propagates_env(dream_paths, tmp_path, runner_entry):
    kwargs, captured = dream_paths
    task = await service.start_dream_now(**kwargs, runner_entry=runner_entry)
    assert task is not None
    if runner_entry == "agent":
        expected_workspace = (tmp_path / "custom-agent").resolve()
    else:
        expected_workspace = (tmp_path / ".guyline" / "agent").resolve()
    assert captured[-1]["env"]["GUYLINE_AGENT_WORKSPACE"] == str(expected_workspace)
    # The explicit memory directory is used verbatim...
    assert captured[-1]["env"]["GUYLINE_AUTODREAM_MEMORY_DIR"] == str(
        (tmp_path / "custom-agent" / "memory").resolve()
    )
    # ...and resolving the default workspace never creates a ~/.guyline tree.
    assert not (tmp_path / ".guyline").exists()


@pytest.mark.parametrize("resolver", ["get_config_dir", "get_data_dir", "get_logs_dir", "get_workspace_root"])
async def test_dream_env_resolution_failure_allows_immediate_retry(dream_paths, tmp_path, monkeypatch, resolver):
    kwargs, captured = dream_paths
    original = getattr(service, resolver)

    def fail():
        raise RuntimeError("resolver failed")

    monkeypatch.setattr(service, resolver, fail)
    with pytest.raises(RuntimeError, match="resolver failed"):
        await service.start_dream_now(**kwargs)
    assert not captured
    assert not (kwargs["memory_dir"] / ".consolidate-lock").exists()
    monkeypatch.setattr(service, resolver, original)
    monkeypatch.setenv("GUYLINE_AGENT_WORKSPACE", str(tmp_path / "custom-agent"))
    assert await service.start_dream_now(**kwargs) is not None
