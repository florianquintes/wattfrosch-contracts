"""Contract error types.

Raised (via PydanticCustomError) when a MeasurementRecord references a key
that is not part of the catalogs or a region that is not valid at the
record's timestamp. Callers catch pydantic.ValidationError and can inspect
``exc.errors()[0]["type"]`` for the machine-readable error kind.
"""

from pydantic_core import PydanticCustomError

ERROR_PREFIX = "wattfrosch"

UNKNOWN_METRIC = "unknown_metric"
UNKNOWN_SOURCE = "unknown_source"
UNKNOWN_REGION = "unknown_region"
REGION_NOT_VALID = "region_not_valid"
TS_UTC_NOT_DATETIME = "ts_utc_not_datetime"


def ts_utc_not_datetime_error(value: object) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{TS_UTC_NOT_DATETIME}",
        "ts_utc must be a datetime or ISO string, not a unix timestamp: {value!r}",
        {"value": value},
    )


def unknown_metric_error(metric: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{UNKNOWN_METRIC}",
        "Unknown metric key: '{metric}'",
        {"metric": metric},
    )


def unknown_source_error(source: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{UNKNOWN_SOURCE}",
        "Unknown source name: '{source}'",
        {"source": source},
    )


def unknown_region_error(region: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{UNKNOWN_REGION}",
        "Unknown region code: '{region}'",
        {"region": region},
    )


def region_not_valid_error(region: str, ts: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{REGION_NOT_VALID}",
        "Region '{region}' is not valid at {ts}",
        {"region": region, "ts": ts},
    )
