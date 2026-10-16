"""REGIONS catalog — region definitions per README §3.

Bidding zones and weather points, time-dependent (Slowly Changing Dimension
Type 2): a bidding zone can change over time and both the old and the new code
exist with half-open [valid_from, valid_to) validity windows, so historical
records stay queryable without rewriting data.

Code schema: "DE-LU" (country-country) for bidding zones, "DE-BERLIN"
(country-city) for weather points. The `kind` field is the actual
discriminator — codes alone are NOT unique across kinds (e.g. "DE-LU" and
"DE-BERLIN" have the same dash shape).
"""

from collections.abc import Mapping
from datetime import date
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from wattfrosch_contracts import errors

RegionKind = Literal["bidding_zone", "weather_point"]

BIDDING_ZONE: Final = "bidding_zone"
WEATHER_POINT: Final = "weather_point"

_KINDS: Final[frozenset[str]] = frozenset({BIDDING_ZONE, WEATHER_POINT})

_LAT_RANGE: Final = (-90.0, 90.0)
_LON_RANGE: Final = (-180.0, 180.0)


class RegionEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    kind: RegionKind
    country: str
    lat: float | None
    lon: float | None
    tz: str
    valid_from: date
    valid_to: date | None

    @model_validator(mode="after")
    def _validate_code(self) -> "RegionEntry":
        prefix = "-".join(self.country.split(","))
        if self.code != prefix and not self.code.startswith(f"{prefix}-"):
            raise errors.region_code_mismatch_error(self.code, self.country)
        if self.lat is not None and not (_LAT_RANGE[0] <= self.lat <= _LAT_RANGE[1]):
            raise errors.region_coords_out_of_range_error(self.code, "lat", self.lat)
        if self.lon is not None and not (_LON_RANGE[0] <= self.lon <= _LON_RANGE[1]):
            raise errors.region_coords_out_of_range_error(self.code, "lon", self.lon)
        return self


def _entry(
    code: str,
    name: str,
    kind: RegionKind,
    country: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: str = "Europe/Berlin",
    valid_from: date = date(2015, 1, 1),
    valid_to: date | None = None,
) -> RegionEntry:
    return RegionEntry(
        code=code,
        name=name,
        kind=kind,
        country=country,
        lat=lat,
        lon=lon,
        tz=tz,
        valid_from=valid_from,
        valid_to=valid_to,
    )


REGIONS: Final[Mapping[str, RegionEntry]] = {
    entry.code: entry
    for entry in (
        # Bidding-zone history: DE-AT-LU until 2018-09-30, DE-LU afterwards.
        _entry(
            "DE-AT-LU",
            "Germany/Austria/Luxembourg bidding zone",
            BIDDING_ZONE,
            "DE,AT,LU",
            valid_to=date(2018, 10, 1),
        ),
        _entry(
            "DE-LU",
            "Germany/Luxembourg bidding zone",
            BIDDING_ZONE,
            "DE,LU",
            valid_from=date(2018, 10, 1),
        ),
        # Weather points (v1: Berlin, Hamburg, Köln, München).
        _entry(
            "DE-BERLIN",
            "Berlin",
            WEATHER_POINT,
            "DE",
            lat=52.52,
            lon=13.405,
        ),
        _entry(
            "DE-HAMBURG",
            "Hamburg",
            WEATHER_POINT,
            "DE",
            lat=53.551,
            lon=9.993,
        ),
        _entry(
            "DE-KOELN",
            "Köln",
            WEATHER_POINT,
            "DE",
            lat=50.937,
            lon=6.96,
        ),
        _entry(
            "DE-MUENCHEN",
            "München",
            WEATHER_POINT,
            "DE",
            lat=48.137,
            lon=11.575,
        ),
    )
}
