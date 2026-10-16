"""Shared contracts for the wattfrosch module family (models + catalogs only)."""

from wattfrosch_contracts.errors import (
    REGION_NOT_VALID,
    UNKNOWN_METRIC,
    UNKNOWN_REGION,
    UNKNOWN_SOURCE,
)
from wattfrosch_contracts.records import MeasurementRecord
from wattfrosch_contracts.version import CONTRACT_VERSION

__all__ = [
    "CONTRACT_VERSION",
    "REGION_NOT_VALID",
    "UNKNOWN_METRIC",
    "UNKNOWN_REGION",
    "UNKNOWN_SOURCE",
    "MeasurementRecord",
]
