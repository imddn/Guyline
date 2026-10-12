"""Approved launcher and PowerShell installation contract."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib


def test_pyproject_exports_only_guyline():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"] == {"guyline": "guyline.cli:app"}


def test_powershell_installs_local_source_or_wheel_and_verifies_interpreter():
    script = Path("scripts/install.ps1").read_text(encoding="utf-8")
    assert "[string]$Source" in script
    assert "[string]$Wheel" in script
    assert '.guyline-venv' in script
    assert 'guyline.exe' in script
    assert '-m guyline --version' in script
    assert '-m guyline agent --help' in script
    assert 'get_frontend_dir' in script
    assert '$LASTEXITCODE' in script
    # The installer wires only the current `guyline` entry point from a local
    # checkout or wheel, with no remote fallback.
    assert "-e $Target" in script
    assert "pip install $Target" in script
    assert "github.com" not in script
    assert "raw.githubusercontent" not in script
