from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import numpy as np
import pandas as pd

from .constants import (
    DEFAULT_TEST_DOCS,
    ISSUE_LABEL,
    LABELS,
    LEGACY_HINT_COLUMNS,
    OTHER_LABEL,
    REMEDIATION_LABEL,
    SHORT_SENTENCE_CHARS,
    SOURCE_XLSX,
    normalize_label,
)


DEICTIC_START_RE = re.compile(
    r"^(this|these|it|they|such|those|here|there|to address|to remediate|to resolve|in response|accordingly|therefore|however|as a result)\b",
    re.IGNORECASE,
)
EFFECT_RE = re.compile(
    r"\b(result(ed)?|impact(ed)?|improv(e|ed|ement)|enhanc(e|ed|ement)|increase(d)?|decrease(d)?)\b",
    re.IGNORECASE,
)
STATUS_RE = re.compile(
    r"\b(currently|presently|as of|at present|we continue|management continues|there were no changes)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SeedSample:
    annotations: pd.DataFrame
    blind_relabel_queue: pd.DataFrame


def load_raw_workbook(path: str | None = None) -> pd.DataFrame:
    source = SOURCE_XLSX if path is None else path
    return pd.read_excel(source)


def _proxy_label_row(row: pd.Series) -> tuple[str, int, str]:
    impact = int(row["impact"])
    remediation = int(row["remediation"])
    attestation = int(row["attestation"])
    mixed = int(impact == 1 and remediation == 1)

    if attestation == 1:
        return OTHER_LABEL, mixed, "attestation"
    if impact == 1 and remediation == 0:
        return ISSUE_LABEL, mixed, "other"
    if remediation == 1 and impact == 0:
        return REMEDIATION_LABEL, mixed, "other"

    text = str(row["sentence_norm"])
    if EFFECT_RE.search(text):
        return OTHER_LABEL, mixed, "effect"
    if STATUS_RE.search(text):
        return OTHER_LABEL, mixed, "status"
    return OTHER_LABEL, mixed, "background"


def normalize_sentences(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["row_id"] = np.arange(1, len(df) + 1, dtype=int)
    proxy_meta = df.apply(_proxy_label_row, axis=1, result_type="expand")
    proxy_meta.columns = ["proxy_label_main", "proxy_flag_mixed_ab", "proxy_c_subtype"]

    out = pd.DataFrame(
        {
            "row_id": df["row_id"],
            "doc_id": df["text_key"].astype(str),
            "sent_id": df["seq"].astype(int),
            "text_raw": df["sentence"].fillna("").astype(str),
            "text_norm": df["sentence_norm"].fillna("").astype(str),
            "quarter_end": pd.to_datetime(df["quarter_end"]),
            "cik": df["cik"].astype(str).str.zfill(10),
            "prev_text_raw": df.groupby("text_key")["sentence"].shift(1).fillna("").astype(str),
            "prev_text_norm": df.groupby("text_key")["sentence_norm"].shift(1).fillna("").astype(str),
            "text_len_chars": df["sentence_norm"].fillna("").astype(str).str.len().astype(int),
            "short_sentence": (df["sentence_norm"].fillna("").astype(str).str.len() <= SHORT_SENTENCE_CHARS).astype(int),
            "heuristic_needs_context": (
                df["sentence_norm"].fillna("").astype(str).str.match(DEICTIC_START_RE).astype(int)
            ),
            "proxy_label_main": proxy_meta["proxy_label_main"],
            "proxy_flag_mixed_ab": proxy_meta["proxy_flag_mixed_ab"].astype(int),
            "proxy_c_subtype": proxy_meta["proxy_c_subtype"],
        }
    )

    for col in LEGACY_HINT_COLUMNS:
        out[f"legacy_hint_{col}"] = df[col]

    out["legacy_hint_impact"] = out["legacy_hint_impact"].astype(int)
    out["legacy_hint_remediation"] = out["legacy_hint_remediation"].astype(int)
    out["legacy_hint_attestation"] = out["legacy_hint_attestation"].astype(int)
    out["legacy_ab"] = ((out["legacy_hint_impact"] == 1) & (out["legacy_hint_remediation"] == 1)).astype(int)
    out["legacy_negative"] = (
        (out["legacy_hint_impact"] == 0)
        & (out["legacy_hint_remediation"] == 0)
        & (out["legacy_hint_attestation"] == 0)
    ).astype(int)
    return out


def make_doc_table(sentences_df: pd.DataFrame) -> pd.DataFrame:
    doc_table = (
        sentences_df.groupby("doc_id")
        .agg(
            has_A=("legacy_hint_impact", "max"),
            has_B=("legacy_hint_remediation", "max"),
            has_attestation=("legacy_hint_attestation", "max"),
        )
        .reset_index()
    )

    def bucket(row: pd.Series) -> str:
        if row["has_A"] and row["has_B"]:
            return "issue_and_remediation"
        if row["has_A"]:
            return "issue_only"
        if row["has_B"]:
            return "remediation_only"
        if row["has_attestation"]:
            return "attestation_only"
        return "negative_only"

    doc_table["legacy_presence_bucket"] = doc_table.apply(bucket, axis=1)
    return doc_table


def make_doc_splits(
    sentences_df: pd.DataFrame,
    test_docs: int = DEFAULT_TEST_DOCS,
    random_state: int = 42,
) -> pd.DataFrame:
    from sklearn.model_selection import StratifiedShuffleSplit

    doc_table = make_doc_table(sentences_df)
    if test_docs >= len(doc_table):
        raise ValueError("test_docs must be smaller than the number of unique documents")

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_docs, random_state=random_state)
    try:
        train_idx, test_idx = next(
            splitter.split(doc_table["doc_id"], doc_table["legacy_presence_bucket"])
        )
    except ValueError:
        rng = np.random.default_rng(random_state)
        test_idx = rng.choice(doc_table.index.to_numpy(), size=test_docs, replace=False)
        train_idx = np.setdiff1d(doc_table.index.to_numpy(), test_idx)

    split_map = pd.DataFrame({"doc_id": doc_table["doc_id"], "split": "trainval"})
    split_map.loc[test_idx, "split"] = "test"
    split_map = split_map.merge(doc_table[["doc_id", "legacy_presence_bucket"]], on="doc_id", how="left")
    return split_map.sort_values(["split", "doc_id"]).reset_index(drop=True)


def _take_without_replacement(
    frame: pd.DataFrame,
    n: int,
    used_ids: set[int],
    rng: np.random.Generator,
) -> pd.DataFrame:
    available = frame.loc[~frame["row_id"].isin(used_ids)]
    if available.empty:
        return available.copy()
    if len(available) <= n:
        result = available.copy()
    else:
        result = available.sample(n=n, random_state=int(rng.integers(0, 1_000_000)))
    used_ids.update(result["row_id"].tolist())
    return result.copy()


def sample_seed_annotations(sentences_df: pd.DataFrame, random_state: int = 42) -> SeedSample:
    rng = np.random.default_rng(random_state)
    used_ids: set[int] = set()

    a_only = sentences_df[(sentences_df["legacy_hint_impact"] == 1) & (sentences_df["legacy_hint_remediation"] == 0)]
    b_only = sentences_df[
        (sentences_df["legacy_hint_remediation"] == 1)
        & (sentences_df["legacy_hint_impact"] == 0)
        & (sentences_df["legacy_hint_attestation"] == 0)
    ]
    ab = sentences_df[sentences_df["legacy_ab"] == 1]
    attestation = sentences_df[sentences_df["legacy_hint_attestation"] == 1]
    background = sentences_df[
        (sentences_df["legacy_negative"] == 1)
        & (sentences_df["legacy_hint_find_opinion"] == False)
        & (sentences_df["short_sentence"] == 0)
    ]
    negatives = sentences_df[sentences_df["legacy_negative"] == 1]

    sampled = []
    sampled.append(_take_without_replacement(a_only, 60, used_ids, rng).assign(sampling_bucket="legacy_issue_only"))
    sampled.append(
        _take_without_replacement(b_only, 60, used_ids, rng).assign(sampling_bucket="legacy_remediation_only")
    )
    sampled.append(
        _take_without_replacement(ab, 30, used_ids, rng).assign(sampling_bucket="legacy_issue_and_remediation")
    )
    sampled.append(_take_without_replacement(attestation, 10, used_ids, rng).assign(sampling_bucket="legacy_attestation"))
    sampled.append(_take_without_replacement(background, 10, used_ids, rng).assign(sampling_bucket="legacy_background"))
    sampled.append(_take_without_replacement(negatives, 30, used_ids, rng).assign(sampling_bucket="legacy_negative"))

    seed = pd.concat(sampled, ignore_index=True)
    if len(seed) < 200:
        filler_pool = sentences_df.loc[~sentences_df["row_id"].isin(used_ids)]
        filler = _take_without_replacement(filler_pool, 200 - len(seed), used_ids, rng).assign(
            sampling_bucket="legacy_filler"
        )
        seed = pd.concat([seed, filler], ignore_index=True)

    boundary_priority = pd.concat(
        [
            seed[seed["legacy_ab"] == 1],
            seed[seed["heuristic_needs_context"] == 1],
            seed[seed["legacy_hint_find_opinion"] == True],
            seed[
                seed["legacy_hint_remedia_start_seq"].notna()
                & ((seed["sent_id"] - seed["legacy_hint_remedia_start_seq"]).abs() <= 1)
            ],
            seed[seed["short_sentence"] == 1],
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["row_id"])
    if len(boundary_priority) < 50:
        boundary_priority = pd.concat(
            [
                boundary_priority,
                seed.loc[~seed["row_id"].isin(boundary_priority["row_id"])].sample(
                    n=min(50 - len(boundary_priority), len(seed) - len(boundary_priority)),
                    random_state=random_state,
                ),
            ],
            ignore_index=True,
        ).drop_duplicates(subset=["row_id"])

    boundary_ids = set(boundary_priority.head(50)["row_id"].tolist())

    seed = seed.sort_values(["sampling_bucket", "doc_id", "sent_id", "row_id"]).reset_index(drop=True)
    seed["is_boundary_case"] = seed["row_id"].isin(boundary_ids).astype(int)
    seed["legacy_suggested_label"] = seed["proxy_label_main"]
    seed["legacy_suggested_mixed_ab"] = seed["proxy_flag_mixed_ab"]
    seed["legacy_suggested_needs_context"] = seed["heuristic_needs_context"]
    seed["legacy_suggested_c_subtype"] = seed["proxy_c_subtype"]

    for col in ("label_main", "flag_mixed_ab", "flag_needs_context", "c_subtype", "annotator", "note"):
        seed[col] = ""
    seed["label_version"] = "guideline_v1"

    blind_queue = (
        seed.loc[seed["is_boundary_case"] == 1]
        .sample(frac=1.0, random_state=random_state)
        .reset_index(drop=True)
        .copy()
    )
    blind_queue["blind_pass_order"] = np.arange(1, len(blind_queue) + 1, dtype=int)
    for col in ("label_main", "flag_mixed_ab", "flag_needs_context", "c_subtype", "annotator", "note"):
        blind_queue[col] = ""

    return SeedSample(annotations=seed, blind_relabel_queue=blind_queue)


def build_annotation_frame(
    sentences_df: pd.DataFrame,
    annotations_df: pd.DataFrame | None = None,
    label_source: str = "annotations",
) -> pd.DataFrame:
    if label_source == "legacy_proxy":
        frame = sentences_df[["row_id", "proxy_label_main", "proxy_flag_mixed_ab", "heuristic_needs_context", "proxy_c_subtype"]].copy()
        frame = frame.rename(
            columns={
                "proxy_label_main": "label_main",
                "proxy_flag_mixed_ab": "flag_mixed_ab",
                "heuristic_needs_context": "flag_needs_context",
                "proxy_c_subtype": "c_subtype",
            }
        )
        frame["label_main"] = frame["label_main"].map(normalize_label)
        frame["annotator"] = "legacy_proxy"
        frame["label_version"] = "legacy_proxy_v1"
        frame["note"] = ""
        return frame

    if annotations_df is None:
        raise ValueError("annotations_df is required when label_source='annotations'")

    frame = annotations_df.copy()
    frame["label_main"] = frame["label_main"].map(normalize_label)
    labeled = frame[frame["label_main"].isin(LABELS)].copy()
    if labeled.empty:
        raise ValueError("No adjudicated labels found in annotations file")
    labeled = labeled.drop_duplicates(subset=["row_id"], keep="last").copy()

    for col in ("flag_mixed_ab", "flag_needs_context"):
        labeled[col] = labeled[col].fillna(0).replace({"": 0}).astype(int)
    labeled["c_subtype"] = labeled["c_subtype"].fillna("").astype(str).replace({"": "other"})
    labeled["annotator"] = labeled["annotator"].fillna("").astype(str)
    labeled["label_version"] = labeled["label_version"].fillna("guideline_v1").astype(str)
    labeled["note"] = labeled["note"].fillna("").astype(str)
    return labeled[
        [
            "row_id",
            "label_main",
            "flag_mixed_ab",
            "flag_needs_context",
            "c_subtype",
            "annotator",
            "label_version",
            "note",
        ]
    ]


def text_view(sentences_df: pd.DataFrame, context_mode: str = "sentence_only") -> pd.Series:
    if context_mode == "sentence_only":
        return sentences_df["text_norm"].fillna("").astype(str)
    if context_mode == "prev_sentence":
        prev = sentences_df["prev_text_norm"].fillna("").astype(str)
        current = sentences_df["text_norm"].fillna("").astype(str)
        return np.where(prev.eq(""), current, prev + " [SEP] " + current)
    raise ValueError(f"Unsupported context_mode: {context_mode}")


def ensure_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in frame.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
