"""Inject reproducible data quality defects into synthetic datasets."""

import random
from pathlib import Path

import pandas as pd

REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "address_line_1",
    "city",
    "postcode",
    "country",
    "email",
    "phone",
]

TEXT_FIELDS = [
    "first_name",
    "last_name",
    "address_line_1",
    "city",
    "county",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DICTIONARY_PATH = (
    PROJECT_ROOT / "configs" / "dictionaries" / "inappropriate_words_en_GB.txt"
)


def load_inappropriate_words() -> list[str]:
    """Load the inappropriate words dictionary."""
    words = [
        word.strip()
        for word in DICTIONARY_PATH.read_text(encoding="utf-8").splitlines()
        if word.strip()
    ]

    if not words:
        raise ValueError("Inappropriate words dictionary is empty.")

    return words


def inject_defects(
    clean: pd.DataFrame,
    config: dict,
) -> tuple[pd.DataFrame, list[dict]]:
    """Return a dirty dataset and its defect audit trail."""
    dirty = clean.copy(deep=True).reset_index(drop=True)
    rng = random.Random(config["seed"])
    rates = config["defect_rates"]
    total = len(dirty)
    audit = []
    modified = set()

    words = load_inappropriate_words()

    def apply_defect(
        defect: str,
        fields: list[str],
        transform,
    ) -> None:
        target = int(total * rates[defect])
        candidates = list(range(total))
        rng.shuffle(candidates)
        applied = 0

        for row in candidates:
            if applied >= target:
                break

            available = [
                field
                for field in fields
                if (row, field) not in modified and dirty.at[row, field] != ""
            ]

            rng.shuffle(available)

            for field in available:
                original = dirty.at[row, field]
                replacement = transform(original)

                if replacement == original:
                    continue

                dirty.at[row, field] = replacement
                modified.add((row, field))

                audit.append(
                    {
                        "defect_type": defect,
                        "customer_id": dirty.at[row, "customer_id"],
                        "row_index": row,
                        "field": field,
                        "original_value": original,
                        "injected_value": replacement,
                    }
                )

                applied += 1
                break

        if applied != target:
            raise ValueError(f"{defect}: requested {target}, applied {applied}")

    apply_defect(
        "invalid_email",
        ["email"],
        lambda value: value.replace("@", "."),
    )

    apply_defect(
        "invalid_postcode",
        ["postcode"],
        lambda value: "INVALID",
    )

    apply_defect(
        "invalid_phone",
        ["phone"],
        lambda value: "123ABC",
    )

    apply_defect(
        "inappropriate_words",
        ["first_name", "last_name"],
        lambda value: rng.choice(words),
    )

    apply_defect(
        "missing_values",
        REQUIRED_FIELDS,
        lambda value: "",
    )

    apply_defect(
        "capitalization",
        TEXT_FIELDS,
        lambda value: value.upper(),
    )

    apply_defect(
        "whitespace",
        TEXT_FIELDS,
        lambda value: f"  {value}  ",
    )

    duplicate_count = int(total * rates["duplicates"])
    duplicate_rows = rng.sample(range(total), duplicate_count)

    duplicates = dirty.iloc[duplicate_rows].copy()

    for offset, row in enumerate(duplicate_rows):
        audit.append(
            {
                "defect_type": "duplicates",
                "customer_id": dirty.at[row, "customer_id"],
                "row_index": total + offset,
                "source_row_index": row,
                "field": None,
                "original_value": None,
                "injected_value": dirty.iloc[row].to_dict(),
            }
        )

    dirty = pd.concat(
        [dirty, duplicates],
        ignore_index=True,
    )

    return dirty, audit
