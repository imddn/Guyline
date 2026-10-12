"""Unified authentication management for Guyline."""

from guyline.auth.flows import ApiKeyFlow, BrowserFlow, DeviceCodeFlow
from guyline.auth.manager import AuthManager
from guyline.auth.storage import (
    clear_provider_credentials,
    decrypt,
    encrypt,
    load_credential,
    load_external_binding,
    store_credential,
    store_external_binding,
)

__all__ = [
    "ApiKeyFlow",
    "AuthManager",
    "BrowserFlow",
    "DeviceCodeFlow",
    "clear_provider_credentials",
    "decrypt",
    # Deprecated — use _obfuscate/_deobfuscate directly if needed.
    # Kept for backward compatibility; will be removed in a future version.
    "encrypt",
    "load_credential",
    "load_external_binding",
    "store_credential",
    "store_external_binding",
]
