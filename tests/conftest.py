"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
import pytest_asyncio

from guyline.tasks.manager import shutdown_task_manager

# Any variable with these prefixes can leak the host's Guyline configuration,
# model/endpoint selection or credentials into a test.
_ISOLATED_ENV_PREFIXES = ("GUYLINE_", "ANTHROPIC_", "OPENAI_")

# Native API keys probed by settings.auth_source_env_var_candidates().
_ISOLATED_NATIVE_API_KEYS = (
    "DASHSCOPE_API_KEY",
    "MOONSHOT_API_KEY",
    "GEMINI_API_KEY",
    "MINIMAX_API_KEY",
    "NVIDIA_API_KEY",
    "MODELSCOPE_API_KEY",
)


@pytest.fixture(autouse=True)
def _isolate_host_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[None]:
    """Detach tests from the host Guyline config, model, endpoint and credentials.

    Tests may still set their own inputs explicitly via ``monkeypatch``; this
    fixture only removes inherited values and redirects the storage roots into
    a per-test temporary directory that is kept outside the test's own
    ``tmp_path`` so tests enumerating their workspace are unaffected.
    """
    for name in list(os.environ):
        if name.startswith(_ISOLATED_ENV_PREFIXES):
            monkeypatch.delenv(name, raising=False)
    for name in _ISOLATED_NATIVE_API_KEYS:
        monkeypatch.delenv(name, raising=False)

    root = tmp_path_factory.mktemp("guyline-isolation")
    for var, dirname in (
        ("GUYLINE_CONFIG_DIR", "config"),
        ("GUYLINE_DATA_DIR", "data"),
        ("GUYLINE_LOGS_DIR", "logs"),
    ):
        path = root / dirname
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(var, str(path))

    yield


@pytest_asyncio.fixture(autouse=True)
async def _reset_background_task_manager(_isolate_host_environment: None):
    yield
    await shutdown_task_manager()
