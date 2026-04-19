#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.constants import ISSUE_LABEL


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
    parser = argparse.ArgumentParser(description="Prepare batch CSVs for ISSUE re-audit review.")
    parser.add_argument(
        "--winner-predictions",
        default=str(PROJECT_ROOT / "outputs" / "pilot_run_round2" / "winner_predictions.csv"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "issue_reaudit_round3"),
    )
    parser.add_argument("--target-batch-size", type=int, default=25)
    parser.add_argument(
        "--label-version",
        default="guideline_v1_1_issue_reaudit_round3",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def initialize_annotation_columns(frame: pd.DataFrame, label_version: str) -> pd.DataFrame:
    out = frame.copy()
    out["label_main"] = ""
    out["flag_mixed_ab"] = ""
    out["flag_needs_context"] = ""
    out["c_subtype"] = ""
    out["annotator"] = ""
    out["label_version"] = label_version
    out["note"] = ""
    return out


def pack_doc_batches(issue_df: pd.DataFrame, target_batch_size: int) -> list[pd.DataFrame]:
    batches: list[pd.DataFrame] = []
    current_docs: list[pd.DataFrame] = []
    current_rows = 0

    def flush() -> None:
        nonlocal current_docs, current_rows
        if not current_docs:
            return
        batches.append(pd.concat(current_docs, ignore_index=True))
        current_docs = []
        current_rows = 0

    for _, doc_frame in issue_df.groupby("doc_id", sort=False):
        doc_frame = doc_frame.reset_index(drop=True)
        doc_rows = len(doc_frame)

        if doc_rows > target_batch_size:
            flush()
            for start in range(0, doc_rows, target_batch_size):
                chunk = doc_frame.iloc[start : start + target_batch_size].copy().reset_index(drop=True)
                batches.append(chunk)
            continue

        if current_rows > 0 and current_rows + doc_rows > target_batch_size:
            flush()

        current_docs.append(doc_frame)
        current_rows += doc_rows

    flush()
    return batches


def write_csv(frame: pd.DataFrame, path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main() -> None:
    args = parse_args()
    winner_predictions = pd.read_csv(args.winner_predictions)
    issue_df = winner_predictions.loc[winner_predictions["pred_label"] == ISSUE_LABEL].copy()
    issue_df = issue_df.sort_values(["doc_id", "sent_id", "row_id"]).reset_index(drop=True)

    if issue_df.empty:
        raise ValueError("No ISSUE rows found in winner predictions")

    batches = pack_doc_batches(issue_df, target_batch_size=args.target_batch_size)
    output_dir = Path(args.output_dir)
    batches_dir = output_dir / "batches"
    manifests_dir = output_dir / "manifests"

    row_manifest_rows: list[dict[str, object]] = []
    batch_summary_rows: list[dict[str, object]] = []

    for idx, batch in enumerate(batches, start=1):
        batch_id = f"batch_{idx:03d}"
        batch_path = batches_dir / f"{batch_id}.csv"
        initialized = initialize_annotation_columns(batch, label_version=args.label_version)
        write_csv(initialized, batch_path, force=args.force)

        docs = batch["doc_id"].drop_duplicates().tolist()
        batch_summary_rows.append(
            {
                "batch_id": batch_id,
                "batch_path": str(batch_path),
                "row_count": int(len(batch)),
                "doc_count": int(len(docs)),
                "first_doc_id": docs[0],
                "last_doc_id": docs[-1],
                "first_row_id": int(batch["row_id"].min()),
                "last_row_id": int(batch["row_id"].max()),
            }
        )

        for row_order, row in enumerate(batch.itertuples(index=False), start=1):
            row_manifest_rows.append(
                {
                    "batch_id": batch_id,
                    "batch_path": str(batch_path),
                    "row_order": row_order,
                    "row_id": int(row.row_id),
                    "doc_id": str(row.doc_id),
                    "sent_id": int(row.sent_id),
                }
            )

    row_manifest = pd.DataFrame(row_manifest_rows).sort_values(["batch_id", "row_order"]).reset_index(drop=True)
    batch_summary = pd.DataFrame(batch_summary_rows).sort_values("batch_id").reset_index(drop=True)

    if len(row_manifest) != len(issue_df):
        raise AssertionError("Row manifest length does not match ISSUE pool length")
    if row_manifest["row_id"].nunique() != len(issue_df):
        raise AssertionError("Duplicate row_id detected while building batch manifest")

    write_csv(row_manifest, manifests_dir / "batch_manifest.csv", force=args.force)
    write_csv(batch_summary, manifests_dir / "batch_summary.csv", force=args.force)

    print(
        {
            "issue_rows": int(len(issue_df)),
            "batch_count": int(len(batch_summary)),
            "target_batch_size": int(args.target_batch_size),
            "min_batch_rows": int(batch_summary["row_count"].min()),
            "max_batch_rows": int(batch_summary["row_count"].max()),
            "output_dir": str(output_dir),
        }
    )


if __name__ == "__main__":
    main()
