from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


DROPIN_XML_DIR = "api-monitor-xml"


def discover_xml_root(project_root: Path, env: Mapping[str, str] | None = None) -> Path:
    """Find the API Monitor XML root for a standalone checkout.

    The deployable default is `<repo>/api-monitor-xml`; `APIMON_XML_ROOT` remains
    available for users who keep the API Monitor definitions elsewhere.
    """
    values = env if env is not None else os.environ
    env_value = values.get("APIMON_XML_ROOT")
    if env_value:
        return normalize_xml_root(Path(env_value))

    return normalize_xml_root(project_root / DROPIN_XML_DIR)


def normalize_xml_root(path: Path) -> Path:
    """Accept either the XML root itself or a directory containing an API folder."""
    expanded = path.expanduser().resolve()
    if _looks_like_xml_root(expanded):
        return expanded

    nested_api = expanded / "API"
    if _looks_like_xml_root(nested_api):
        return nested_api

    return expanded


def _looks_like_xml_root(path: Path) -> bool:
    return path.is_dir() and (
        (path / "Headers").is_dir()
        or (path / "Windows").is_dir()
        or any(path.glob("*.xml"))
    )
