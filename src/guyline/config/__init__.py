"""Configuration system for Guyline.

Provides settings management, path resolution, and API key handling.
"""

from guyline.config.paths import (
    get_config_dir,
    get_config_file_path,
    get_data_dir,
    get_logs_dir,
)
from guyline.config.settings import (
    ProviderProfile,
    Settings,
    auth_source_provider_name,
    default_auth_source_for_provider,
    default_provider_profiles,
    load_settings,
    save_settings,
)

__all__ = [
    "ProviderProfile",
    "Settings",
    "auth_source_provider_name",
    "default_auth_source_for_provider",
    "default_provider_profiles",
    "get_config_dir",
    "get_config_file_path",
    "get_data_dir",
    "get_logs_dir",
    "load_settings",
    "save_settings",
]
