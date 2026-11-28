"""Generate clean synthetic customer datasets."""

from datetime import date, timedelta

import pandas as pd
from faker import Faker

from generator.config import load_config

COLUMNS = [
    "customer_id",
    "title",
    "first_name",
    "middle_name",
    "last_name",
    "date_of_birth",
    "gender",
    "company_name",
    "address_line_1",
    "address_line_2",
    "city",
    "county",
    "postcode",
    "country",
    "email",
    "phone",
    "created_at",
]


def generate_clean_data(config: dict) -> pd.DataFrame:
    """Generate a reproducible synthetic customer dataset."""
    fake = Faker(config["locale"])
    fake.seed_instance(config["seed"])

    reference_date = date.fromisoformat(config["reference_date"])
    records = []

    for index in range(1, config["record_count"] + 1):
        gender = fake.random_element(["Male", "Female"])

        if gender == "Male":
            first_name = fake.first_name_male()
            title = "Mr"
        else:
            first_name = fake.first_name_female()
            title = fake.random_element(["Mrs", "Ms", "Miss"])

        last_name = fake.last_name()

        birth_date = fake.date_between_dates(
            date_start=reference_date - timedelta(days=80 * 365),
            date_end=reference_date - timedelta(days=18 * 366),
        )

        email = f"customer{index:06d}@example.com"
        phone = f"07700 900{(index - 1) % 1000:03d}"

        record = {
            "customer_id": f"DD{index:06d}",
            "title": title,
            "first_name": first_name,
            "middle_name": fake.first_name() if fake.random_int(1, 100) <= 30 else "",
            "last_name": last_name,
            "date_of_birth": birth_date.isoformat(),
            "gender": gender,
            "company_name": fake.company() if fake.random_int(1, 100) <= 40 else "",
            "address_line_1": " ".join(fake.street_address().split()),
            "address_line_2": f"Flat {fake.random_int(1, 50)}"
            if fake.random_int(1, 100) <= 20
            else "",
            "city": fake.city(),
            "county": fake.county(),
            "postcode": fake.postcode(),
            "country": "United Kingdom",
            "email": email,
            "phone": phone,
            "created_at": f"{reference_date.isoformat()}T00:00:00Z",
        }

        records.append(record)

    return pd.DataFrame(records, columns=COLUMNS)


def main() -> None:
    """Run the initial clean data generation preview."""
    config = load_config("configs/generator/default.json")
    dataset = generate_clean_data(config)

    print("===== DATADUCK CLEAN DATA GENERATOR =====")
    print(f"Records generated: {len(dataset):,}")
    print(f"Total columns: {len(dataset.columns)}")
    print(f"Locale: {config['locale']}")
    print(f"Random seed: {config['seed']}")
    print()
    print("===== DATASET PREVIEW =====")
    print(dataset.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
