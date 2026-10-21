# wattfrosch-contracts

Single source of truth for the interfaces between all wattfrosch modules.
Contains definitions only — no logic, no network or database access.

Part of the [wattfrosch](https://github.com/florianquintes/wattfrosch) module
family.

## What is this?

wattfrosch is built from small, independently usable modules (fetch, store,
transform, pipeline, forecast, dashboard, platform). This package is the
shared contract core: it defines the shape of the data that flows between
them, so no module has to install the entire data-fetch stack (HTTP libraries,
retry logic, etc.) just to know what a record looks like.

This package is the shared core, but it is NOT the only dependency point in
the system — there are directed dependencies between modules as well
(e.g. store → fetch, transform → store).

It provides:

- `MeasurementRecord` — the exchange format for a single measurement
- `METRICS` — the metric catalog
- `REGIONS` — the region catalog (bidding zones + weather points)
- `SOURCES` — the source catalog
- `SOURCE_METRIC_MAP` / `SOURCE_REGION_MAP` — internal → external key maps
- `CONTRACT_VERSION` — one version for the entire contract set
- error-type constants (`wattfrosch.*`) for machine-readable validation errors

### MeasurementRecord

A single measurement. Immutable and self-validating, implemented with pydantic.

| Field | Type | Rule |
|---|---|---|
| `ts_utc` | `AwareDatetime` | tz-aware; naive input rejected, non-UTC offsets converted to UTC, unix timestamps (int/float) rejected; start of the interval |
| `region` | `str` | must exist in REGIONS and be valid at `ts_utc` |
| `metric` | `str` | must exist in METRICS |
| `value` | `float` | finite; no NaN, no Inf |
| `source` | `str` | must exist in SOURCES |
| `resolution` | `Literal["PT1H"]` | ISO-8601 duration; v1 only hourly, enforced at the type level |

Design rules:

- The unit lives in the METRIC, not in the record.
- Missing values are NOT rows with `value=NULL`, but missing rows; gaps are
  filled later in transform.
- The time interval is half-open `[start, end)`; `ts_utc` is the interval
  start, `end = start + resolution`.
- The metric's category must match the region kind: generation, consumption
  and price require a `bidding_zone`; weather requires a `weather_point`.
- `ingested_at` is NOT part of the record (storage metadata belongs to store).
- Errors are pydantic `PydanticCustomError`s with machine-readable types
  (`wattfrosch.unknown_metric`, `wattfrosch.unknown_region`,
  `wattfrosch.region_not_valid`, ...); catch `pydantic.ValidationError` and
  inspect `exc.errors()[0]["type"]`.

### METRICS

Catalog of all metrics; the v1 list has 21 entries (13 generation,
3 consumption, 1 price, 4 weather) and is filled completely at implementation
start — an unknown key raises an error.

Fields per metric: `key` (schema `"<category>.<name>"`), `unit` (e.g. "MW",
"EUR/MWh", "K"), `category` (generation | consumption | price | weather),
`aggregation` (mean | sum | max | min), `derived`, `description`,
`is_renewable`, `can_be_negative`, `plausible_range`, `display_name`,
`valid_from`, `valid_to`.

Notable rules: the key→category map is leading and strictly validated;
`derived=true` metrics are never fetched (only computed in transform);
weather units are kelvin (K), m/s, mm and % — fetch converts from source
units. Planned for v0.2.*: `weather.wind_speed_100m` and a radiation metric.

### REGIONS

Bidding zones and weather points; 6 entries in v1.

Fields per region: `code` ("DE-LU" / "DE-BERLIN"), `name`, `kind`
(`bidding_zone` | `weather_point`), `country`, `lat`, `lon`, `tz`,
`valid_from`, `valid_to`.

Notable rules: regions are time-dependent (SCD Type 2) — `DE-AT-LU` is valid
until 2018-10-01, `DE-LU` from 2018-10-01, so backfills across the zone change
work without rewriting data. `AT` alone is not an allowed region. v1 weather
points: Berlin, Hamburg, Köln, München.

### SOURCES

Fields: `name`, `license`, `url` (must be https). v1: energy-charts
(Fraunhofer ISE), smard (Bundesnetzagentur), open-meteo — all CC BY 4.0.

### CONTRACT_VERSION

Semantic versioning MAJOR.MINOR.PATCH for the whole contract set:
MINOR = new metric/region/source/optional field/new allowed resolution;
MAJOR = field rename/remove, unit or meaning change; PATCH = internal fixes.

The static `project.version` in `pyproject.toml` is the single source of truth;
`version.py` resolves `CONTRACT_VERSION` via `importlib.metadata` (with a
`pyproject.toml` fallback when running from source).

## Installation

Requires Python 3.13+ (`requires-python >= 3.13`). The only runtime dependency
is `pydantic>=2`.

```sh
uv add wattfrosch-contracts
# or
pip install wattfrosch-contracts
```

From source:

```sh
git clone https://github.com/florianquintes/wattfrosch-contracts
cd wattfrosch-contracts
uv sync --dev
```

## Usage

```python
from datetime import datetime, UTC

from wattfrosch_contracts import (
    MeasurementRecord, METRICS, REGIONS, SOURCES,
    SOURCE_METRIC_MAP, SOURCE_REGION_MAP, CONTRACT_VERSION,
)

record = MeasurementRecord(
    ts_utc=datetime(2026, 10, 10, 12, 0, tzinfo=UTC),
    region="DE-LU",
    metric="consumption.load",
    value=42150.0,
    source="smard",
    resolution="PT1H",
)

record.value        # 42150.0
METRICS[record.metric].unit   # "MW"
CONTRACT_VERSION    # "0.1.0"
```

Construction validates everything: the metric, source and region keys must
exist in the catalogs, the region must be valid at `ts_utc`, the value must be
finite, and the metric's category must match the region's kind. An invalid
record raises a `pydantic.ValidationError` with a machine-readable
`wattfrosch.*` error type.

The catalog entry models `MetricEntry`, `RegionEntry` and `SourceEntry` are
importable from their submodules (`metrics.py`, `regions.py`, `sources.py`)
but deliberately not re-exported from `__init__` — consumers read the
catalogs, not the entry classes.

## Contributing

Tooling is uv (Python 3.13):

```bash
uv sync --dev                          # install deps into .venv
uv run pytest                          # tests
uv run ruff format --check .           # formatting check
uv run ruff check .                    # lint
uv run pyrefly check .                 # type check
```

CI (`.github/workflows/`) runs on every push/PR: `ruff format --check`,
`ruff check`, `pytest`, `pyrefly check` — all must pass.

Conventions:

- Type checking is **pyrefly** (always use pyrefly, not mypy).
- Tests live in root-level `tests/` (pytest resolves imports via
  `pythonpath = ["src"]`).
- Keep the package dependency-free except pydantic — adding HTTP/DB libraries
  here breaks the architecture (every other wattfrosch module depends on this
  one).
- Applied contract versions are frozen: renaming/removing a field, changing a
  unit or a meaning is a MAJOR change; adding a metric/region/source or an
  optional field is MINOR.
- Release procedure: bump `project.version` in `pyproject.toml` and set the
  git tag together.

Open points:

- Verify the best-effort license/url values and external codes in the maps.
- Maintain the bidding-zone history.
- v0.2.*: add `weather.wind_speed_100m` and a radiation metric.

## Mappings

The same signal has a different name in each source. The two translation maps
translate internal keys to source-specific external keys. They are deliberately
NOT part of METRICS/REGIONS, so the catalogs stay clean.
`SOURCE_REGION_MAP` needs no time logic — region history lives in REGIONS
(SCD Type 2), one entry per internal code is enough.

### SOURCE_METRIC_MAP — internal metric key → external metric key

**energy-charts** uses the same key names as the internal metric keys
(identity mapping) for all 17 energy metrics:
`generation.biomass`, `generation.gas`, `generation.hard_coal`,
`generation.hydro`, `generation.lignite`, `generation.nuclear`,
`generation.oil`, `generation.other`, `generation.other_renewable`,
`generation.pumped_storage`, `generation.solar`, `generation.wind_offshore`,
`generation.wind_onshore`, `consumption.load`, `consumption.residual_load`,
`consumption.pumped_storage`, `price.day_ahead`.

**open-meteo** uses its raw API variable names for the weather metrics:

| Internal key | Open-Meteo variable |
|---|---|
| `weather.temperature_2m` | `temperature_2m` |
| `weather.wind_speed_10m` | `wind_speed_10m` |
| `weather.precipitation` | `precipitation` |
| `weather.cloud_cover` | `cloud_cover` |

**smard** uses numeric filter IDs from the SMARD API readme
(price filter 4169 is documented separately from that readme's filter list):

| Internal key | SMARD filter |
|---|---|
| `generation.lignite` | `1223` |
| `generation.nuclear` | `1224` |
| `generation.wind_offshore` | `1225` |
| `generation.hydro` | `1226` |
| `generation.other` | `1227` |
| `generation.other_renewable` | `1228` |
| `generation.biomass` | `4066` |
| `generation.wind_onshore` | `4067` |
| `generation.solar` | `4068` |
| `generation.hard_coal` | `4069` |
| `generation.pumped_storage` | `4070` |
| `generation.gas` | `4071` |
| `consumption.load` | `410` |
| `consumption.residual_load` | `4359` |
| `consumption.pumped_storage` | `4387` |
| `price.day_ahead` | `4169` |

Notes: `generation.oil` has no documented smard filter — it is only available
via energy-charts. Weather metrics are not covered by smard.

### SOURCE_REGION_MAP — internal region code → external region code

| Internal code | smard | energy-charts | open-meteo |
|---|---|---|---|
| `DE-AT-LU` | `DE-AT-LU` | `de-at-lu` | — |
| `DE-LU` | `DE-LU` | `de-lu` | — |
| `DE-BERLIN` | — | — | `52.52,13.405` |
| `DE-HAMBURG` | — | — | `53.551,9.993` |
| `DE-KOELN` | — | — | `50.937,6.96` |
| `DE-MUENCHEN` | — | — | `48.137,11.575` |

Bidding zones are covered by smard and energy-charts; weather points
("lat,lon" strings) by open-meteo.

## License

See [LICENSE](LICENSE).
