#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.data import build_annotation_frame
from sox404_pilot.modeling import build_review_queue, run_model_suite
from sox404_pilot.constants import ISSUE_LABEL, REMEDIATION_LABEL
from sox404_pilot.paths import (
    DOC_SPLITS_FIXED,
    MASTER_ANNOTATIONS_WORKING,
    PILOT_ROUND1_RUN_DIR,
    SEED_ANNOTATIONS_ROUND1,
    SENTENCES_CANONICAL,
)

DEFAULT_ANNOTATIONS = MASTER_ANNOTATIONS_WORKING
if not DEFAULT_ANNOTATIONS.exists():
    DEFAULT_ANNOTATIONS = SEED_ANNOTATIONS_ROUND1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline models for the SOX404 pilot.")
    parser.add_argument("--sentences", default=str(SENTENCES_CANONICAL))
    parser.add_argument("--doc-splits", default=str(DOC_SPLITS_FIXED))
    parser.add_argument("--annotations", default=str(DEFAULT_ANNOTATIONS))
    parser.add_argument("--label-source", choices=["annotations", "legacy_proxy"], default="annotations")
    parser.add_argument("--context-mode", choices=["sentence_only", "prev_sentence"], default="sentence_only")
    parser.add_argument("--output-dir", default=str(PILOT_ROUND1_RUN_DIR))
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sentences = pd.read_csv(args.sentences)
    doc_splits = pd.read_csv(args.doc_splits)
    annotations = pd.read_csv(args.annotations) if Path(args.annotations).exists() else None
    labels = build_annotation_frame(sentences, annotations, label_source=args.label_source)

    results, winner = run_model_suite(
        sentences_df=sentences,
        labels_df=labels,
        doc_splits_df=doc_splits,
        output_dir=output_dir,
        context_mode=args.context_mode,
        random_state=args.random_state,
    )

    winner.predictions.to_csv(output_dir / "winner_predictions.csv", index=False)
    np.save(output_dir / "winner_embeddings.npy", winner.embeddings)
    alternate = sorted(
        [result for result in results if result.model_name != winner.model_name],
        key=lambda result: result.test_metrics["macro_f1"],
        reverse=True,
    )
    if alternate:
        alternate[0].predictions.to_csv(output_dir / "alternate_predictions.csv", index=False)
    review_queue = build_review_queue(winner.predictions, size=50)
    review_queue.to_csv(output_dir / "review_queue_top50.csv", index=False)

    summary = {
        "label_source": args.label_source,
        "context_mode": args.context_mode,
        "winner": winner.model_name,
        "winner_embedding_model": winner.embedding_model,
        "winner_classifier": winner.classifier,
        "winner_test_macro_f1": winner.test_metrics["macro_f1"],
        "winner_test_review_rate": winner.test_metrics["review_rate"],
        "winner_auto_precision_issue": winner.test_metrics["auto_precision"][ISSUE_LABEL],
        "winner_auto_precision_remediation": winner.test_metrics["auto_precision"][REMEDIATION_LABEL],
        "review_queue_rows": int(len(review_queue)),
        "winner_embeddings_path": str(output_dir / "winner_embeddings.npy"),
        "models": [
            {
                "model_name": result.model_name,
                "test_macro_f1": result.test_metrics["macro_f1"],
                "test_review_rate": result.test_metrics["review_rate"],
            }
            for result in results
        ],
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
