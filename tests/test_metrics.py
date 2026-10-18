"""Tests for the METRICS catalog (README §2, TODO Issue 4)."""

import pytest
from pydantic import ValidationError

from wattfrosch_contracts import METRICS
from wattfrosch_contracts.errors import (
    METRIC_CATEGORY_MISMATCH,
    METRIC_REGION_KIND_MISMATCH,
)
from wattfrosch_contracts.metrics import MetricEntry
from wattfrosch_contracts.regions import REGIONS

VALID_FROM = "2015-01-01"


def _make_entry(**overrides: object) -> MetricEntry:
    base: dict[str, object] = {
        "key": "generation.solar",
        "unit": "MW",
        "category": "generation",
        "aggregation": "mean",
        "derived": False,
        "description": "Solar power generation",
        "is_renewable": True,
        "can_be_negative": False,
        "plausible_range": (0.0, 100_000.0),
        "display_name": "Solar",
        "valid_from": VALID_FROM,
        "valid_to": None,
    }
    base.update(overrides)
    return MetricEntry(**base)  # type: ignore[arg-type]


def error_type(exc: ValidationError) -> str:
    return exc.errors()[0]["type"]


# --- Catalog integrity ----------------------------------------------------


def test_catalog_not_empty() -> None:
    assert len(METRICS) >= 20


def test_all_keys_follow_category_schema() -> None:
    for key, entry in METRICS.items():
        category, sep, name = key.partition(".")
        assert sep == ".", f"key {key!r} has no category prefix"
        assert category == entry.category, f"key {key!r} vs category {entry.category}"
        assert name != "", f"key {key!r} has empty name"


def test_dict_keys_match_entry_keys() -> None:
    for key, entry in METRICS.items():
        assert entry.key == key


def test_unique_categories_present() -> None:
    assert {entry.category for entry in METRICS.values()} == {
        "generation",
        "consumption",
        "price",
        "weather",
    }


@pytest.mark.parametrize("entry", list(METRICS.values()), ids=lambda e: e.key)
def test_entry_fields_valid(entry: MetricEntry) -> None:
    assert entry.unit != ""
    assert entry.description != ""
    assert entry.display_name != ""
    assert entry.aggregation in {"mean", "sum", "max", "min"}
    assert entry.valid_from.isoformat() == VALID_FROM
    assert entry.valid_to is None
    if entry.plausible_range is not None:
        low, high = entry.plausible_range
        assert low < high


# --- Strict key↔category validation ---------------------------------------


def test_key_category_mismatch_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _make_entry(key="weather.solar", category="generation")
    assert error_type(excinfo.value) == f"wattfrosch.{METRIC_CATEGORY_MISMATCH}"


def test_key_without_category_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _make_entry(key="solar", category="generation")
    assert error_type(excinfo.value) == f"wattfrosch.{METRIC_CATEGORY_MISMATCH}"


def test_unknown_category_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _make_entry(key="finance.stock", category="generation")
    assert error_type(excinfo.value) == f"wattfrosch.{METRIC_CATEGORY_MISMATCH}"


def test_matching_key_accepted() -> None:
    entry = _make_entry(key="generation.solar", category="generation")
    assert entry.key == "generation.solar"


# --- Domain rules ----------------------------------------------------------


def test_pumped_storage_rules() -> None:
    entry = METRICS["generation.pumped_storage"]
    assert entry.category == "generation"
    assert entry.can_be_negative is True
    assert entry.is_renewable is False


def test_day_ahead_price_can_be_negative() -> None:
    entry = METRICS["price.day_ahead"]
    assert entry.category == "price"
    assert entry.can_be_negative is True


def test_renewable_metrics() -> None:
    renewable = {
        key
        for key, entry in METRICS.items()
        if entry.is_renewable and entry.category == "generation"
    }
    assert renewable == {
        "generation.solar",
        "generation.wind_onshore",
        "generation.wind_offshore",
        "generation.biomass",
        "generation.hydro",
        "generation.other_renewable",
    }


def test_temperature_in_kelvin_with_earth_record_range() -> None:
    entry = METRICS["weather.temperature_2m"]
    assert entry.unit == "K"
    assert entry.plausible_range == (170.0, 345.0)
    assert entry.can_be_negative is False


def test_precipitation_is_sum_aggregation() -> None:
    assert METRICS["weather.precipitation"].aggregation == "sum"


def test_frozen_model_rejects_mutation() -> None:
    entry = METRICS["generation.solar"]
    with pytest.raises(ValidationError) as excinfo:
        entry.unit = "GW"  # type: ignore[misc]
    assert error_type(excinfo.value) == "frozen_instance"


# --- Category → region-kind pairing ----------------------------------------


_KIND_BY_CATEGORY = {
    "generation": "bidding_zone",
    "consumption": "bidding_zone",
    "price": "bidding_zone",
    "weather": "weather_point",
}


def test_region_kind_pairing_is_satisfied_by_catalog() -> None:
    for entry in METRICS.values():
        expected_kind = _KIND_BY_CATEGORY[entry.category]
        matching = [
            region for region in REGIONS.values() if region.kind == expected_kind
        ]
        assert matching, f"no {expected_kind} region for {entry.key}"


def test_no_category_maps_to_multiple_kinds() -> None:
    for entry in METRICS.values():
        assert entry.category in _KIND_BY_CATEGORY


def test_category_kind_mismatch_error_type() -> None:
    from wattfrosch_contracts import errors

    exc = errors.metric_region_kind_mismatch_error(
        "weather.temperature_2m", "DE-LU", "bidding_zone"
    )
    assert exc.type == f"wattfrosch.{METRIC_REGION_KIND_MISMATCH}"
