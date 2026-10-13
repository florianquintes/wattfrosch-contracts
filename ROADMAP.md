# Roadmap - wattfrosch-contracts

Duration: 3 working days.

## Day 1
- Repo skeleton (uv, src-layout, ruff, mypy, pytest)
- version.py: CONTRACT_VERSION = "0.1.0"

## Day 2
- records.py: MeasurementRecord + validators (tz-aware, finite, known keys)
- tests for validation rules

## Day 3
- metrics.py, regions.py, sources.py, SOURCE_METRIC_MAP
  (structure final; list is a v1 stub to be filled manually)
- README final; tag v0.1.0

## Definition of Done
- importable from another module
- tests green
- usable as a versioned package (git tag)

## Open for detail work
- fill METRICS and SOURCE_METRIC_MAP
- bidding zone history
