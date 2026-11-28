"""Load and validate synthetic data generator configuration."""

import json
from datetime import date
from pathlib import Path

SUPPORTED_LOCALES = {"en_GB"}

SUPPORTED_DEFECTS = {
    "duplicates",
    "missing_values",
    "invalid_email",
    "invalid_postcode",
    "capitalization",
    "whitespace",
    "invalid_phone",
    "inappropriate_words",
}


def load_config(config_path: str | Path) -> dict:
    """Load and validate a JSON generator configuration."""
    path = Path(config_path)

    with path.open(encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object.")

    required_keys = {
        "record_count",
        "locale",
        "seed",
        "reference_date",
        "output_directory",
        "defect_rates",
    }

    missing = required_keys - config.keys()

    if missing:
        raise ValueError(f"Missing configuration keys: {sorted(missing)}")

    count = config["record_count"]

    if type(count) is not int or count < 1:
        raise ValueError("record_count must be a positive integer.")

    locale = config["locale"]

    if not isinstance(locale, str) or locale not in SUPPORTED_LOCALES:
        raise ValueError("Unsupported locale.")

    if type(config["seed"]) is not int:
        raise ValueError("seed must be an integer.")

    reference_date = config["reference_date"]

    if not isinstance(reference_date, str):
        raise ValueError("reference_date must be an ISO date string.")

    try:
        parsed_date = date.fromisoformat(reference_date)
    except ValueError as exc:
        raise ValueError("reference_date must be a valid ISO date.") from exc

    if parsed_date.isoformat() != reference_date:
        raise ValueError("reference_date must use YYYY-MM-DD format.")

    output = config["output_directory"]

    if not isinstance(output, str) or not output.strip():
        raise ValueError("output_directory must be a non-empty string.")

    rates = config["defect_rates"]

    if not isinstance(rates, dict):
        raise ValueError("defect_rates must be a JSON object.")

    if set(rates) != SUPPORTED_DEFECTS:
        raise ValueError("Missing or unsupported defect types.")

    for defect, rate in rates.items():
        if type(rate) not in (int, float) or not 0 <= rate <= 1:
            raise ValueError(f"Invalid defect rate: {defect}")

    return config
