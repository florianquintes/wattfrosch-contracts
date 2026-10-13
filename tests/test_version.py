import re
import tomllib
from pathlib import Path

from wattfrosch_contracts import CONTRACT_VERSION

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

PEP440 = r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"


def test_contract_version_importable() -> None:
    assert isinstance(CONTRACT_VERSION, str)
    assert CONTRACT_VERSION
    assert re.fullmatch(PEP440, CONTRACT_VERSION), CONTRACT_VERSION


def test_version_matches_pyproject() -> None:
    with PYPROJECT.open("rb") as f:
        pyproject = tomllib.load(f)
    assert CONTRACT_VERSION == pyproject["project"]["version"]
