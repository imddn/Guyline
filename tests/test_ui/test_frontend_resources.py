"""Frontend dependency installation follows the packaged lockfile."""

from types import SimpleNamespace

import pytest

from guyline.ui import react_launcher


@pytest.mark.parametrize("locked", [True, False])
@pytest.mark.parametrize("install_exit", [0, 9])
async def test_frontend_install_uses_lock_and_propagates_failure(tmp_path, monkeypatch, locked, install_exit):
    (tmp_path / "package.json").write_text("{}")
    if locked:
        (tmp_path / "package-lock.json").write_text("{}")
    calls = []

    async def spawn(*args, **kwargs):
        calls.append((args, kwargs))

        async def wait():
            return install_exit if len(calls) == 1 else 0

        return SimpleNamespace(wait=wait)

    monkeypatch.setattr(react_launcher, "get_frontend_dir", lambda: tmp_path)
    monkeypatch.setattr(react_launcher, "_resolve_npm", lambda: "npm")
    monkeypatch.setattr(react_launcher, "_resolve_tsx", lambda _: ("tsx",))
    monkeypatch.setattr(react_launcher, "_resolve_theme", lambda: "default")
    monkeypatch.setattr(react_launcher.asyncio, "create_subprocess_exec", spawn)
    if install_exit:
        with pytest.raises(RuntimeError, match="Failed to install"):
            await react_launcher.launch_react_tui(cwd="/external")
        assert len(calls) == 1
    else:
        assert await react_launcher.launch_react_tui(cwd="/external") == 0
        assert len(calls) == 2
        assert "GUYLINE_FRONTEND_CONFIG" in calls[1][1]["env"]
    assert calls[0][0] == ("npm", "ci" if locked else "install", "--no-fund", "--no-audit")
    assert calls[0][1]["cwd"] == str(tmp_path)
