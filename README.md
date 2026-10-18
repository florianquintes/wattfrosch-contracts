# wattfrosch-contracts

Single source of truth for the interfaces between all wattfrosch modules.
Contains definitions only — no logic, no network or database access.

## Why a separate module?
So that no module has to install the entire data-fetch stack (HTTP libraries,
retry logic, etc.) just to know the shape of a record. All modules depend only
on this lightweight package.

## Dependencies
- depends on: nothing (except pydantic); otherwise standard library only
- used by: all modules (fetch, store, transform, pipeline, forecast, dashboard)

Note on architecture: this contract package is the shared core, but it is NOT the
only dependency point in the system. There are directed dependencies between
modules as well (e.g. store → fetch, transform → store). See the module map in
the central knowledge file.

## Contents (contract building blocks)

### 1. MeasurementRecord — exchange format
A single measurement. Immutable and self-validating, implemented with pydantic.

Fields:
- ts_utc      : datetime (timezone-aware, normalized to UTC; start of the interval).
                Typed as pydantic `AwareDatetime`: tz-awareness is enforced at the
                type level — naive input is rejected; non-UTC offsets are
                converted to UTC; unix timestamps (int/float) are rejected.
- region      : str      (region_code; must exist in REGIONS and be valid at ts_utc)
- metric      : str      (metric_key; must exist in METRICS)
- value       : float    (finite; no NaN, no Inf)
- source      : str      (source_name; must exist in SOURCES)
- resolution  : str      (ISO-8601 duration; v1 only "PT1H" = hourly)

Design rules:
- Immutable and self-validating (via pydantic).
- The unit lives in the METRIC, not in the record (prevents two units for the
  same metric).
- Missing values are NOT rows with value=NULL, but missing rows. Gaps are filled
  later in transform (time-series generation).
- The time interval is half-open [start, end); ts_utc is the interval start, and
  end = start + resolution.
- Times are UTC only. `ts_utc` is typed as pydantic `AwareDatetime`: naive input
  is rejected (tz-awareness is required to get the full time information);
  non-UTC offsets are converted to UTC; unix timestamps (int/float) are
  rejected.
- An unknown metric raises an error (this also surfaces external API changes
  immediately during operation).
- A region that is not valid at ts_utc raises an error.
- The metric's category must match the region kind: generation, consumption and
  price require a bidding_zone; weather requires a weather_point (mismatch
  raises).
- Parquet mirror (export): same columns as above.
- ingested_at is NOT part of the record (storage metadata belongs to store).

### 2. METRICS — metric catalog
Catalog of all metrics. The structure is fixed; the v1 list is deliberately
incomplete and filled manually.

Fields per metric:
- key             : str   (schema "<category>.<name>", e.g. "generation.solar")
- unit            : str   (e.g. "MW", "EUR/MWh", "°C")
- category        : str   (generation | consumption | price | weather)
- aggregation     : str   (time aggregation: mean | sum | max | min)
- derived         : bool  (true = NOT fetched; only computed in transform)
- description     : str
- is_renewable    : bool  (counts as renewable; used for renewable_share)
- can_be_negative : bool  (e.g. prices, pumped storage)
- plausible_range : (float, float) or None  (bounds for data-quality checks)
- display_name    : str   (readable label for the dashboard)
- valid_from      : date
- valid_to        : date or None  (None = currently valid)

Rules:
- Key schema "<category>.<name>"; the category is always the first segment.
- The key→category map is the leading source of truth and is strictly validated
  (mismatch between key and category raises an error).
- An unknown metric raises an error.
- derived=true → fetch never delivers this metric; it is only produced in transform.
- aggregation is the time aggregation (hour → day), not spatial.
- is_renewable is a field on the metric entry; there is no separate map
  (avoids duplication).
- Allowed region kind per category:
  generation, consumption, price → bidding_zone
  weather                      → weather_point
- Pumped storage: category=generation, can_be_negative=true, is_renewable=false
  (a storage unit can be charged from any source, including coal).
- weather.temperature_2m is in kelvin (K); its plausibility bounds are the
  coldest (170 K) and hottest (345 K) temperatures measured on earth. Fetch
  converts from source units.
- Both pumped-storage entries (generation.pumped_storage and
  consumption.pumped_storage) use negative = charging (mirrored convention).
- consumption.residual_load can be negative (renewable generation exceeds load).
- The v1 catalog has 21 entries (13 generation, 3 consumption, 1 price,
  4 weather); new metrics are added as needed.

### 3. REGIONS — region catalog
Bidding zones and weather points.

Fields per region:
- code        : str   (e.g. "DE-LU", "DE-BERLIN")
- name        : str
- kind        : str   ("bidding_zone" | "weather_point")
- country     : str
- lat, lon    : float or None
- tz          : str
- valid_from  : date       (from when this region is valid)
- valid_to    : date or None  (None = currently valid)

Rules:
- Code schema: "DE-LU" (country-country) for bidding zones, "DE-BERLIN"
  (country-city) for weather points. The `kind` field is the actual
  discriminator — codes alone are NOT unique.
- Generation/price/load always on the bidding zone; weather on weather points.
- Bidding zones can change over time (example: "DE-AT-LU" until 2018, afterwards
  "DE-LU" separately). valid_from/valid_to allows correct historical
  mapping without rewriting data (Slowly Changing Dimension Type 2).
- A region that is not valid at the requested timestamp raises an error
  (relevant for backfills before a bidding zone change).
- v1: four weather points (Berlin, Hamburg, Köln, München).
- The code's country prefix must match the `country` field (comma-separated
  list for multi-country zones: "DE-AT-LU" → country "DE,AT,LU"); mismatch
  raises `wattfrosch.region_code_mismatch`. Coordinates are bounds-checked
  (lat −90..90, lon −180..180; `wattfrosch.region_coords_out_of_range`).
- AT is not an allowed region (removed from the catalog); only the historical
  DE-AT-LU zone exists for backfills before 2018-10-01.

### 4. SOURCES — source catalog *(implemented)*
Fields: name, license, url. The url must be https
(`wattfrosch.source_url_not_https`).
v1: energy-charts (Fraunhofer ISE), smard (Bundesnetzagentur), open-meteo —
all CC BY 4.0 (best-effort values, verify before release).

### 5. SOURCE_METRIC_MAP — source → external key *(implemented; partially filled)*
The same signal has a different name in each source. This map maps the internal
metric_key to the source-specific key:

SOURCE_METRIC_MAP = {
    "smard":         {"generation.solar": "<external key>", ...},
    "energy-charts": {"generation.solar": "<external key>", ...},
}

fetch uses this map to request the correct external key. It is deliberately NOT
part of METRICS, so the metric stays clean. Fill status: energy-charts maps
every energy metric to itself (same-key assumption); open-meteo maps the four
weather metrics to its raw API variable names; smard maps the energy metrics
to the numeric filter IDs from the SMARD API readme (price filter 4169 is
documented separately from that readme's filter list; generation.oil has no
documented smard filter). Every referenced source and internal metric key must
exist in SOURCES/METRICS.

### 6. SOURCE_REGION_MAP — source → external region key *(implemented)*
The same zone has a different code in each source. This map translates the internal
region_code to the source-specific code:

SOURCE_REGION_MAP = {
    "smard":         {"DE-LU": "<external code>", ...},
    "energy-charts": {"DE-LU": "<external code>", ...},
}

Since region history lives in REGIONS, this map needs no time logic of its own —
one entry per internal code is enough. Fill status: smard and energy-charts
cover the bidding zones (smard uses the same codes, energy-charts lowercase
ids); open-meteo covers the weather points with "lat,lon" strings. Every
referenced source and internal region code must exist in SOURCES/REGIONS.

### 7. CONTRACT_VERSION *(implemented)*
One version for the entire contract set (semantic versioning MAJOR.MINOR.PATCH):
- MINOR: new metric/region/source, new optional field, new allowed resolution
- MAJOR: rename or remove a field, change a unit or a meaning
- PATCH: purely internal fixes

Implementation: the static version (single source of truth) is `project.version` in
`pyproject.toml` — the `uv_build` backend requires a static version and does not support
dynamic metadata. `src/wattfrosch_contracts/version.py` resolves `CONTRACT_VERSION` from
the installed package metadata (`importlib.metadata`) and falls back to parsing
`pyproject.toml` when running from source.
Release procedure: bump `project.version` in `pyproject.toml` and set the git tag together.

## Responsibility boundaries
The contract defines structure and value ranges. Stricter, source-specific checks
belong to the consuming module:
- Unit conversion into the metric's unit: fetch
- Strict source/API monitoring: fetch
- Storage metadata (ingested_at): store
- Calendar attributes such as daylight-saving classification: store (dim_time)
- Presentation (e.g. negative pumped-storage values): the consuming module

Pydantic is used in lenient mode (structure and value ranges validated, strict
type origin not enforced). Exception: `ts_utc` is typed as `AwareDatetime` —
tz-awareness is strictly enforced so the record always carries full time
information; naive input is rejected, as are unix timestamps (int/float).
Lenient typing elsewhere means a source
that suddenly returns "12.5" as text is tolerated. Strict monitoring of
external APIs is the responsibility of fetch, which knows the source and can
report deviations most meaningfully.

## Design decisions
- Definitions only — no logic, no I/O; maximum dependency is pydantic, otherwise
  standard library only.
- MeasurementRecord is immutable and self-validating via pydantic.
- The unit lives in the metric, not in the record.
- Missing values are missing rows (not NULL); gaps are filled in transform.
- The interval is half-open [start, end); end = start + resolution.
- Times are UTC only.
- resolution is an ISO-8601 duration; v1 allows only "PT1H".
- Region schema: "DE-LU" / "DE-BERLIN"; `kind` distinguishes bidding zone
  from weather point.
- Regions are time-dependent; an invalid region at a given time raises an error.
- The key↔category map is leading and strictly validated.
- SOURCE_METRIC_MAP and SOURCE_REGION_MAP are separate from METRICS.
- Semantic versioning; a new allowed resolution is a MINOR change.
- Catalogs are filled completely at implementation start; an unknown key raises
  an error.
- ingested_at is not part of the contract.
- v1 uses the UTC day (every day has 24 hours); local market days are a later
  concern.

## Out of scope
- Database access, migrations (→ wattfrosch-store)
- HTTP clients (→ wattfrosch-fetch)
- Transformation (→ wattfrosch-transform)
- Orchestration and backfill (→ wattfrosch-pipeline)

## Usage
Currently importable: `CONTRACT_VERSION`, `MeasurementRecord`, `METRICS`,
`REGIONS`, `SOURCES`, `SOURCE_METRIC_MAP`, `SOURCE_REGION_MAP` and the
error-type constants (the full import surface):

from wattfrosch_contracts import (
    MeasurementRecord, METRICS, REGIONS, SOURCES,
    SOURCE_METRIC_MAP, SOURCE_REGION_MAP, CONTRACT_VERSION,
)

## Structure

src/wattfrosch_contracts/
    __init__.py      # package docstring; re-exports the public surface
    version.py       # CONTRACT_VERSION (resolved from pyproject.toml version)
    records.py       # MeasurementRecord (§1)
    metrics.py       # METRICS catalog (§2)
    regions.py       # REGIONS catalog (§3)
    sources.py       # SOURCES catalog + SOURCE_METRIC_MAP + SOURCE_REGION_MAP (§4–§6)
    errors.py        # contract error types (PydanticCustomError factories)
    py.typed         # PEP 561 marker

tests/               # root-level (pytest resolves imports via pythonpath = ["src"])
pyproject.toml

## Development

Tooling is uv (Python 3.13, `requires-python >= 3.13`):

```bash
uv sync --dev                          # install deps into .venv
uv run pytest                          # tests
uv run ruff format --check .           # formatting check
uv run ruff check .                    # lint
uv run pyrefly check .                 # type check
```

CI (`.github/workflows/`) runs on every push/PR: `ruff format --check`, `ruff check`,
`pytest`, `pyrefly check` — all must pass.

## Open points
- Verify the best-effort license/url values and external codes in the maps.
- Maintain the bidding-zone history.