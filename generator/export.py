"""Export synthetic datasets and defect generation reports."""

import json
from collections import Counter
from pathlib import Path

from generator.config import load_config
from generator.defects import inject_defects
from generator.generate import generate_clean_data


def export_datasets(config: dict) -> dict:
    """Generate and export clean and dirty datasets."""
    clean = generate_clean_data(config)
    dirty, audit = inject_defects(clean, config)

    output = Path(config["output_directory"])
    output.mkdir(parents=True, exist_ok=True)

    clean_path = output / "customers_clean.csv"
    dirty_path = output / "customers_dirty.csv"
    report_path = output / "generation_report.json"

    clean.to_csv(clean_path, index=False, encoding="utf-8")
    dirty.to_csv(dirty_path, index=False, encoding="utf-8")

    affected_rows = {
        event["row_index"] for event in audit if event["defect_type"] != "duplicates"
    }

    report = {
        "generator": "DataDuck",
        "locale": config["locale"],
        "seed": config["seed"],
        "reference_date": config["reference_date"],
        "defect_rates": config["defect_rates"],
        "summary": {
            "clean_records": len(clean),
            "dirty_records": len(dirty),
            "columns": len(clean.columns),
            "total_defect_events": len(audit),
            "affected_original_records": len(affected_rows),
            "exact_duplicates": int(dirty.duplicated().sum()),
        },
        "defect_distribution": dict(
            sorted(Counter(event["defect_type"] for event in audit).items())
        ),
        "files": {
            "clean_dataset": clean_path.name,
            "dirty_dataset": dirty_path.name,
        },
        "audit_trail": audit,
    }

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("===== DATADUCK EXPORT =====")

    for path in [clean_path, dirty_path, report_path]:
        print(f"{path.resolve()}: {path.stat().st_size:,} bytes")

    return report


def main() -> None:
    """Run dataset generation and export."""
    config = load_config("configs/generator/default.json")
    report = export_datasets(config)

    print()
    print("===== GENERATION SUMMARY =====")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
