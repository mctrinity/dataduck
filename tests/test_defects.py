"""Unit tests for synthetic data defect injection."""

from collections import Counter

import pandas as pd
import pytest

from generator.defects import (
    inject_defects,
    load_inappropriate_words,
)


@pytest.fixture
def defect_result(clean_dataset, generator_config):
    """Return a dirty dataset and its audit trail."""
    return inject_defects(clean_dataset, generator_config)


def test_dictionary_not_empty():
    assert load_inappropriate_words()


def test_dictionary_unique():
    words = load_inappropriate_words()

    assert len(words) == len(set(words))


def test_clean_dataset_preservation(clean_dataset, generator_config):
    baseline = clean_dataset.copy(deep=True)

    inject_defects(clean_dataset, generator_config)

    pd.testing.assert_frame_equal(clean_dataset, baseline)


def test_dirty_record_count(clean_dataset, generator_config, defect_result):
    dirty, _ = defect_result

    expected = len(clean_dataset) + int(
        len(clean_dataset) * generator_config["defect_rates"]["duplicates"]
    )

    assert len(dirty) == expected


def test_column_preservation(clean_dataset, defect_result):
    dirty, _ = defect_result

    assert list(dirty.columns) == list(clean_dataset.columns)


def test_total_defect_events(clean_dataset, generator_config, defect_result):
    _, audit = defect_result

    expected = sum(
        int(len(clean_dataset) * rate)
        for rate in generator_config["defect_rates"].values()
    )

    assert len(audit) == expected


@pytest.mark.parametrize(
    "defect",
    [
        "duplicates",
        "missing_values",
        "invalid_email",
        "invalid_postcode",
        "capitalization",
        "whitespace",
        "invalid_phone",
        "inappropriate_words",
    ],
)
def test_defect_distribution(clean_dataset, generator_config, defect_result, defect):
    _, audit = defect_result

    counts = Counter(event["defect_type"] for event in audit)

    expected = int(len(clean_dataset) * generator_config["defect_rates"][defect])

    assert counts[defect] == expected


def test_exact_duplicates(clean_dataset, generator_config, defect_result):
    dirty, _ = defect_result

    expected = int(len(clean_dataset) * generator_config["defect_rates"]["duplicates"])

    assert dirty.duplicated().sum() == expected


def test_duplicate_audit_accuracy(defect_result):
    dirty, audit = defect_result

    for event in audit:
        if event["defect_type"] != "duplicates":
            continue

        source = dirty.iloc[event["source_row_index"]]
        duplicate = dirty.iloc[event["row_index"]]

        pd.testing.assert_series_equal(
            source,
            duplicate,
            check_names=False,
        )

        assert duplicate.to_dict() == event["injected_value"]


def test_original_audit_values(clean_dataset, defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "duplicates":
            continue

        original = clean_dataset.at[
            event["row_index"],
            event["field"],
        ]

        assert original == event["original_value"]


def test_injected_audit_values(defect_result):
    dirty, audit = defect_result

    for event in audit:
        if event["defect_type"] == "duplicates":
            continue

        actual = dirty.at[
            event["row_index"],
            event["field"],
        ]

        assert actual == event["injected_value"]


def test_no_unchanged_defect_events(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] != "duplicates":
            assert event["original_value"] != event["injected_value"]


def test_no_overwritten_defects(defect_result):
    _, audit = defect_result

    cells = [
        (event["row_index"], event["field"])
        for event in audit
        if event["defect_type"] != "duplicates"
    ]

    assert len(cells) == len(set(cells))


def test_audit_covers_all_changed_cells(clean_dataset, defect_result):
    dirty, audit = defect_result

    changed = {
        (row, field)
        for row in range(len(clean_dataset))
        for field in clean_dataset.columns
        if clean_dataset.at[row, field] != dirty.at[row, field]
    }

    audited = {
        (event["row_index"], event["field"])
        for event in audit
        if event["defect_type"] != "duplicates"
    }

    assert changed == audited


def test_customer_id_preservation(clean_dataset, defect_result):
    dirty, _ = defect_result

    assert (
        dirty["customer_id"].iloc[: len(clean_dataset)].tolist()
        == clean_dataset["customer_id"].tolist()
    )


def test_missing_values(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "missing_values":
            assert event["injected_value"] == ""


def test_invalid_email(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "invalid_email":
            assert "@" not in event["injected_value"]


def test_invalid_postcode(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "invalid_postcode":
            assert event["injected_value"] == "INVALID"


def test_invalid_phone(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "invalid_phone":
            assert event["injected_value"] == "123ABC"


def test_capitalization(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "capitalization":
            assert event["injected_value"] == event["original_value"].upper()


def test_whitespace(defect_result):
    _, audit = defect_result

    for event in audit:
        if event["defect_type"] == "whitespace":
            assert event["injected_value"].strip() == event["original_value"]
            assert event["injected_value"].startswith("  ")
            assert event["injected_value"].endswith("  ")


def test_inappropriate_words(defect_result):
    _, audit = defect_result
    words = load_inappropriate_words()

    for event in audit:
        if event["defect_type"] == "inappropriate_words":
            assert event["injected_value"] in words


def test_defect_reproducibility(clean_dataset, generator_config, defect_result):
    dirty, audit = defect_result

    repeated, repeated_audit = inject_defects(
        clean_dataset,
        generator_config,
    )

    pd.testing.assert_frame_equal(dirty, repeated)
    assert audit == repeated_audit


def test_zero_defects(clean_dataset, generator_config):
    generator_config["defect_rates"] = {
        defect: 0 for defect in generator_config["defect_rates"]
    }

    dirty, audit = inject_defects(
        clean_dataset,
        generator_config,
    )

    pd.testing.assert_frame_equal(clean_dataset, dirty)
    assert audit == []


def test_full_duplication(clean_dataset, generator_config):
    generator_config["defect_rates"] = {
        defect: 0 for defect in generator_config["defect_rates"]
    }
    generator_config["defect_rates"]["duplicates"] = 1

    dirty, audit = inject_defects(
        clean_dataset,
        generator_config,
    )

    assert len(dirty) == len(clean_dataset) * 2
    assert len(audit) == len(clean_dataset)
    assert dirty.duplicated().sum() == len(clean_dataset)


def test_dictionary_independent_of_working_directory(monkeypatch, tmp_path):
    expected = load_inappropriate_words()

    monkeypatch.chdir(tmp_path)

    assert load_inappropriate_words() == expected
