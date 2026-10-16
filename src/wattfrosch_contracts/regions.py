"""REGIONS catalog — v1 stub.

Replaced by Issue 5 (full model + catalog per README §3). Only what the
MeasurementRecord validators need exists here, but the bidding-zone history
already follows the real spec (SCD Type 2, half-open [valid_from, valid_to)).
"""

from collections.abc import Mapping
from datetime import date
from typing import Final, NamedTuple


class RegionStub(NamedTuple):
    code: str
    kind: str
    valid_from: date
    valid_to: date | None


BIDDING_ZONE: Final = "bidding_zone"
WEATHER_POINT: Final = "weather_point"

REGIONS: Final[Mapping[str, RegionStub]] = {
    # Bidding-zone history: DE-AT-LU until 2018-09-30, DE-LU and AT afterwards.
    "DE-AT-LU": RegionStub(
        code="DE-AT-LU",
        kind=BIDDING_ZONE,
        valid_from=date(2015, 1, 1),
        valid_to=date(2018, 10, 1),
    ),
    "DE-LU": RegionStub(
        code="DE-LU",
        kind=BIDDING_ZONE,
        valid_from=date(2018, 10, 1),
        valid_to=None,
    ),
    "AT": RegionStub(
        code="AT",
        kind=BIDDING_ZONE,
        valid_from=date(2018, 10, 1),
        valid_to=None,
    ),
    # Weather points (v1: Berlin, Hamburg, Köln, München).
    "DE-BERLIN": RegionStub(
        code="DE-BERLIN",
        kind=WEATHER_POINT,
        valid_from=date(2015, 1, 1),
        valid_to=None,
    ),
    "DE-HAMBURG": RegionStub(
        code="DE-HAMBURG",
        kind=WEATHER_POINT,
        valid_from=date(2015, 1, 1),
        valid_to=None,
    ),
    "DE-KOELN": RegionStub(
        code="DE-KOELN",
        kind=WEATHER_POINT,
        valid_from=date(2015, 1, 1),
        valid_to=None,
    ),
    "DE-MUENCHEN": RegionStub(
        code="DE-MUENCHEN",
        kind=WEATHER_POINT,
        valid_from=date(2015, 1, 1),
        valid_to=None,
    ),
}
