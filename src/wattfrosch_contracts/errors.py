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
METRIC_CATEGORY_MISMATCH = "metric_category_mismatch"
METRIC_REGION_KIND_MISMATCH = "metric_region_kind_mismatch"
REGION_CODE_MISMATCH = "region_code_mismatch"
REGION_COORDS_OUT_OF_RANGE = "region_coords_out_of_range"
SOURCE_NAME_MISMATCH = "source_name_mismatch"
SOURCE_URL_NOT_HTTPS = "source_url_not_https"


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


def metric_category_mismatch_error(key: str, category: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{METRIC_CATEGORY_MISMATCH}",
        "Metric key '{key}' does not match category '{category}' (key schema "
        "'<category>.<name>')",
        {"key": key, "category": category},
    )


def metric_region_kind_mismatch_error(
    metric: str, region: str, kind: str
) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{METRIC_REGION_KIND_MISMATCH}",
        "Metric '{metric}' is not allowed on region kind '{kind}' (region '{region}')",
        {"metric": metric, "region": region, "kind": kind},
    )


def region_code_mismatch_error(code: str, country: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{REGION_CODE_MISMATCH}",
        "Region code '{code}' does not start with a country listed in "
        "'{country}' (comma-separated)",
        {"code": code, "country": country},
    )


def region_coords_out_of_range_error(
    code: str, field: str, value: float
) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{REGION_COORDS_OUT_OF_RANGE}",
        "Region '{code}' has {field}={value} outside its valid range",
        {"code": code, "field": field, "value": value},
    )


def source_name_mismatch_error(key: str, name: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{SOURCE_NAME_MISMATCH}",
        "Source key '{key}' does not match its name field '{name}'",
        {"key": key, "name": name},
    )


def source_url_not_https_error(name: str, url: str) -> PydanticCustomError:
    return PydanticCustomError(
        f"{ERROR_PREFIX}.{SOURCE_URL_NOT_HTTPS}",
        "Source '{name}' has a non-https url: '{url}'",
        {"name": name, "url": url},
    )
