"""METRICS catalog — metric definitions per README §2.

Each entry fixes the unit, category, aggregation and plausibility bounds for
one metric key (schema "<category>.<name>"). The key→category relationship is
strictly validated: a mismatch raises. Units are the contract units — sources
delivering other units are converted in fetch.

The v1 list is deliberately incomplete and filled manually later.
"""

from collections.abc import Mapping
from datetime import date
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from wattfrosch_contracts import errors

MetricCategory = Literal["generation", "consumption", "price", "weather"]
Aggregation = Literal["mean", "sum", "max", "min"]

_CATEGORIES: Final[frozenset[str]] = frozenset(
    {"generation", "consumption", "price", "weather"}
)


class MetricEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    unit: str
    category: MetricCategory
    aggregation: Aggregation
    derived: bool
    description: str
    is_renewable: bool
    can_be_negative: bool
    plausible_range: tuple[float, float] | None
    display_name: str
    valid_from: date
    valid_to: date | None

    @model_validator(mode="after")
    def _validate_key_matches_category(self) -> "MetricEntry":
        category, _, _ = self.key.partition(".")
        if category not in _CATEGORIES or category != self.category:
            raise errors.metric_category_mismatch_error(self.key, self.category)
        return self


def _entry(
    key: str,
    unit: str,
    category: MetricCategory,
    description: str,
    *,
    is_renewable: bool = False,
    can_be_negative: bool = False,
    plausible_range: tuple[float, float] | None = None,
    aggregation: Aggregation = "mean",
    display_name: str | None = None,
) -> MetricEntry:
    return MetricEntry(
        key=key,
        unit=unit,
        category=category,
        aggregation=aggregation,
        derived=False,
        description=description,
        is_renewable=is_renewable,
        can_be_negative=can_be_negative,
        plausible_range=plausible_range,
        display_name=display_name if display_name is not None else key,
        valid_from=date(2015, 1, 1),
        valid_to=None,
    )


METRICS: Final[Mapping[str, MetricEntry]] = {
    entry.key: entry
    for entry in (
        _entry(
            "generation.solar",
            "MW",
            "generation",
            "Solar power generation",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.wind_onshore",
            "MW",
            "generation",
            "Onshore wind power generation",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.wind_offshore",
            "MW",
            "generation",
            "Offshore wind power generation",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.biomass",
            "MW",
            "generation",
            "Biomass power generation",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.hydro",
            "MW",
            "generation",
            "Hydropower generation (run-of-river and reservoir)",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.lignite",
            "MW",
            "generation",
            "Lignite power generation",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.hard_coal",
            "MW",
            "generation",
            "Hard coal power generation",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.gas",
            "MW",
            "generation",
            "Natural gas power generation",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.nuclear",
            "MW",
            "generation",
            "Nuclear power generation",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.oil",
            "MW",
            "generation",
            "Oil power generation",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.other",
            "MW",
            "generation",
            "Other power generation (not covered by the other keys)",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.other_renewable",
            "MW",
            "generation",
            "Other renewable power generation (not covered by the other keys)",
            is_renewable=True,
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "generation.pumped_storage",
            "MW",
            "generation",
            "Pumped storage generation (negative = charging). A storage unit "
            "can be charged from any source, including coal.",
            can_be_negative=True,
            plausible_range=(-10_000.0, 10_000.0),
        ),
        _entry(
            "consumption.load",
            "MW",
            "consumption",
            "Electricity consumption (load)",
            plausible_range=(0.0, 100_000.0),
        ),
        _entry(
            "consumption.residual_load",
            "MW",
            "consumption",
            "Residual load (load minus renewable generation); negative when "
            "renewable generation exceeds load",
            can_be_negative=True,
            plausible_range=(-50_000.0, 100_000.0),
        ),
        _entry(
            "consumption.pumped_storage",
            "MW",
            "consumption",
            "Pumped storage consumption (negative = charging, mirroring the "
            "generation convention)",
            can_be_negative=True,
            plausible_range=(-10_000.0, 10_000.0),
        ),
        _entry(
            "price.day_ahead",
            "EUR/MWh",
            "price",
            "Day-ahead market price",
            can_be_negative=True,
            plausible_range=(-500.0, 3_000.0),
        ),
        _entry(
            "weather.temperature_2m",
            "K",
            "weather",
            "Air temperature at 2 m above ground, in kelvin. Plausibility "
            "bounds are the coldest (170 K) and hottest (345 K) temperatures "
            "measured on earth; fetch converts from source units.",
            plausible_range=(170.0, 345.0),
        ),
        _entry(
            "weather.wind_speed_10m",
            "m/s",
            "weather",
            "Wind speed at 10 m above ground",
            plausible_range=(0.0, 75.0),
        ),
        _entry(
            "weather.precipitation",
            "mm",
            "weather",
            "Precipitation sum per hour",
            aggregation="sum",
            plausible_range=(0.0, 200.0),
        ),
        _entry(
            "weather.cloud_cover",
            "%",
            "weather",
            "Cloud cover fraction",
            plausible_range=(0.0, 100.0),
        ),
    )
}
