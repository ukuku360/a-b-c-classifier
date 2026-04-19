#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sox404_pilot.data import load_raw_workbook, make_doc_splits, normalize_sentences, sample_seed_annotations
from sox404_pilot.paths import (
    BOUNDARY_RELABEL_QUEUE_ROUND1,
    DOC_SPLITS_FIXED,
    PILOT_DATASET_SUMMARY,
    SEED_ANNOTATIONS_ROUND1,
    SENTENCES_CANONICAL,
    SOURCE_WORKBOOK,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare canonical tables and seed annotation queues.")
    parser.add_argument("--input", default=str(SOURCE_WORKBOOK))
    parser.add_argument("--sentences-out", default=str(SENTENCES_CANONICAL))
    parser.add_argument("--annotations-out", default=str(SEED_ANNOTATIONS_ROUND1))
    parser.add_argument("--blind-relabel-out", default=str(BOUNDARY_RELABEL_QUEUE_ROUND1))
    parser.add_argument("--doc-splits-out", default=str(DOC_SPLITS_FIXED))
    parser.add_argument("--summary-out", default=str(PILOT_DATASET_SUMMARY))
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    raw = load_raw_workbook(args.input)
    sentences = normalize_sentences(raw)
    doc_splits = make_doc_splits(sentences, random_state=args.random_state)
    sentences_with_splits = sentences.merge(doc_splits[["doc_id", "split"]], on="doc_id", how="left")
    seed = sample_seed_annotations(sentences_with_splits, random_state=args.random_state)

    Path(args.sentences_out).parent.mkdir(parents=True, exist_ok=True)
    sentences_with_splits.to_csv(args.sentences_out, index=False)
    seed.annotations.to_csv(args.annotations_out, index=False)
    seed.blind_relabel_queue.to_csv(args.blind_relabel_out, index=False)
    doc_splits.to_csv(args.doc_splits_out, index=False)

    summary = {
        "rows": int(len(sentences_with_splits)),
        "docs": int(sentences_with_splits["doc_id"].nunique()),
        "test_docs": int((doc_splits["split"] == "test").sum()),
        "trainval_docs": int((doc_splits["split"] == "trainval").sum()),
        "seed_rows": int(len(seed.annotations)),
        "boundary_rows": int(seed.annotations["is_boundary_case"].sum()),
        "proxy_label_counts": sentences_with_splits["proxy_label_main"].value_counts().to_dict(),
        "seed_sampling_counts": seed.annotations["sampling_bucket"].value_counts().to_dict(),
        "seed_split_counts": seed.annotations["split"].value_counts().to_dict(),
    }
    Path(args.summary_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
