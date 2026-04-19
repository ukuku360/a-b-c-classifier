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

from sox404_pilot.constants import ISSUE_LABEL, LABELS, OTHER_LABEL, REMEDIATION_LABEL, normalize_label
from sox404_pilot.paths import (
    MASTER_ANNOTATIONS_FULL_ROUND3,
    ROUND3_ISSUE_EXPORT,
    ROUND3_OTHER_EXPORT,
    ROUND3_REMEDIATION_EXPORT,
    SENTENCES_CANONICAL,
)

EXPECTED_TOTAL_ROWS = 1_636

SENTENCE_COLUMNS = [
    "row_id",
    "doc_id",
    "sent_id",
    "quarter_end",
    "cik",
    "text_raw",
    "text_norm",
    "split",
]

ANNOTATION_COLUMNS = [
    "label_main",
    "flag_mixed_ab",
    "flag_needs_context",
    "c_subtype",
    "annotator",
    "label_version",
    "note",
]

OUTPUT_COLUMNS = [*SENTENCE_COLUMNS, *ANNOTATION_COLUMNS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export round-3 master annotations into label-specific CSV files with sentence text."
    )
    parser.add_argument(
        "--sentences",
        default=str(SENTENCES_CANONICAL),
        help="Canonical sentence table containing sentence text and metadata.",
    )
    parser.add_argument(
        "--master-annotations",
        default=str(MASTER_ANNOTATIONS_FULL_ROUND3),
        help="Final round-3 master annotation file.",
    )
    parser.add_argument(
        "--issue-output",
        default=str(ROUND3_ISSUE_EXPORT),
        help="Output CSV path for ISSUE rows.",
    )
    parser.add_argument(
        "--remediation-output",
        default=str(ROUND3_REMEDIATION_EXPORT),
        help="Output CSV path for REMEDIATION rows.",
    )
    parser.add_argument(
        "--other-output",
        default=str(ROUND3_OTHER_EXPORT),
        help="Output CSV path for OTHER rows.",
    )
    return parser.parse_args()


def require_columns(frame: pd.DataFrame, required: list[str], path: Path) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")


def require_unique_row_ids(frame: pd.DataFrame, path: Path) -> None:
    duplicates = frame.loc[frame["row_id"].duplicated(), "row_id"].astype(int).tolist()
    if duplicates:
        raise ValueError(f"{path} contains duplicate row_id values: {duplicates[:10]}")


def load_sentences(path: Path) -> pd.DataFrame:
    sentences = pd.read_csv(path)
    require_columns(sentences, SENTENCE_COLUMNS, path)
    sentences = sentences.loc[:, SENTENCE_COLUMNS].copy()
    sentences["row_id"] = sentences["row_id"].astype(int)
    require_unique_row_ids(sentences, path)
    if len(sentences) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"{path} row count {len(sentences)} does not match expected {EXPECTED_TOTAL_ROWS}")
    return sentences


def load_master_annotations(path: Path) -> pd.DataFrame:
    master = pd.read_csv(path)
    require_columns(master, ["row_id", *ANNOTATION_COLUMNS], path)
    master = master.loc[:, ["row_id", *ANNOTATION_COLUMNS]].copy()
    master["row_id"] = master["row_id"].astype(int)
    master["label_main"] = master["label_main"].map(normalize_label)
    master["flag_mixed_ab"] = master["flag_mixed_ab"].fillna(0).replace({"": 0}).astype(int)
    master["flag_needs_context"] = master["flag_needs_context"].fillna(0).replace({"": 0}).astype(int)
    master["c_subtype"] = master["c_subtype"].fillna("").astype(str).str.strip().replace({"": "other"})
    master["annotator"] = master["annotator"].fillna("").astype(str).str.strip()
    master["label_version"] = master["label_version"].fillna("").astype(str).str.strip()
    master["note"] = master["note"].fillna("").astype(str).str.strip()
    require_unique_row_ids(master, path)

    bad_labels = master.loc[~master["label_main"].isin(LABELS), ["row_id", "label_main"]]
    if not bad_labels.empty:
        sample = bad_labels.head(10).to_dict(orient="records")
        raise ValueError(f"{path} contains invalid label_main values: {sample}")

    if len(master) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"{path} row count {len(master)} does not match expected {EXPECTED_TOTAL_ROWS}")

    return master


def build_joined_export(sentences: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    joined = sentences.merge(master, on="row_id", how="inner")
    joined = joined.loc[:, OUTPUT_COLUMNS].sort_values("row_id").reset_index(drop=True)

    if len(joined) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"Joined export has {len(joined)} rows; expected {EXPECTED_TOTAL_ROWS}")

    sentence_ids = set(sentences["row_id"].astype(int).tolist())
    joined_ids = set(joined["row_id"].astype(int).tolist())
    missing = sorted(sentence_ids - joined_ids)
    extra = sorted(joined_ids - sentence_ids)
    if missing or extra:
        raise ValueError(
            "Joined export does not preserve full row_id coverage; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    return joined


def export_slice(frame: pd.DataFrame, label: str, output_path: Path) -> int:
    label_frame = frame.loc[frame["label_main"] == label, OUTPUT_COLUMNS].copy()
    if label_frame.empty:
        raise ValueError(f"No rows found for label {label}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    label_frame.to_csv(output_path, index=False)
    return int(len(label_frame))


def main() -> None:
    args = parse_args()

    sentences_path = Path(args.sentences)
    master_path = Path(args.master_annotations)
    issue_output = Path(args.issue_output)
    remediation_output = Path(args.remediation_output)
    other_output = Path(args.other_output)

    sentences = load_sentences(sentences_path)
    master = load_master_annotations(master_path)
    joined = build_joined_export(sentences, master)

    summary = {
        "rows_total": int(len(joined)),
        "issue_rows": export_slice(joined, ISSUE_LABEL, issue_output),
        "remediation_rows": export_slice(joined, REMEDIATION_LABEL, remediation_output),
        "other_rows": export_slice(joined, OTHER_LABEL, other_output),
        "issue_output": str(issue_output),
        "remediation_output": str(remediation_output),
        "other_output": str(other_output),
    }

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
