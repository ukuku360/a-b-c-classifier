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

from sox404_pilot.constants import LABELS, normalize_label
from sox404_pilot.paths import (
    MASTER_ANNOTATIONS_WORKING,
    PILOT_ROUND1_ACTIVE_LEARNING_BATCH,
    ROUND2_STAGE_A_ANNOTATIONS,
    ROUND2_STAGE_A_BLIND_REVIEW,
    ROUND2_STAGE_B_ANNOTATIONS,
    SEED_ANNOTATIONS_ROUND1,
)


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
    parser = argparse.ArgumentParser(description="Prepare round-2 annotation files from the active-learning batch.")
    parser.add_argument("--seed-annotations", default=str(SEED_ANNOTATIONS_ROUND1))
    parser.add_argument("--active-learning-batch", default=str(PILOT_ROUND1_ACTIVE_LEARNING_BATCH))
    parser.add_argument("--master-out", default=str(MASTER_ANNOTATIONS_WORKING))
    parser.add_argument("--stage-a-out", default=str(ROUND2_STAGE_A_ANNOTATIONS))
    parser.add_argument("--stage-a-blind-out", default=str(ROUND2_STAGE_A_BLIND_REVIEW))
    parser.add_argument("--stage-b-out", default=str(ROUND2_STAGE_B_ANNOTATIONS))
    parser.add_argument("--stage-a-size", type=int, default=50)
    parser.add_argument("--double-check-size", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def annotation_view(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["label_main"] = frame["label_main"].map(normalize_label)
    frame = frame[frame["label_main"].isin(LABELS)].copy()
    frame = frame.drop_duplicates(subset=["row_id"], keep="last")
    for col in ("flag_mixed_ab", "flag_needs_context"):
        frame[col] = frame[col].fillna(0).replace({"": 0}).astype(int)
    frame["c_subtype"] = frame["c_subtype"].fillna("").astype(str).replace({"": "other"})
    frame["annotator"] = frame["annotator"].fillna("").astype(str)
    frame["label_version"] = frame["label_version"].fillna("").astype(str)
    frame["note"] = frame["note"].fillna("").astype(str)
    return frame[ANNOTATION_COLUMNS].sort_values("row_id").reset_index(drop=True)


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


def write_if_allowed(frame: pd.DataFrame, target: Path, force: bool) -> None:
    if target.exists() and not force:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)


def main() -> None:
    args = parse_args()
    seed = pd.read_csv(args.seed_annotations)
    batch = pd.read_csv(args.active_learning_batch)

    master = annotation_view(seed)
    write_if_allowed(master, Path(args.master_out), args.force)

    disagreement_rows = batch.loc[batch["selection_reason"] == "disagreement"].copy()
    remaining = batch.loc[~batch["row_id"].isin(disagreement_rows["row_id"])].sort_values(["margin_top2", "priority_rank"])
    stage_a = pd.concat(
        [
            disagreement_rows,
            remaining.head(max(0, args.stage_a_size - len(disagreement_rows))),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["row_id"])
    stage_a = stage_a.sort_values("priority_rank").reset_index(drop=True)

    stage_a_extra = stage_a.loc[stage_a["selection_reason"] != "disagreement"].sort_values(["margin_top2", "priority_rank"])
    double_check = pd.concat(
        [
            disagreement_rows,
            stage_a_extra.head(max(0, args.double_check_size - len(disagreement_rows))),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["row_id"])
    double_check = double_check.sort_values(["selection_reason", "margin_top2", "priority_rank"], ascending=[True, True, True]).reset_index(drop=True)
    double_check["blind_pass_order"] = range(1, len(double_check) + 1)

    stage_b = batch.loc[~batch["row_id"].isin(stage_a["row_id"])].copy().sort_values("priority_rank").reset_index(drop=True)

    stage_a_out = initialize_annotation_columns(stage_a, label_version="guideline_v1_round2_stage_a")
    stage_b_out = initialize_annotation_columns(stage_b, label_version="guideline_v1_1_round2_stage_b")
    blind_out = initialize_annotation_columns(double_check, label_version="guideline_v1_round2_stage_a_pass2")
    blind_out["blind_pass_order"] = double_check["blind_pass_order"]

    write_if_allowed(stage_a_out, Path(args.stage_a_out), args.force)
    write_if_allowed(blind_out, Path(args.stage_a_blind_out), args.force)
    write_if_allowed(stage_b_out, Path(args.stage_b_out), args.force)

    print(
        {
            "master_rows": len(master),
            "stage_a_rows": len(stage_a_out),
            "stage_a_reason_counts": stage_a_out["selection_reason"].value_counts().to_dict(),
            "double_check_rows": len(blind_out),
            "stage_b_rows": len(stage_b_out),
        }
    )


if __name__ == "__main__":
    main()
