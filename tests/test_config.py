"""Unit tests for generator configuration validation."""

import json

import pytest

from generator.config import load_config


def write_config(tmp_path, config):
    """Write a temporary configuration file."""
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )
    return path


def test_valid_config(generator_config, tmp_path):
    path = write_config(tmp_path, generator_config)

    assert load_config(path) == generator_config


@pytest.mark.parametrize(
    "count",
    [0, -1, -100, 1.5, "100", True, None],
)
def test_invalid_record_count(generator_config, tmp_path, count):
    generator_config["record_count"] = count
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="record_count"):
        load_config(path)


@pytest.mark.parametrize(
    "key",
    [
        "record_count",
        "locale",
        "seed",
        "reference_date",
        "output_directory",
        "defect_rates",
    ],
)
def test_missing_required_key(generator_config, tmp_path, key):
    del generator_config[key]
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="Missing"):
        load_config(path)


def test_unsupported_locale(generator_config, tmp_path):
    generator_config["locale"] = "invalid_locale"
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="locale"):
        load_config(path)


@pytest.mark.parametrize("seed", ["42", 1.5, True, None])
def test_invalid_seed(generator_config, tmp_path, seed):
    generator_config["seed"] = seed
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="seed"):
        load_config(path)


@pytest.mark.parametrize(
    "reference_date",
    ["invalid", "2026-02-30", "2026-13-01"],
)
def test_invalid_reference_date(generator_config, tmp_path, reference_date):
    generator_config["reference_date"] = reference_date
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError):
        load_config(path)


@pytest.mark.parametrize(
    "output_directory",
    ["", "   ", None, 123],
)
def test_invalid_output_directory(generator_config, tmp_path, output_directory):
    generator_config["output_directory"] = output_directory
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="output_directory"):
        load_config(path)


@pytest.mark.parametrize(
    "rate",
    [-0.1, 1.1, "0.05", True, None],
)
def test_invalid_defect_rate(generator_config, tmp_path, rate):
    generator_config["defect_rates"]["duplicates"] = rate
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="Invalid defect rate"):
        load_config(path)


def test_missing_defect_type(generator_config, tmp_path):
    del generator_config["defect_rates"]["duplicates"]
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="defect types"):
        load_config(path)


def test_unsupported_defect_type(generator_config, tmp_path):
    generator_config["defect_rates"]["unknown"] = 0.1
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="defect types"):
        load_config(path)


@pytest.mark.parametrize("rate", [0, 1])
def test_valid_defect_rate_boundary(generator_config, tmp_path, rate):
    generator_config["defect_rates"]["duplicates"] = rate
    path = write_config(tmp_path, generator_config)

    assert load_config(path)["defect_rates"]["duplicates"] == rate


def test_invalid_json(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_config(path)


def test_missing_config_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "locale",
    [None, True, 123, [], {}],
)
def test_invalid_locale_type(generator_config, tmp_path, locale):
    generator_config["locale"] = locale
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="locale"):
        load_config(path)


@pytest.mark.parametrize(
    "reference_date",
    [None, True, 20261127, [], {}],
)
def test_invalid_reference_date_type(generator_config, tmp_path, reference_date):
    generator_config["reference_date"] = reference_date
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="reference_date"):
        load_config(path)


@pytest.mark.parametrize(
    "reference_date",
    ["20261127", "2026-W48-5"],
)
def test_noncanonical_reference_date(generator_config, tmp_path, reference_date):
    generator_config["reference_date"] = reference_date
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="reference_date"):
        load_config(path)


@pytest.mark.parametrize(
    "config",
    [None, [], "invalid", 123],
)
def test_invalid_configuration_root(tmp_path, config):
    path = write_config(tmp_path, config)

    with pytest.raises(ValueError, match="JSON object"):
        load_config(path)


@pytest.mark.parametrize(
    "rates",
    [None, [], "invalid", 123],
)
def test_invalid_defect_rates_type(generator_config, tmp_path, rates):
    generator_config["defect_rates"] = rates
    path = write_config(tmp_path, generator_config)

    with pytest.raises(ValueError, match="defect_rates"):
        load_config(path)
