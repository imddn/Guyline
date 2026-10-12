"""Prompt assembly for guyline persona and workspace context."""

from __future__ import annotations

from pathlib import Path

from guyline.agent.memory import load_memory_prompt as load_agent_memory_prompt
from guyline.agent.workspace import (
    get_bootstrap_path,
    get_identity_path,
    get_soul_path,
    get_user_path,
    get_workspace_root,
)
from guyline.memory import load_memory_prompt as load_project_memory_prompt
from guyline.prompts.system_prompt import get_base_system_prompt


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8", errors="replace").strip()
    return content or None


def build_agent_system_prompt(
    cwd: str | Path,
    *,
    workspace: str | Path | None = None,
    extra_prompt: str | None = None,
    include_project_memory: bool = False,
) -> str:
    """Build the custom base prompt for guyline sessions."""
    root = get_workspace_root(workspace)
    sections = [get_base_system_prompt()]

    if extra_prompt:
        sections.extend(["# Additional Instructions", extra_prompt.strip()])

    soul = _read_text(get_soul_path(root))
    if soul:
        sections.extend(["# guyline Soul", soul])

    identity = _read_text(get_identity_path(root))
    if identity:
        sections.extend(["# guyline Identity", identity])

    user = _read_text(get_user_path(root))
    if user:
        sections.extend(["# User Profile", user])

    bootstrap = _read_text(get_bootstrap_path(root))
    if bootstrap:
        sections.extend(["# First-Run Bootstrap", bootstrap])

    sections.extend(
        [
            "# guyline Workspace",
            f"- Personal workspace root: {root}",
            "- Personal memory and sessions live under the shared guyline workspace root.",
            "- Resume only within guyline sessions; do not assume interoperability with plain Guyline sessions.",
        ]
    )

    if guyline_memory := load_agent_memory_prompt(root):
        sections.append(guyline_memory)

    if include_project_memory:
        project_memory = load_project_memory_prompt(cwd)
        if project_memory:
            sections.append(project_memory)

    return "\n\n".join(section for section in sections if section and section.strip())
