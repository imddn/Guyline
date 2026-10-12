"""Bridge exports."""

from guyline.bridge.manager import BridgeSessionManager, BridgeSessionRecord, get_bridge_manager
from guyline.bridge.session_runner import SessionHandle, spawn_session
from guyline.bridge.types import BridgeConfig, WorkData, WorkSecret
from guyline.bridge.work_secret import build_sdk_url, decode_work_secret, encode_work_secret

__all__ = [
    "BridgeConfig",
    "BridgeSessionManager",
    "BridgeSessionRecord",
    "SessionHandle",
    "WorkData",
    "WorkSecret",
    "build_sdk_url",
    "decode_work_secret",
    "encode_work_secret",
    "get_bridge_manager",
    "spawn_session",
]
