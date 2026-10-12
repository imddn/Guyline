"""Local rules file management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from guyline.config.paths import get_config_dir


def _rules_dir() -> Path:
    directory = get_config_dir() / "local_rules"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_local_rules() -> str:
    """Load the local rules markdown, or empty string if none exist."""
    path = _rules_dir() / "rules.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def save_local_rules(content: str) -> Path:
    """Write local rules markdown."""
    path = _rules_dir() / "rules.md"
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def load_facts() -> dict:
    """Load extracted facts as a dict."""
    path = _rules_dir() / "facts.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"facts": [], "last_updated": None}


def save_facts(facts: dict) -> None:
    """Persist extracted facts."""
    facts["last_updated"] = datetime.now(timezone.utc).isoformat()
    (_rules_dir() / "facts.json").write_text(
        json.dumps(facts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def merge_facts(existing: dict, new_facts: list[dict]) -> dict:
    """Merge new facts into existing, deduplicating by key."""
    by_key = {}
    for f in existing.get("facts", []):
        by_key[f["key"]] = f
    for f in new_facts:
        key = f.get("key", "")
        if key:
            if key in by_key:
                # Update with newer value, keep higher confidence
                old = by_key[key]
                if f.get("confidence", 0) >= old.get("confidence", 0):
                    by_key[key] = f
            else:
                by_key[key] = f
    return {"facts": list(by_key.values())}
