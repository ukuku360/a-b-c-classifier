#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.active_learning import select_active_learning_batch
from sox404_pilot.constants import LABELS, normalize_label

DEFAULT_ANNOTATIONS = PROJECT_ROOT / "data" / "master_annotations.csv"
if not DEFAULT_ANNOTATIONS.exists():
    DEFAULT_ANNOTATIONS = PROJECT_ROOT / "data" / "seed_annotations_v1.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select the next active-learning batch.")
    parser.add_argument("--sentences", default=str(PROJECT_ROOT / "data" / "sentences.csv"))
    parser.add_argument("--annotations", default=str(DEFAULT_ANNOTATIONS))
    parser.add_argument("--winner-predictions", default=str(PROJECT_ROOT / "outputs" / "pilot_run" / "winner_predictions.csv"))
    parser.add_argument("--alternate-predictions", default="")
    parser.add_argument("--winner-embeddings", default=str(PROJECT_ROOT / "outputs" / "pilot_run" / "winner_embeddings.npy"))
    parser.add_argument("--output-file", default=str(PROJECT_ROOT / "outputs" / "pilot_run" / "active_learning_batch_round1.csv"))
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sentences = pd.read_csv(args.sentences)
    annotations = pd.read_csv(args.annotations) if Path(args.annotations).exists() else pd.DataFrame(columns=["row_id", "label_main"])
    annotations["label_main"] = annotations["label_main"].map(normalize_label)
    labeled_row_ids = set(annotations.loc[annotations["label_main"].isin(LABELS), "row_id"].astype(int).tolist())
    winner_predictions = pd.read_csv(args.winner_predictions)
    alternate_predictions = pd.read_csv(args.alternate_predictions) if args.alternate_predictions else None
    winner_embeddings = np.load(args.winner_embeddings)

    batch = select_active_learning_batch(
        sentences_df=sentences,
        winner_predictions=winner_predictions,
        alternate_predictions=alternate_predictions,
        winner_embeddings=winner_embeddings,
        labeled_row_ids=labeled_row_ids,
        batch_size=args.batch_size,
        random_state=args.random_state,
    )
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    batch.to_csv(args.output_file, index=False)
    print(f"selected_rows={len(batch)} output={args.output_file}")


if __name__ == "__main__":
    main()
