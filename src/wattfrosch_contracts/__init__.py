"""Shared contracts for the wattfrosch module family (models + catalogs only)."""

from wattfrosch_contracts.errors import (
    METRIC_CATEGORY_MISMATCH,
    METRIC_REGION_KIND_MISMATCH,
    REGION_NOT_VALID,
    TS_UTC_NOT_DATETIME,
    UNKNOWN_METRIC,
    UNKNOWN_REGION,
    UNKNOWN_SOURCE,
)
from wattfrosch_contracts.metrics import METRICS
from wattfrosch_contracts.records import MeasurementRecord
from wattfrosch_contracts.version import CONTRACT_VERSION

__all__ = [
    "CONTRACT_VERSION",
    "METRICS",
    "METRIC_CATEGORY_MISMATCH",
    "METRIC_REGION_KIND_MISMATCH",
    "REGION_NOT_VALID",
    "TS_UTC_NOT_DATETIME",
    "UNKNOWN_METRIC",
    "UNKNOWN_REGION",
    "UNKNOWN_SOURCE",
    "MeasurementRecord",
]
