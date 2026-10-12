"""Execute installers with isolated tool shims, without network installs."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def installer_tools(tmp_path):
    tools = tmp_path / "tool bin"
    tools.mkdir()
    shim = tools / "python3"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, shutil, sys\n"
        "args = sys.argv[1:]\n"
        "with open(os.environ['INSTALL_RECORD'], 'a') as f: f.write(json.dumps(args) + '\\n')\n"
        "if args[:2] == ['-m', 'venv']:\n"
        "    target = pathlib.Path(args[2]) / 'bin'; target.mkdir(parents=True)\n"
        "    shutil.copyfile(__file__, target / 'python'); (target / 'python').chmod(0o755)\n"
        "    launcher = target / 'guyline'; launcher.write_text('#!/bin/sh\\nexit 0\\n'); launcher.chmod(0o755)\n"
        "elif args[:2] == ['-m', 'pip'] and os.environ.get('INSTALL_FAIL'):\n"
        "    sys.exit(17)\n"
        "elif args and args[0] == '-c':\n"
        "    if 'get_frontend_dir' in args[1]: print(os.environ['INSTALL_FRONTEND'])\n"
        "    elif 'get_config_dir' in args[1]: print(os.environ['GUYLINE_CONFIG_DIR'])\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    npm = tools / "npm"
    npm.write_text(f"#!{sys.executable}\nimport json, os, sys\nwith open(os.environ['INSTALL_RECORD'], 'a') as f: f.write(json.dumps(['npm', *sys.argv[1:]]) + '\\n')\nsys.exit(19 if os.environ.get('INSTALL_NPM_FAIL') else 0)\n")
    npm.chmod(0o755)
    frontend = tmp_path / "installed frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}")
    (frontend / "package-lock.json").write_text("{}")
    home = tmp_path / "user home"
    home.mkdir()
    env = {
        **os.environ, "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(home), "GUYLINE_CONFIG_DIR": str(tmp_path / "custom config"),
        "INSTALL_FRONTEND": str(frontend), "INSTALL_RECORD": str(tmp_path / "record.jsonl"),
    }
    return env, tmp_path


@pytest.mark.parametrize("script", ["install.sh", "install_dev.sh"])
@pytest.mark.parametrize("kind", ["source", "wheel"])
def test_bash_installer_uses_local_target_and_installed_frontend(installer_tools, script, kind):
    env, root = installer_tools
    target = root / ("source checkout" if kind == "source" else "guyline local.whl")
    if kind == "source":
        target.mkdir()
        (target / "pyproject.toml").write_text('[project]\nname="guyline"\n')
    else:
        target.touch()
    result = subprocess.run(
        ["bash", f"scripts/{script}", f"--{kind}", str(target), "--global-venv"],
        env=env, capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in Path(env["INSTALL_RECORD"]).read_text().splitlines()]
    pip = next(call for call in calls if call[:2] == ["-m", "pip"])
    assert str(target) in pip
    assert ("-e" in pip) == (kind == "source")
    assert ["-m", "guyline", "--version"] in calls
    assert ["-m", "guyline", "agent", "--help"] in calls
    assert ["npm", "ci", "--no-fund", "--no-audit"] in calls
    launchers = list((Path(env["HOME"]) / ".local/bin").iterdir())
    assert [path.name for path in launchers] == ["guyline"]
    assert launchers[0].resolve() == Path(env["HOME"]) / ".guyline-venv/bin/guyline"


def test_bash_installer_stops_on_pip_failure(installer_tools):
    env, root = installer_tools
    wheel = root / "broken wheel.whl"
    wheel.touch()
    env["INSTALL_FAIL"] = "1"
    result = subprocess.run(["bash", "scripts/install.sh", "--wheel", str(wheel)], env=env, capture_output=True, timeout=20, check=False)
    assert result.returncode != 0
    assert not (Path(env["HOME"]) / ".local/bin/guyline").exists()


def test_bash_installer_rejects_missing_local_target(installer_tools):
    env, root = installer_tools
    result = subprocess.run(["bash", "scripts/install.sh", "--wheel", str(root / "missing.whl")], env=env, capture_output=True, timeout=20, check=False)
    assert result.returncode != 0
    assert not Path(env["INSTALL_RECORD"]).exists()


@pytest.mark.parametrize("script", ["install.sh", "install_dev.sh"])
def test_bash_installer_defaults_to_its_checkout(installer_tools, script):
    env, _ = installer_tools
    result = subprocess.run(["bash", f"scripts/{script}", "--global-venv"], env=env, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in Path(env["INSTALL_RECORD"]).read_text().splitlines()]
    pip = next(call for call in calls if call[:2] == ["-m", "pip"])
    assert str(Path.cwd()) in pip


@pytest.mark.parametrize("npm_fail", [False, True])
def test_bash_installer_npm_fallback_and_failure(installer_tools, npm_fail):
    env, root = installer_tools
    (Path(env["INSTALL_FRONTEND"]) / "package-lock.json").unlink()
    wheel = root / "local.whl"
    wheel.touch()
    if npm_fail:
        env["INSTALL_NPM_FAIL"] = "1"
    result = subprocess.run(["bash", "scripts/install.sh", "--wheel", str(wheel)], env=env, capture_output=True, timeout=20, check=False)
    calls = [json.loads(line) for line in Path(env["INSTALL_RECORD"]).read_text().splitlines()]
    assert ["npm", "install", "--no-fund", "--no-audit"] in calls
    assert (result.returncode != 0) == npm_fail
    assert (Path(env["HOME"]) / ".local/bin/guyline").exists() == (not npm_fail)
