"""Tests for SOURCES and the translation maps (README §4–§6, TODO Issue 6).

Covers catalog integrity, the https-url rule, map integrity (every referenced
source/metric/region exists in the catalogs) and the fill status: the smard
metric map covers all energy metrics except oil (no documented filter).
"""

import pytest
from pydantic import ValidationError

from wattfrosch_contracts import METRICS, REGIONS, SOURCES

URL_NOT_HTTPS = "wattfrosch.source_url_not_https"


def error_type(exc: ValidationError) -> str:
    return exc.errors()[0]["type"]


def make_source(**overrides: object) -> object:
    from wattfrosch_contracts.sources import SourceEntry

    base: dict[str, object] = {
        "name": "test-source",
        "license": "CC BY 4.0",
        "url": "https://example.com",
    }
    base.update(overrides)
    return SourceEntry(**base)  # type: ignore[arg-type]


# --- SOURCES catalog -------------------------------------------------------


def test_catalog_not_empty() -> None:
    assert len(SOURCES) > 0


def test_expected_sources_present() -> None:
    assert set(SOURCES) == {"energy-charts", "smard", "open-meteo"}


def test_dict_keys_match_entry_names() -> None:
    for name, entry in SOURCES.items():
        assert name == entry.name


def test_all_urls_are_https() -> None:
    for entry in SOURCES.values():
        assert entry.url.startswith("https://")


def test_licenses_present() -> None:
    for entry in SOURCES.values():
        assert entry.license


def test_non_https_url_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_source(url="http://example.com")
    assert error_type(excinfo.value) == URL_NOT_HTTPS


def test_frozen_model_rejects_mutation() -> None:
    entry = SOURCES["smard"]
    with pytest.raises(ValidationError) as excinfo:
        entry.name = "other"  # type: ignore[misc]
    assert error_type(excinfo.value) == "frozen_instance"


# --- Map integrity ----------------------------------------------------------


def test_metric_map_sources_exist() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    for source in SOURCE_METRIC_MAP:
        assert source in SOURCES


def test_metric_map_internal_keys_exist() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    for translations in SOURCE_METRIC_MAP.values():
        for internal_key in translations:
            assert internal_key in METRICS


def test_region_map_sources_exist() -> None:
    from wattfrosch_contracts import SOURCE_REGION_MAP

    for source in SOURCE_REGION_MAP:
        assert source in SOURCES


def test_region_map_internal_codes_exist() -> None:
    from wattfrosch_contracts import SOURCE_REGION_MAP

    for translations in SOURCE_REGION_MAP.values():
        for internal_code in translations:
            assert internal_code in REGIONS


def test_no_map_references_at() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP, SOURCE_REGION_MAP

    for translations in SOURCE_METRIC_MAP.values():
        assert not any(key.startswith("AT") for key in translations)
    for translations in SOURCE_REGION_MAP.values():
        assert not any(key.startswith("AT") for key in translations)


# --- Fill status -------------------------------------------------------------


def test_smard_metric_map_no_weather() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    smard_keys = SOURCE_METRIC_MAP["smard"]
    assert not any(key.startswith("weather.") for key in smard_keys)
    assert any(key.startswith("price.") for key in smard_keys)


def test_energy_charts_metric_keys_map_to_themselves() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    translations = SOURCE_METRIC_MAP["energy-charts"]
    assert all(internal == external for internal, external in translations.items())


def test_open_meteo_covers_all_weather_metrics() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    weather_keys = {key for key in METRICS if key.startswith("weather.")}
    assert set(SOURCE_METRIC_MAP["open-meteo"]) == weather_keys


def test_energy_charts_covers_all_energy_metrics() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    energy_keys = {key for key in METRICS if not key.startswith("weather.")}
    assert set(SOURCE_METRIC_MAP["energy-charts"]) == energy_keys


def test_smard_covers_all_energy_metrics_except_oil() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    energy_keys = {
        key
        for key in METRICS
        if not key.startswith("weather.") and key != "generation.oil"
    }
    assert set(SOURCE_METRIC_MAP["smard"]) == energy_keys


def test_smard_filters_are_documented_ids() -> None:
    from wattfrosch_contracts import SOURCE_METRIC_MAP

    documented = {
        "410",
        "1223",
        "1224",
        "1225",
        "1226",
        "1227",
        "1228",
        "4066",
        "4067",
        "4068",
        "4069",
        "4070",
        "4071",
        "4169",
        "4359",
        "4387",
    }
    assert set(SOURCE_METRIC_MAP["smard"].values()) == documented


def test_open_meteo_region_map_uses_lat_lon() -> None:
    from wattfrosch_contracts import SOURCE_REGION_MAP

    for code, external in SOURCE_REGION_MAP["open-meteo"].items():
        lat, lon = REGIONS[code].lat, REGIONS[code].lon
        assert external == f"{lat},{lon}"


def test_open_meteo_covers_all_weather_points() -> None:
    from wattfrosch_contracts import SOURCE_REGION_MAP

    weather_points = {
        code for code, entry in REGIONS.items() if entry.kind == "weather_point"
    }
    assert set(SOURCE_REGION_MAP["open-meteo"]) == weather_points


def test_smard_and_energy_charts_cover_bidding_zones() -> None:
    from wattfrosch_contracts import SOURCE_REGION_MAP

    bidding_zones = {
        code for code, entry in REGIONS.items() if entry.kind == "bidding_zone"
    }
    for source in ("smard", "energy-charts"):
        assert set(SOURCE_REGION_MAP[source]) == bidding_zones
