"""Central contract version for the entire contract set."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Final


def _read_version() -> str:
    try:
        from importlib import metadata

        return metadata.version("wattfrosch-contracts")
    except Exception:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        if pyproject.is_file():
            with pyproject.open("rb") as f:
                version = tomllib.load(f)["project"]["version"]
            assert isinstance(version, str)
            return version
        raise


CONTRACT_VERSION: Final[str] = _read_version()
