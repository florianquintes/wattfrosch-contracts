"""Shared contracts for the wattfrosch module family (models + catalogs only)."""

from wattfrosch_contracts.errors import (
    METRIC_CATEGORY_MISMATCH,
    METRIC_REGION_KIND_MISMATCH,
    REGION_CODE_MISMATCH,
    REGION_COORDS_OUT_OF_RANGE,
    REGION_NOT_VALID,
    SOURCE_NAME_MISMATCH,
    SOURCE_URL_NOT_HTTPS,
    TS_UTC_NOT_DATETIME,
    UNKNOWN_METRIC,
    UNKNOWN_REGION,
    UNKNOWN_SOURCE,
)
from wattfrosch_contracts.metrics import METRICS
from wattfrosch_contracts.records import MeasurementRecord
from wattfrosch_contracts.regions import REGIONS
from wattfrosch_contracts.sources import (
    SOURCE_METRIC_MAP,
    SOURCE_REGION_MAP,
    SOURCES,
)
from wattfrosch_contracts.version import CONTRACT_VERSION

__all__ = [
    "CONTRACT_VERSION",
    "METRICS",
    "METRIC_CATEGORY_MISMATCH",
    "METRIC_REGION_KIND_MISMATCH",
    "REGIONS",
    "REGION_CODE_MISMATCH",
    "REGION_COORDS_OUT_OF_RANGE",
    "REGION_NOT_VALID",
    "SOURCES",
    "SOURCE_METRIC_MAP",
    "SOURCE_NAME_MISMATCH",
    "SOURCE_REGION_MAP",
    "SOURCE_URL_NOT_HTTPS",
    "TS_UTC_NOT_DATETIME",
    "UNKNOWN_METRIC",
    "UNKNOWN_REGION",
    "UNKNOWN_SOURCE",
    "MeasurementRecord",
]
