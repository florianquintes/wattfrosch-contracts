"""Tests for the REGIONS catalog (README §3, TODO Issue 5).

Covers catalog integrity, code↔country consistency, coordinate bounds,
SCD Type 2 history boundaries (half-open [valid_from, valid_to)) and the
frozen model. AT is not an allowed region (removed from the catalog).
"""

from datetime import date

import pytest
from pydantic import ValidationError

from wattfrosch_contracts import REGIONS

CODE_MISMATCH = "wattfrosch.region_code_mismatch"
COORDS_OUT_OF_RANGE = "wattfrosch.region_coords_out_of_range"


def error_type(exc: ValidationError) -> str:
    return exc.errors()[0]["type"]


def make_region(**overrides: object) -> object:
    from wattfrosch_contracts.regions import RegionEntry

    base: dict[str, object] = {
        "code": "DE-TESTSTADT",
        "name": "Teststadt",
        "kind": "weather_point",
        "country": "DE",
        "lat": None,
        "lon": None,
        "tz": "Europe/Berlin",
        "valid_from": date(2015, 1, 1),
        "valid_to": None,
    }
    base.update(overrides)
    return RegionEntry(**base)  # type: ignore[arg-type]


# --- Catalog integrity ----------------------------------------------------


def test_catalog_not_empty() -> None:
    assert len(REGIONS) > 0


def test_dict_keys_match_entry_codes() -> None:
    for code, entry in REGIONS.items():
        assert code == entry.code


def test_both_kinds_present() -> None:
    kinds = {entry.kind for entry in REGIONS.values()}
    assert kinds == {"bidding_zone", "weather_point"}


def test_expected_codes_present() -> None:
    assert {
        "DE-AT-LU",
        "DE-LU",
        "DE-BERLIN",
        "DE-HAMBURG",
        "DE-KOELN",
        "DE-MUENCHEN",
    } == set(REGIONS)


# --- Code ↔ country consistency ------------------------------------------


def test_code_country_prefix_matches_country_field() -> None:
    for entry in REGIONS.values():
        code_country = entry.code.partition("-")[0]
        assert code_country in entry.country.split(",")


def test_code_country_mismatch_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_region(code="FR-PARIS", country="DE")
    assert error_type(excinfo.value) == CODE_MISMATCH


def test_code_country_mismatch_error_message_contains_parts() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_region(code="FR-PARIS", country="DE")
    message = excinfo.value.errors()[0]["msg"]
    assert "FR-PARIS" in message
    assert "DE" in message


def test_code_without_dash_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_region(code="DETESTSTADT")
    assert error_type(excinfo.value) == CODE_MISMATCH


def test_multi_country_comma_list_accepted() -> None:
    region = make_region(code="DE-AT-LU", kind="bidding_zone", country="DE,AT,LU")
    assert region.country == "DE,AT,LU"  # type: ignore[attr-defined]


# --- Coordinate bounds ----------------------------------------------------


def test_weather_points_have_coordinates() -> None:
    for entry in REGIONS.values():
        if entry.kind == "weather_point":
            assert entry.lat is not None
            assert entry.lon is not None


def test_lat_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_region(lat=91.0)
    assert error_type(excinfo.value) == COORDS_OUT_OF_RANGE


def test_lon_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_region(lon=-181.0)
    assert error_type(excinfo.value) == COORDS_OUT_OF_RANGE


@pytest.mark.parametrize(
    ("lat", "lon"),
    [(-90.0, -180.0), (90.0, 180.0), (0.0, 0.0)],
)
def test_boundary_coordinates_accepted(lat: float, lon: float) -> None:
    region = make_region(lat=lat, lon=lon)
    assert region.lat == lat  # type: ignore[attr-defined]
    assert region.lon == lon  # type: ignore[attr-defined]


# --- SCD Type 2 history (half-open [valid_from, valid_to)) ----------------


def test_de_at_lu_validity_window() -> None:
    entry = REGIONS["DE-AT-LU"]
    assert entry.valid_from == date(2015, 1, 1)
    assert entry.valid_to == date(2018, 10, 1)


def test_de_lu_validity_window() -> None:
    entry = REGIONS["DE-LU"]
    assert entry.valid_from == date(2018, 10, 1)
    assert entry.valid_to is None


def test_history_has_no_gap_or_overlap() -> None:
    end = REGIONS["DE-AT-LU"].valid_to
    start = REGIONS["DE-LU"].valid_from
    assert end == start


def test_weather_points_currently_valid() -> None:
    for code in ("DE-BERLIN", "DE-HAMBURG", "DE-KOELN", "DE-MUENCHEN"):
        assert REGIONS[code].valid_to is None
        assert REGIONS[code].valid_from == date(2015, 1, 1)


def test_at_not_in_catalog() -> None:
    assert "AT" not in REGIONS


# --- Frozen model ---------------------------------------------------------


def test_frozen_model_rejects_mutation() -> None:
    entry = REGIONS["DE-LU"]
    with pytest.raises(ValidationError) as excinfo:
        entry.name = "x"
    assert error_type(excinfo.value) == "frozen_instance"
