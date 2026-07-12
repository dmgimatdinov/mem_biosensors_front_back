# Combination synthesis flow

## Purpose

The combination synthesis service builds candidate biosensor combinations from four independent entity groups:

- analyte records
- bio-recognition layers
- immobilization layers
- memristive layers

Each combination is evaluated for compatibility, scored, and optionally persisted as a sensor combination.

## Entry points

The service currently exposes two synthesis entry points:

1. `synthesize_all_combinations(...)` — classic flow using the original compatibility and metrics pipeline.
2. `synthesize_all_combinations_v2(...)` — newer flow that uses `CompatibilityEngineV2` and the same scoring pipeline.

## Filtering of test records

Before any combination generation starts, the service removes records marked as test data. This is done by filtering out items where:

- `is_test` is explicitly set to `1`/`true`/`yes`
- or the record ID ends with `_TEST` or `_DUP`

This prevents synthetic or demo entries from entering the production synthesis process.

## High-level algorithm

### 1. Load source records

Both synthesis methods begin by loading the four lists from the database:

- `list_all_analytes()`
- `list_all_bio_recognition_layers()`
- `list_all_immobilization_layers()`
- `list_all_memristive_layers()`

The lists are filtered to exclude test-marked records before the cartesian product is created.

### 2. Build the cartesian product

The service iterates over all combinations of the four lists:

- analyte × bio layer × immobilization layer × memristive layer

This yields the full candidate space for synthesis.

### 3. Validate the candidate

For the classic pipeline, the candidate goes through `CombinationValidator.validate_combination(...)`.

The validation checks structural compatibility conditions such as:

- pH range overlap
- temperature compatibility
- mechanical compatibility

If validation fails, the candidate is rejected and no combination is created.

For the v2 pipeline, the candidate is validated in two stages:

- stage 1: structural compatibility via `CompatibilityEngineV2.validate_stage1(...)`
- stage 2: application-specific compatibility via `CompatibilityEngineV2.validate_stage2(...)`

### 4. Calculate metrics

If validation passes, the service calls `_calculate_metrics(...)`.

That function uses the metric facade to compute aggregated metrics such as:

- `SN_total`
- `TR_total`
- `ST_total`
- `RP_total`
- `LOD_total`
- `DR_total`
- `HL_total`
- `PC_total`

### 5. Calculate score

The raw score is computed by `_calculate_score(...)`.

That method:

- uses a `MetricsNormalizer`
- applies metric weights for sensitivity, reproducibility, stability, durability, and penalties for response time, detection limit, and power consumption
- clamps the result into the $[0, 10]$ range

The final score is then combined with a reliability coefficient to produce the final combination score.

### 6. Prepare the database record

A payload is built for persistence with fields such as:

- `Combo_ID`
- `TA_ID`
- `BRE_ID`
- `IM_ID`
- `MEM_ID`
- metric totals
- `Score`

### 7. Persist the combination

The payload is stored using `insert_sensor_combination(...)`.

The service handles three outcomes:

- created successfully
- duplicate entry
- insertion failure

## Error handling

The current implementation is defensive in two important ways:

- invalid or `None` numeric values are coerced to `0.0` during scoring
- exceptions during synthesis are logged with full traceback information using `logger.exception(...)`

## Notes on implementation details

- Records are normalized through `_normalize_record(...)` to support both legacy and current field names.
- The service uses a simple cartesian-product approach, so the runtime grows quickly with the number of available records.
- The v2 flow is intended to be a more structured compatibility check, but the scoring and persistence steps remain the same.
