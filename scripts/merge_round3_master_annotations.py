#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.constants import C_SUBTYPES, LABELS, normalize_label


ANNOTATION_COLUMNS = [
    "row_id",
    "label_main",
    "flag_mixed_ab",
    "flag_needs_context",
    "c_subtype",
    "annotator",
    "label_version",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge round-3 re-audit overlays into a new master annotation file.")
    parser.add_argument(
        "--issue-overlay",
        default=str(PROJECT_ROOT / "outputs" / "issue_reaudit_round3" / "issue_reaudit_overlay.csv"),
    )
    parser.add_argument(
        "--remediation-overlay",
        default=str(PROJECT_ROOT / "outputs" / "remediation_reaudit_round3" / "remediation_reaudit_overlay.csv"),
    )
    parser.add_argument(
        "--other-overlay",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "other_reaudit_overlay.csv"),
    )
    parser.add_argument(
        "--sentences",
        default=str(PROJECT_ROOT / "data" / "sentences.csv"),
    )
    parser.add_argument(
        "--master-annotations",
        default=str(PROJECT_ROOT / "data" / "master_annotations.csv"),
    )
    parser.add_argument(
        "--output-file",
        default=str(PROJECT_ROOT / "data" / "master_annotations_round3_reaudit.csv"),
    )
    return parser.parse_args()


def normalize_row(row: dict[str, object]) -> dict[str, object]:
    c_subtype = str(row.get("c_subtype", "")).strip() or "other"
    return {
        "row_id": int(str(row.get("row_id", "")).strip()),
        "label_main": normalize_label(row.get("label_main")),
        "flag_mixed_ab": int(str(row.get("flag_mixed_ab", "")).strip() or "0"),
        "flag_needs_context": int(str(row.get("flag_needs_context", "")).strip() or "0"),
        "c_subtype": c_subtype,
        "annotator": str(row.get("annotator", "")).strip(),
        "label_version": str(row.get("label_version", "")).strip(),
        "note": str(row.get("note", "")).strip(),
    }


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, object]]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def validate_schema(actual_columns: list[str], path: Path, expected_columns: list[str]) -> None:
    if actual_columns != expected_columns:
        raise ValueError(f"{path} columns do not match expected schema; actual={actual_columns} expected={expected_columns}")


def validate_annotation_values(rows: list[dict[str, object]], path: Path) -> None:
    row_ids = [int(row["row_id"]) for row in rows]
    duplicated = sorted([row_id for row_id, count in Counter(row_ids).items() if count > 1])
    if duplicated:
        duplicated = duplicated[:10]
        raise ValueError(f"{path} has duplicate row_id values: {duplicated}")
    bad_labels = [
        {"row_id": int(row["row_id"]), "label_main": row["label_main"]}
        for row in rows
        if row["label_main"] not in LABELS
    ]
    if bad_labels:
        raise ValueError(f"{path} has invalid label_main values: {bad_labels[:10]}")
    if any(int(row["flag_mixed_ab"]) not in [0, 1] for row in rows):
        raise ValueError(f"{path} has non-binary flag_mixed_ab values")
    if any(int(row["flag_needs_context"]) not in [0, 1] for row in rows):
        raise ValueError(f"{path} has non-binary flag_needs_context values")
    bad_c_subtypes = sorted({str(row["c_subtype"]) for row in rows if row["c_subtype"] not in C_SUBTYPES})
    if bad_c_subtypes:
        bad = bad_c_subtypes
        raise ValueError(f"{path} has invalid c_subtype values: {bad}")
    if any(str(row["annotator"]) == "" for row in rows):
        raise ValueError(f"{path} has blank annotator values")
    if any(str(row["label_version"]) == "" for row in rows):
        raise ValueError(f"{path} has blank label_version values")


def load_annotation_file(path: Path, expected_columns: list[str]) -> list[dict[str, object]]:
    fieldnames, raw_rows = read_csv_rows(path)
    validate_schema(fieldnames, path, expected_columns)
    rows = [normalize_row(row) for row in raw_rows]
    validate_annotation_values(rows, path)
    return rows


def validate_no_overlay_overlap(named_frames: list[tuple[str, list[dict[str, object]]]]) -> None:
    owners: dict[int, str] = {}
    collisions: list[tuple[int, str, str]] = []
    for name, rows in named_frames:
        for row in rows:
            row_id = int(row["row_id"])
            prior = owners.get(row_id)
            if prior is not None:
                collisions.append((row_id, prior, name))
            owners[row_id] = name
    if collisions:
        sample = collisions[:10]
        raise ValueError(f"Overlay row_id collisions detected: {sample}")


def validate_sentence_coverage(merged_rows: list[dict[str, object]], sentences_path: Path) -> None:
    fieldnames, sentences = read_csv_rows(sentences_path)
    if "row_id" not in fieldnames:
        raise ValueError(f"{sentences_path} does not contain row_id")
    sentence_row_ids = {int(str(row["row_id"]).strip()) for row in sentences}
    merged_row_ids = {int(row["row_id"]) for row in merged_rows}
    missing = sorted(sentence_row_ids - merged_row_ids)
    extra = sorted(merged_row_ids - sentence_row_ids)
    if missing or extra:
        raise ValueError(
            "Merged annotations do not exactly match sentences row_id coverage; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )


def build_summary(merged_rows: list[dict[str, object]], master_rows: list[dict[str, object]], output_file: Path) -> dict[str, object]:
    merged_row_ids = {int(row["row_id"]) for row in merged_rows}
    master_row_ids = {int(row["row_id"]) for row in master_rows}
    return {
        "total_rows": int(len(merged_rows)),
        "overlap_with_existing_master": int(len(merged_row_ids & master_row_ids)),
        "new_rows_added": int(len(merged_row_ids - master_row_ids)),
        "output_file": str(output_file),
    }


def main() -> None:
    args = parse_args()
    master_path = Path(args.master_annotations)
    master_columns, master_raw_rows = read_csv_rows(master_path)
    validate_schema(master_columns, master_path, ANNOTATION_COLUMNS)
    master_rows = [normalize_row(row) for row in master_raw_rows]

    overlay_paths = [
        ("issue", Path(args.issue_overlay)),
        ("remediation", Path(args.remediation_overlay)),
        ("other", Path(args.other_overlay)),
    ]
    overlay_rows = [(name, load_annotation_file(path, ANNOTATION_COLUMNS)) for name, path in overlay_paths]
    validate_no_overlay_overlap(overlay_rows)

    merged_rows: list[dict[str, object]] = []
    for _, rows in overlay_rows:
        merged_rows.extend(rows)
    validate_annotation_values(merged_rows, Path("merged_overlay_union"))
    validate_sentence_coverage(merged_rows, Path(args.sentences))
    merged_rows.sort(key=lambda row: int(row["row_id"]))

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ANNOTATION_COLUMNS)
        writer.writeheader()
        writer.writerows(merged_rows)

    summary = build_summary(merged_rows, master_rows, output_file)
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
