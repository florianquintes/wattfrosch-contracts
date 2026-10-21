# Roadmap - wattfrosch-contracts

Duration: 3 working days.

## Day 1
- Repo skeleton (uv, src-layout, ruff, pyrefly, pytest)
- version.py: CONTRACT_VERSION resolved from package metadata
  (`importlib.metadata`) with a pyproject.toml fallback — the static
  `project.version` in pyproject.toml is the single source of truth

## Day 2
- records.py: MeasurementRecord + validators (tz-aware, finite, known keys)
- tests for validation rules

## Day 3
- metrics.py, regions.py, sources.py with SOURCE_METRIC_MAP + SOURCE_REGION_MAP
  (structure final; filled from the SMARD readme and the source APIs)
- errors.py: PydanticCustomError factories with `wattfrosch.*` error-type
  constants (was not in the original plan)
- README final; tag v0.1.0

## Definition of Done
- importable from another module
- tests green
- usable as a versioned package (git tag)

Status: DONE — v0.1.0 tagged; all catalog maps filled.

## Open for detail work
- verify best-effort license/url values and external codes
- maintain bidding-zone history (only DE-AT-LU → DE-LU implemented so far)
- contracts v0.2.*: add weather.wind_speed_100m and a radiation metric
