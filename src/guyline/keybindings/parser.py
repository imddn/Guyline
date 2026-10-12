"""Keybinding file parsing."""

from __future__ import annotations

import json


def parse_keybindings(text: str) -> dict[str, str]:
    """Parse a JSON keybinding mapping."""
    data = json.loads(text)
    if type(data) is not dict:
        raise ValueError("keybindings file must be a JSON object")
    parsed: dict[str, str] = {}
    for key, value in data.items():
        if type(key) is not str or type(value) is not str:
            raise ValueError("keybindings keys and values must be strings")
        parsed[key] = value
    return parsed
