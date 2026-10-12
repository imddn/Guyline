import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest


@pytest.fixture
def matrix_channel(monkeypatch):
    # Only import-time optional dependencies are stubbed; the media method is real.
    nio = ModuleType("nio")
    for name in ["AsyncClient", "AsyncClientConfig", "ContentRepositoryConfigError", "DownloadError", "InviteEvent", "JoinError", "MatrixRoom", "MemoryDownloadResponse", "RoomEncryptedMedia", "RoomMessage", "RoomMessageMedia", "RoomMessageText", "RoomSendError", "RoomTypingError", "SyncError", "UploadError"]:
        setattr(nio, name, type(name, (), {}))
    attachments = ModuleType("nio.crypto.attachments")
    attachments.decrypt_attachment = Mock()
    exceptions = ModuleType("nio.exceptions")
    exceptions.EncryptionError = type("EncryptionError", (Exception,), {})
    nh3 = ModuleType("nh3")
    nh3.Cleaner = Mock()
    mistune = ModuleType("mistune")
    mistune.create_markdown = Mock()
    for name, module in {
        "nio": nio, "nio.crypto.attachments": attachments,
        "nio.exceptions": exceptions, "nh3": nh3, "mistune": mistune,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    source = Path(__file__).parents[2] / "src/guyline/channels/impl/matrix.py"
    spec = importlib.util.spec_from_file_location("matrix_paths_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MatrixChannel.__new__(module.MatrixChannel)


@pytest.mark.parametrize("override", [False, True])
def test_matrix_media_uses_shared_paths(matrix_channel, tmp_path, monkeypatch, override):
    monkeypatch.setenv("GUYLINE_AGENT_WORKSPACE", str(tmp_path / "agent"))
    monkeypatch.setenv("GUYLINE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("GUYLINE_CHANNEL_MEDIA_DIR", raising=False)
    root = tmp_path / "agent" / "attachments"
    if override:
        root = tmp_path / "custom-media"
        monkeypatch.setenv("GUYLINE_CHANNEL_MEDIA_DIR", str(root))
    assert matrix_channel._media_dir() == root / "matrix"
    assert (root / "matrix").is_dir()
    assert not (tmp_path / "data" / "media").exists()
