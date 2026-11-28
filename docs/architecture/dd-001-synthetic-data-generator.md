# DD-001 - Synthetic Data Generator

## Objective

Generate reproducible synthetic customer datasets for testing
DataDuck's data profiling, cleansing, validation and
deduplication capabilities.

## Functional Requirements

- Configurable record count, default 1000.
- Configurable random seed, default 42.
- Initial locale: en_GB.
- Extensible to other regional datasets.
- Generate clean and dirty datasets.
- Preserve the clean reference dataset.
- Configurable data quality defect rates.
- Maintain a defect injection audit trail.
- Export datasets in CSV format.
- Export generation reports in JSON format.

## Dataset Schema

| Field | Type | Required |
|---|---|---|
| customer_id | String | Yes |
| title | String | No |
| first_name | String | Yes |
| middle_name | String | No |
| last_name | String | Yes |
| date_of_birth | Date | Yes |
| gender | String | No |
| company_name | String | No |
| address_line_1 | String | Yes |
| address_line_2 | String | No |
| city | String | Yes |
| county | String | No |
| postcode | String | Yes |
| country | String | Yes |
| email | String | Yes |
| phone | String | Yes |
| created_at | Timestamp | Yes |

## Supported Data Quality Defects

- Duplicate records
- Missing required values
- Invalid email addresses
- Invalid postcodes
- Invalid telephone numbers
- Inconsistent capitalization
- Leading and trailing whitespace
- Inappropriate words

## Data Privacy

- Use synthetic data only.
- Use reserved example email domains.
- Use reserved fictional telephone ranges.
- Do not use actual customer information.
- Exclude generated datasets from version control.

## Acceptance Criteria

- Configurable record count is respected.
- Clean dataset contains unique customer IDs.
- Identical configuration, seed and dependency versions
  produce identical output.
- Reference dates are configurable for reproducibility.
- Clean dataset remains unchanged after defect injection.
- Injected defects are traceable.
- Generated files are valid CSV and JSON.
- Automated unit tests pass.
- Ruff linting and formatting checks pass.

## Known Limitations

Synthetic addresses are not verified postal addresses.
Regional address components may not be geographically consistent.

## Implementation and Execution

Run from the repository root.

- Clean data preview: `python -m generator.generate`
- Dataset export: `python -m generator.export`
- Automated testing: `python -m pytest`
- Lint validation: `python -m ruff check generator/ tests/`
- Dependency validation: `python -m pip check`

## Validation Results - 2026-11-28

| Metric | Result |
|---|---:|
| Clean records | 1000 |
| Dirty records | 1050 |
| Columns | 17 |
| Defect events | 390 |
| Affected original records | 293 |
| Exact duplicates | 50 |
| Automated tests passed | 128 |
| Automated tests failed | 0 |
| Regression duration | 3.09 seconds |

Ruff linting, formatting and dependency consistency checks passed.

## Additional Known Limitations

- Fictional phone numbers repeat beyond 1000 records.
- Postcode validation checks basic syntax only.
- Age boundaries use approximate day-based calculations.
- Extreme defect combinations may exhaust eligible cells.
- Existing generated files are overwritten.
- File exports are not atomic.
- CLI execution assumes the repository root.
- Linux compatibility and code coverage remain unverified.
- Dependency vulnerability scanning remains pending.

## Future Enhancements

- Additional regional datasets.
- Configurable dirtiness presets.
- Performance benchmarking.
- Atomic and versioned exports.
- Automated code coverage.
- Dependency security scanning.
- GitHub Actions CI.
