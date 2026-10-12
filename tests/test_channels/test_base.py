from __future__ import annotations

from guyline.channels.impl.base import resolve_channel_media_dir


def test_resolve_channel_media_dir_uses_guyline_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / ".guyline-home"
    monkeypatch.setenv("GUYLINE_AGENT_WORKSPACE", str(workspace))
    monkeypatch.delenv("GUYLINE_CHANNEL_MEDIA_DIR", raising=False)
    monkeypatch.delenv("GUYLINE_DATA_DIR", raising=False)

    media_dir = resolve_channel_media_dir("feishu")

    assert media_dir == workspace / "attachments" / "feishu"
    assert media_dir.is_dir()


def test_resolve_channel_media_dir_uses_default_agent_workspace(monkeypatch, tmp_path):
    from pathlib import Path

    data_dir = tmp_path / ".guyline-data"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("GUYLINE_AGENT_WORKSPACE", raising=False)
    monkeypatch.delenv("GUYLINE_CHANNEL_MEDIA_DIR", raising=False)
    monkeypatch.setenv("GUYLINE_DATA_DIR", str(data_dir))

    media_dir = resolve_channel_media_dir("telegram")

    assert media_dir == tmp_path / ".guyline" / "agent" / "attachments" / "telegram"
    assert media_dir.is_dir()


def test_resolve_channel_media_dir_explicit_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("GUYLINE_AGENT_WORKSPACE", str(tmp_path / "agent"))
    monkeypatch.setenv("GUYLINE_CHANNEL_MEDIA_DIR", str(tmp_path / "media"))
    assert resolve_channel_media_dir("telegram") == tmp_path / "media" / "telegram"
