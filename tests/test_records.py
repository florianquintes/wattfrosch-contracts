"""Tests for MeasurementRecord validation rules (README §1, TODO Issue 3).

Requirements (as changed):
- ts_utc is AwareDatetime: naive input is rejected, non-UTC offsets are
  normalized to UTC, unix timestamps (int/float) are rejected.
- AT is not an allowed region (removed from the catalog).
"""

import re
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from wattfrosch_contracts import MeasurementRecord

BASE = {
    "ts_utc": "2024-06-01T12:00:00Z",
    "region": "DE-LU",
    "metric": "generation.solar",
    "value": 1.0,
    "source": "energy-charts",
    "resolution": "PT1H",
}


def make_record(**overrides: object) -> MeasurementRecord:
    return MeasurementRecord(**{**BASE, **overrides})  # type: ignore[arg-type]


def error_type(exc: ValidationError) -> str:
    return exc.errors()[0]["type"]


# --- Happy path ---------------------------------------------------------


def test_valid_record_constructs() -> None:
    record = make_record()
    assert record.region == "DE-LU"
    assert record.metric == "generation.solar"
    assert record.value == 1.0
    assert record.source == "energy-charts"
    assert record.resolution == "PT1H"


def test_no_unit_or_ingested_at_field() -> None:
    make_record()
    assert "unit" not in MeasurementRecord.model_fields
    assert "ingested_at" not in MeasurementRecord.model_fields


# --- Dateformat handling -------------------------------------------------


@pytest.mark.parametrize(
    ("ts", "expected"),
    [
        ("2024-06-01T14:00:00+02:00", datetime(2024, 6, 1, 12, 0, tzinfo=UTC)),
        ("2024-06-01T12:00:00+00:00", datetime(2024, 6, 1, 12, 0, tzinfo=UTC)),
        ("2024-06-01T12:00:00Z", datetime(2024, 6, 1, 12, 0, tzinfo=UTC)),
    ],
)
def test_offsets_normalized_to_utc(ts: str, expected: datetime) -> None:
    assert make_record(ts_utc=ts).ts_utc == expected


@pytest.mark.parametrize(
    "ts",
    [
        "2024-06-01T12:00:00",  # naive ISO string
        datetime(2024, 6, 1, 12, 0),  # naive datetime object
    ],
)
def test_naive_input_rejected(ts: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(ts_utc=ts)
    assert error_type(excinfo.value) == "timezone_aware"


@pytest.mark.parametrize("ts", [1.5, 1750000000])
def test_unix_timestamp_rejected(ts: float) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(ts_utc=ts)
    assert error_type(excinfo.value) == "wattfrosch.ts_utc_not_datetime"


@pytest.mark.parametrize("ts", ["not-a-date", None])
def test_garbage_ts_rejected(ts: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(ts_utc=ts)
    assert error_type(excinfo.value) != "wattfrosch.ts_utc_not_datetime"


# --- Value validation ----------------------------------------------------


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_value_rejected(value: float) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(value=value)
    assert error_type(excinfo.value) == "finite_number"


# --- Catalog keys ---------------------------------------------------------


def test_unknown_metric_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(metric="generation.nonexistent")
    assert error_type(excinfo.value) == "wattfrosch.unknown_metric"


def test_unknown_source_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(source="not-a-source")
    assert error_type(excinfo.value) == "wattfrosch.unknown_source"


def test_unknown_region_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(region="XX-YY")
    assert error_type(excinfo.value) == "wattfrosch.unknown_region"


# --- Category → region-kind rule ------------------------------------------


def test_weather_metric_on_bidding_zone_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(metric="weather.temperature_2m", region="DE-LU", value=280.0)
    assert error_type(excinfo.value) == "wattfrosch.metric_region_kind_mismatch"


def test_generation_metric_on_weather_point_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(metric="generation.solar", region="DE-BERLIN")
    assert error_type(excinfo.value) == "wattfrosch.metric_region_kind_mismatch"


def test_weather_metric_on_weather_point_accepted() -> None:
    record = make_record(
        metric="weather.temperature_2m", region="DE-BERLIN", value=280.0
    )
    assert record.metric == "weather.temperature_2m"
    assert record.region == "DE-BERLIN"


# --- Region validity + bidding-zone history -------------------------------


def test_de_lu_before_history_start_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(region="DE-LU", ts_utc="2016-01-01T00:00:00Z")
    assert error_type(excinfo.value) == "wattfrosch.region_not_valid"


def test_de_at_lu_after_history_end_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(region="DE-AT-LU", ts_utc="2018-10-01T00:00:00Z")
    assert error_type(excinfo.value) == "wattfrosch.region_not_valid"


def test_boundary_de_at_lu_still_valid_before_end() -> None:
    record = make_record(region="DE-AT-LU", ts_utc="2018-09-30T23:00:00Z")
    assert record.region == "DE-AT-LU"


def test_boundary_de_lu_valid_from_start() -> None:
    record = make_record(region="DE-LU", ts_utc="2018-10-01T00:00:00Z")
    assert record.region == "DE-LU"


def test_at_not_an_allowed_region() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(region="AT", ts_utc="2024-06-01T12:00:00Z")
    assert error_type(excinfo.value) == "wattfrosch.unknown_region"


# --- Resolution + immutability -------------------------------------------


@pytest.mark.parametrize("resolution", ["PT15M", "PT1H "])
def test_wrong_resolution_rejected(resolution: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(resolution=resolution)
    assert error_type(excinfo.value) == "literal_error"


def test_frozen_model_rejects_mutation() -> None:
    record = make_record()
    with pytest.raises(ValidationError) as excinfo:
        record.value = 2.0
    assert error_type(excinfo.value) == "frozen_instance"


def test_error_message_contains_region_and_ts() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_record(region="DE-LU", ts_utc="2016-01-01T00:00:00Z")
    message = excinfo.value.errors()[0]["msg"]
    assert "DE-LU" in message
    assert re.search(r"2016-01-01", message)
