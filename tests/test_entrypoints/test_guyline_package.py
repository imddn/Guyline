from __future__ import annotations

import importlib
from pathlib import Path


def test_guyline_package_namespaces_are_importable():
    package = importlib.import_module("guyline")
    agent = importlib.import_module("guyline.agent")

    assert Path(package.__file__).resolve().parent.name == "guyline"
    assert Path(agent.__file__).resolve().parent.name == "agent"
