"""Integration tests for synthetic dataset exports."""

import json
from collections import Counter

import pandas as pd
import pytest

from generator.defects import inject_defects
from generator.export import export_datasets
from generator.generate import generate_clean_data


@pytest.fixture
def exported_dataset(generator_config, tmp_path):
    """Export datasets into an isolated temporary directory."""
    output = tmp_path / "datasets"
    generator_config["output_directory"] = str(output)

    report = export_datasets(generator_config)

    return output, report


def read_csv(path):
    """Preserve string values and empty fields during CSV loading."""
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )


@pytest.mark.parametrize(
    "filename",
    [
        "customers_clean.csv",
        "customers_dirty.csv",
        "generation_report.json",
    ],
)
def test_exported_files_exist(exported_dataset, filename):
    output, _ = exported_dataset

    assert (output / filename).is_file()


@pytest.mark.parametrize(
    "filename",
    [
        "customers_clean.csv",
        "customers_dirty.csv",
        "generation_report.json",
    ],
)
def test_exported_files_not_empty(exported_dataset, filename):
    output, _ = exported_dataset

    assert (output / filename).stat().st_size > 0


def test_clean_csv_record_count(exported_dataset, generator_config):
    output, _ = exported_dataset
    clean = read_csv(output / "customers_clean.csv")

    assert len(clean) == generator_config["record_count"]


def test_dirty_csv_record_count(exported_dataset):
    output, report = exported_dataset
    dirty = read_csv(output / "customers_dirty.csv")

    assert len(dirty) == report["summary"]["dirty_records"]


def test_clean_csv_round_trip(exported_dataset, generator_config):
    output, _ = exported_dataset
    actual = read_csv(output / "customers_clean.csv")
    expected = generate_clean_data(generator_config)

    pd.testing.assert_frame_equal(
        actual,
        expected,
        check_dtype=False,
    )


def test_dirty_csv_round_trip(exported_dataset, generator_config):
    output, _ = exported_dataset
    actual = read_csv(output / "customers_dirty.csv")

    clean = generate_clean_data(generator_config)
    expected, _ = inject_defects(clean, generator_config)

    pd.testing.assert_frame_equal(
        actual,
        expected,
        check_dtype=False,
    )


def test_csv_column_preservation(exported_dataset):
    output, _ = exported_dataset

    clean = read_csv(output / "customers_clean.csv")
    dirty = read_csv(output / "customers_dirty.csv")

    assert list(clean.columns) == list(dirty.columns)
    assert len(clean.columns) == 17


def test_json_report_integrity(exported_dataset):
    output, report = exported_dataset

    saved = json.loads((output / "generation_report.json").read_text(encoding="utf-8"))

    assert saved == report


def test_report_metadata(exported_dataset, generator_config):
    _, report = exported_dataset

    assert report["generator"] == "DataDuck"
    assert report["locale"] == generator_config["locale"]
    assert report["seed"] == generator_config["seed"]
    assert report["reference_date"] == generator_config["reference_date"]


def test_report_defect_distribution(exported_dataset):
    _, report = exported_dataset

    counts = Counter(event["defect_type"] for event in report["audit_trail"])

    assert dict(counts) == report["defect_distribution"]


def test_report_audit_count(exported_dataset):
    _, report = exported_dataset

    assert len(report["audit_trail"]) == report["summary"]["total_defect_events"]


def test_report_affected_records(exported_dataset):
    _, report = exported_dataset

    affected = {
        event["row_index"]
        for event in report["audit_trail"]
        if event["defect_type"] != "duplicates"
    }

    assert len(affected) == report["summary"]["affected_original_records"]


def test_exported_exact_duplicates(exported_dataset):
    output, report = exported_dataset
    dirty = read_csv(output / "customers_dirty.csv")

    assert dirty.duplicated().sum() == report["summary"]["exact_duplicates"]


def test_exported_audit_accuracy(exported_dataset):
    output, report = exported_dataset

    clean = read_csv(output / "customers_clean.csv")
    dirty = read_csv(output / "customers_dirty.csv")

    for event in report["audit_trail"]:
        row = event["row_index"]

        if event["defect_type"] == "duplicates":
            assert dirty.iloc[row].to_dict() == (event["injected_value"])
        else:
            field = event["field"]

            assert clean.at[row, field] == (event["original_value"])

            assert dirty.at[row, field] == (event["injected_value"])


def test_export_reproducibility(exported_dataset, generator_config):
    output, _ = exported_dataset

    filenames = [
        "customers_clean.csv",
        "customers_dirty.csv",
        "generation_report.json",
    ]

    original = {name: (output / name).read_bytes() for name in filenames}

    export_datasets(generator_config)

    for name in filenames:
        assert (output / name).read_bytes() == original[name]


def test_invalid_output_directory(generator_config, tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")

    generator_config["output_directory"] = str(blocked)

    with pytest.raises(FileExistsError):
        export_datasets(generator_config)
