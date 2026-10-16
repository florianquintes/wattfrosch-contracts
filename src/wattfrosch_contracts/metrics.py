"""METRICS catalog — v1 stub.

Replaced by Issue 4 (full model + catalog per README §2). Only what the
MeasurementRecord validators need exists here.
"""

from collections.abc import Mapping
from typing import Final, NamedTuple


class MetricStub(NamedTuple):
    key: str


METRICS: Final[Mapping[str, MetricStub]] = {
    "generation.solar": MetricStub(key="generation.solar"),
    "generation.wind_onshore": MetricStub(key="generation.wind_onshore"),
    "consumption.load": MetricStub(key="consumption.load"),
    "price.day_ahead": MetricStub(key="price.day_ahead"),
    "weather.temperature_2m": MetricStub(key="weather.temperature_2m"),
}
