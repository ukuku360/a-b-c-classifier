#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.constants import C_SUBTYPES, LABELS, OTHER_LABEL, normalize_label


ANNOTATION_COLUMNS = [
    "label_main",
    "flag_mixed_ab",
    "flag_needs_context",
    "c_subtype",
    "annotator",
    "label_version",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and merge OTHER re-audit batch CSVs.")
    parser.add_argument(
        "--batch-manifest",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "manifests" / "batch_manifest.csv"),
    )
    parser.add_argument(
        "--batch-summary",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "manifests" / "batch_summary.csv"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3"),
    )
    parser.add_argument(
        "--merged-file",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "other_reaudit_merged.csv"),
    )
    parser.add_argument(
        "--overlay-file",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "other_reaudit_overlay.csv"),
    )
    parser.add_argument(
        "--summary-json",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "other_reaudit_summary.json"),
    )
    parser.add_argument(
        "--summary-csv",
        default=str(PROJECT_ROOT / "outputs" / "other_reaudit_round3" / "other_reaudit_summary.csv"),
    )
    parser.add_argument("--expected-total", type=int, default=465)
    return parser.parse_args()


def normalize_annotation_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["label_main"] = out["label_main"].map(normalize_label)
    out["flag_mixed_ab"] = out["flag_mixed_ab"].fillna(0).replace({"": 0}).astype(int)
    out["flag_needs_context"] = out["flag_needs_context"].fillna(0).replace({"": 0}).astype(int)
    out["c_subtype"] = out["c_subtype"].fillna("").astype(str).str.strip().replace({"": "other"})
    out["annotator"] = out["annotator"].fillna("").astype(str).str.strip()
    out["label_version"] = out["label_version"].fillna("").astype(str).str.strip()
    out["note"] = out["note"].fillna("").astype(str).str.strip()
    return out


def validate_annotations(frame: pd.DataFrame) -> None:
    if not frame["label_main"].isin(LABELS).all():
        bad = frame.loc[~frame["label_main"].isin(LABELS), ["row_id", "label_main"]]
        raise ValueError(f"Found invalid label_main values: {bad.head(10).to_dict(orient='records')}")

    if not frame["flag_mixed_ab"].isin([0, 1]).all():
        raise ValueError("flag_mixed_ab must be 0/1")
    if not frame["flag_needs_context"].isin([0, 1]).all():
        raise ValueError("flag_needs_context must be 0/1")
    if not frame["c_subtype"].isin(C_SUBTYPES).all():
        bad = sorted(frame.loc[~frame["c_subtype"].isin(C_SUBTYPES), "c_subtype"].unique().tolist())
        raise ValueError(f"Found invalid c_subtype values: {bad}")
    if (frame["annotator"] == "").any():
        raise ValueError("annotator cannot be blank")
    if (frame["label_version"] == "").any():
        raise ValueError("label_version cannot be blank")

    note_required_mask = (
        (frame["flag_mixed_ab"] == 1)
        | (frame["flag_needs_context"] == 1)
        | ((frame["pred_label"] == OTHER_LABEL) & (frame["label_main"] != OTHER_LABEL))
    )
    missing_note = frame.loc[note_required_mask & (frame["note"] == ""), ["row_id", "label_main", "pred_label"]]
    if not missing_note.empty:
        raise ValueError(
            f"Missing required note for {len(missing_note)} rows; sample={missing_note.head(10).to_dict(orient='records')}"
        )


def load_batches(batch_summary: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for row in batch_summary.itertuples(index=False):
        batch_path = Path(row.batch_path)
        if not batch_path.exists():
            raise FileNotFoundError(f"Missing batch file: {batch_path}")
        batch = pd.read_csv(batch_path)
        batch = normalize_annotation_columns(batch)
        frames.append(batch)
    if not frames:
        raise ValueError("No batch files found to merge")
    return pd.concat(frames, ignore_index=True)


def build_summary(merged: pd.DataFrame) -> dict[str, object]:
    c_subtype_counts = {
        subtype: int((merged["c_subtype"] == subtype).sum())
        for subtype in C_SUBTYPES
    }
    return {
        "rows_total": int(len(merged)),
        "row_id_unique": int(merged["row_id"].nunique()),
        "other_kept": int((merged["label_main"] == OTHER_LABEL).sum()),
        "other_to_issue": int((merged["label_main"] == "ISSUE").sum()),
        "other_to_remediation": int((merged["label_main"] == "REMEDIATION").sum()),
        "needs_context_count": int((merged["flag_needs_context"] == 1).sum()),
        "mixed_ab_count": int((merged["flag_mixed_ab"] == 1).sum()),
        "annotator_count": int(merged["annotator"].nunique()),
        "c_subtype_counts": c_subtype_counts,
    }


def main() -> None:
    args = parse_args()
    batch_manifest = pd.read_csv(args.batch_manifest)
    batch_summary = pd.read_csv(args.batch_summary)
    merged = load_batches(batch_summary)
    merged = merged.sort_values(["doc_id", "sent_id", "row_id"]).reset_index(drop=True)

    if len(merged) != len(batch_manifest):
        raise ValueError("Merged row count does not match batch manifest")
    if merged["row_id"].nunique() != len(batch_manifest):
        raise ValueError("Merged row_id cardinality does not match batch manifest")
    if len(merged) != args.expected_total:
        raise ValueError(f"Merged row count {len(merged)} does not match expected total {args.expected_total}")

    expected_row_ids = set(batch_manifest["row_id"].astype(int).tolist())
    merged_row_ids = set(merged["row_id"].astype(int).tolist())
    missing = sorted(expected_row_ids - merged_row_ids)
    extra = sorted(merged_row_ids - expected_row_ids)
    if missing or extra:
        raise ValueError(f"Row_id mismatch detected; missing={missing[:10]} extra={extra[:10]}")

    validate_annotations(merged)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    merged_path = Path(args.merged_file)
    overlay_path = Path(args.overlay_file)
    summary_json_path = Path(args.summary_json)
    summary_csv_path = Path(args.summary_csv)

    merged.to_csv(merged_path, index=False)
    merged.loc[:, ["row_id", *ANNOTATION_COLUMNS]].sort_values("row_id").to_csv(overlay_path, index=False)

    summary = build_summary(merged)

    with summary_json_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=True, indent=2)

    summary_rows = [
        {"metric": "rows_total", "value": summary["rows_total"]},
        {"metric": "row_id_unique", "value": summary["row_id_unique"]},
        {"metric": "other_kept", "value": summary["other_kept"]},
        {"metric": "other_to_issue", "value": summary["other_to_issue"]},
        {"metric": "other_to_remediation", "value": summary["other_to_remediation"]},
        {"metric": "needs_context_count", "value": summary["needs_context_count"]},
        {"metric": "mixed_ab_count", "value": summary["mixed_ab_count"]},
        {"metric": "annotator_count", "value": summary["annotator_count"]},
    ]
    summary_rows.extend(
        {"metric": f"c_subtype_{subtype}", "value": count}
        for subtype, count in summary["c_subtype_counts"].items()
    )
    pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False)

    print(summary)


if __name__ == "__main__":
    main()
