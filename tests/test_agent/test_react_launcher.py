"""Exercise Agent first-launch dependency selection and failure handling."""

import json

import pytest

from guyline.agent import runtime


@pytest.mark.asyncio
@pytest.mark.parametrize("locked", [True, False])
@pytest.mark.parametrize("install_exit", [0, 9])
async def test_agent_launcher_uses_lock_and_propagates_install_failure(
    tmp_path, monkeypatch, locked, install_exit,
):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}", encoding="utf-8")
    if locked:
        (frontend / "package-lock.json").write_text("{}", encoding="utf-8")
    workspace = tmp_path / "agent workspace"
    calls = []

    class Process:
        def __init__(self, exit_code):
            self.exit_code = exit_code

        async def wait(self):
            return self.exit_code

    async def spawn(*args, **kwargs):
        calls.append((args, kwargs))
        return Process(install_exit if len(calls) == 1 else 7)

    monkeypatch.setattr(runtime, "get_frontend_dir", lambda: frontend)
    monkeypatch.setattr(runtime, "_resolve_npm", lambda: "npm")
    monkeypatch.setattr(runtime, "_resolve_tsx", lambda _: ["tsx"])
    monkeypatch.setattr(runtime.asyncio, "create_subprocess_exec", spawn)

    if install_exit:
        with pytest.raises(RuntimeError, match="Failed to install"):
            await runtime.launch_agent_react_tui(cwd=str(tmp_path), workspace=workspace)
        assert len(calls) == 1
        assert not workspace.exists()
    else:
        assert await runtime.launch_agent_react_tui(
            cwd=str(tmp_path), workspace=workspace,
        ) == 7
        assert len(calls) == 2
        assert calls[1][0] == ("tsx", "src/index.tsx")
        config = json.loads(calls[1][1]["env"]["GUYLINE_FRONTEND_CONFIG"])
        command = config["backend_command"]
        assert command[1:5] == ["-m", "guyline", "agent", "--backend-only"]
        assert command[command.index("--workspace") + 1] == str(workspace)

    assert calls[0][0] == (
        "npm", "ci" if locked else "install", "--no-fund", "--no-audit",
    )
    assert calls[0][1]["cwd"] == str(frontend)
