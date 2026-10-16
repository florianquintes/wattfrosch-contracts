"""MeasurementRecord — exchange format for a single measurement (README §1).

Immutable and self-validating. The unit lives in the metric catalog, not in
the record; missing values are missing rows, never NULL; the interval is
half-open [ts_utc, ts_utc + resolution); times are UTC only.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
)

from wattfrosch_contracts import errors
from wattfrosch_contracts.metrics import METRICS
from wattfrosch_contracts.regions import REGIONS
from wattfrosch_contracts.sources import SOURCES


class MeasurementRecord(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    ts_utc: AwareDatetime
    region: str
    metric: str
    value: float
    source: str
    resolution: Literal["PT1H"]

    @field_validator("ts_utc", mode="before")
    @classmethod
    def _reject_unix_timestamps(cls, v: object) -> object:
        if isinstance(v, (int, float)):
            raise errors.ts_utc_not_datetime_error(v)
        return v

    @field_validator("ts_utc")
    @classmethod
    def _normalize_to_utc(cls, v: datetime) -> datetime:
        return v.astimezone(UTC)

    @model_validator(mode="after")
    def _validate_catalog_keys(self) -> "MeasurementRecord":
        if self.metric not in METRICS:
            raise errors.unknown_metric_error(self.metric)
        if self.source not in SOURCES:
            raise errors.unknown_source_error(self.source)
        region = REGIONS.get(self.region)
        if region is None:
            raise errors.unknown_region_error(self.region)
        ts_date = self.ts_utc.date()
        if not (
            region.valid_from <= ts_date
            and (region.valid_to is None or ts_date < region.valid_to)
        ):
            raise errors.region_not_valid_error(self.region, self.ts_utc.isoformat())
        return self
