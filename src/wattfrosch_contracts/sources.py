"""SOURCES catalog — v1 stub.

Replaced by Issue 6 (full model + maps per README §4–§6). Only what the
MeasurementRecord validators need exists here.
"""

from typing import Final

SOURCES: Final[frozenset[str]] = frozenset(
    {
        "energy-charts",
        "smard",
        "open-meteo",
    }
)
