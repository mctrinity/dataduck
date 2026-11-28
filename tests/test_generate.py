"""Unit tests for clean synthetic dataset generation."""

import pandas as pd

from generator.generate import COLUMNS, generate_clean_data


def test_record_count(clean_dataset, generator_config):
    assert len(clean_dataset) == generator_config["record_count"]


def test_column_count(clean_dataset):
    assert len(clean_dataset.columns) == 17


def test_column_names(clean_dataset):
    assert list(clean_dataset.columns) == COLUMNS


def test_customer_ids_unique(clean_dataset):
    assert clean_dataset["customer_id"].is_unique


def test_customer_id_format(clean_dataset):
    assert clean_dataset["customer_id"].str.fullmatch(r"DD\d{6}").all()


def test_email_uniqueness(clean_dataset):
    assert clean_dataset["email"].is_unique


def test_reserved_email_domain(clean_dataset):
    assert clean_dataset["email"].str.endswith("@example.com").all()


def test_reserved_phone_numbers(clean_dataset):
    assert clean_dataset["phone"].str.fullmatch(r"07700 900\d{3}").all()


def test_country(clean_dataset):
    assert clean_dataset["country"].eq("United Kingdom").all()


def test_required_fields_not_empty(clean_dataset):
    required = [
        "customer_id",
        "title",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
        "address_line_1",
        "city",
        "county",
        "postcode",
        "country",
        "email",
        "phone",
        "created_at",
    ]

    for field in required:
        assert clean_dataset[field].notna().all()
        assert clean_dataset[field].str.strip().ne("").all()


def test_no_exact_duplicates(clean_dataset):
    assert clean_dataset.duplicated().sum() == 0


def test_address_normalization(clean_dataset):
    addresses = clean_dataset["address_line_1"]

    assert not addresses.str.contains(r"[\r\n\t]").any()
    assert addresses.eq(addresses.str.strip()).all()
    assert not addresses.str.contains(r" {2,}").any()


def test_postcode_format(clean_dataset):
    pattern = r"(GIR 0AA|[A-Z]{1,2}[0-9][0-9A-Z]? [0-9][A-Z]{2})"

    assert clean_dataset["postcode"].str.fullmatch(pattern).all()


def test_date_of_birth(clean_dataset, generator_config):
    birth_dates = pd.to_datetime(
        clean_dataset["date_of_birth"],
        format="%Y-%m-%d",
    )

    reference = pd.Timestamp(generator_config["reference_date"])

    assert birth_dates.le(reference - pd.DateOffset(years=18)).all()

    assert birth_dates.ge(reference - pd.DateOffset(years=80)).all()


def test_created_at(clean_dataset, generator_config):
    expected = f"{generator_config['reference_date']}T00:00:00Z"

    assert clean_dataset["created_at"].eq(expected).all()


def test_reproducibility(clean_dataset, generator_config):
    repeated = generate_clean_data(generator_config)

    pd.testing.assert_frame_equal(
        clean_dataset,
        repeated,
    )


def test_different_seed(clean_dataset, generator_config):
    generator_config["seed"] += 1

    different = generate_clean_data(generator_config)

    assert not clean_dataset.equals(different)


def test_single_record(generator_config):
    generator_config["record_count"] = 1

    dataset = generate_clean_data(generator_config)

    assert len(dataset) == 1
    assert dataset.iloc[0]["customer_id"] == "DD000001"
