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

from sox404_pilot.data import build_annotation_frame
from sox404_pilot.modeling import run_model_suite
from sox404_pilot.paths import (
    CONTEXT_EXPERIMENT_ROUND1_DIR,
    DOC_SPLITS_FIXED,
    MASTER_ANNOTATIONS_WORKING,
    SEED_ANNOTATIONS_ROUND1,
    SENTENCES_CANONICAL,
)

DEFAULT_ANNOTATIONS = MASTER_ANNOTATIONS_WORKING
if not DEFAULT_ANNOTATIONS.exists():
    DEFAULT_ANNOTATIONS = SEED_ANNOTATIONS_ROUND1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare sentence-only and prev-sentence context variants.")
    parser.add_argument("--sentences", default=str(SENTENCES_CANONICAL))
    parser.add_argument("--doc-splits", default=str(DOC_SPLITS_FIXED))
    parser.add_argument("--annotations", default=str(DEFAULT_ANNOTATIONS))
    parser.add_argument("--label-source", choices=["annotations", "legacy_proxy"], default="annotations")
    parser.add_argument("--output-dir", default=str(CONTEXT_EXPERIMENT_ROUND1_DIR))
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

    _, sentence_only = run_model_suite(
        sentences_df=sentences,
        labels_df=labels,
        doc_splits_df=doc_splits,
        output_dir=output_dir / "sentence_only",
        context_mode="sentence_only",
        random_state=args.random_state,
    )
    _, prev_sentence = run_model_suite(
        sentences_df=sentences,
        labels_df=labels,
        doc_splits_df=doc_splits,
        output_dir=output_dir / "prev_sentence",
        context_mode="prev_sentence",
        random_state=args.random_state,
    )

    sentence_slice = sentence_only.test_metrics["slice_metrics"].get("needs_context", {})
    prev_slice = prev_sentence.test_metrics["slice_metrics"].get("needs_context", {})
    comparison = {
        "sentence_only": {
            "winner": sentence_only.model_name,
            "test_macro_f1": sentence_only.test_metrics["macro_f1"],
            "needs_context_macro_f1": sentence_slice.get("macro_f1"),
            "review_rate": sentence_only.test_metrics["review_rate"],
        },
        "prev_sentence": {
            "winner": prev_sentence.model_name,
            "test_macro_f1": prev_sentence.test_metrics["macro_f1"],
            "needs_context_macro_f1": prev_slice.get("macro_f1"),
            "review_rate": prev_sentence.test_metrics["review_rate"],
        },
    }
    (output_dir / "context_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
