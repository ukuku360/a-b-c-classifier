from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import MiniBatchKMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import KFold, StratifiedGroupKFold
from sklearn.svm import LinearSVC

from .constants import (
    DEFAULT_MARGIN_THRESHOLD,
    DEFAULT_PROB_THRESHOLD,
    ISSUE_LABEL,
    LABELS,
    MODEL_SPECS,
    OTHER_LABEL,
    PRIMARY_LABELS,
    REMEDIATION_LABEL,
    TARGET_AUTO_PRECISION,
    THRESHOLD_GRID,
)
from .data import make_doc_table, text_view
from .embeddings import TransformerEmbedder, cache_key, save_embeddings


@dataclass
class EvaluationResult:
    model_name: str
    embedding_model: str
    classifier: str
    thresholds: dict[str, Any]
    cv_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    predictions: pd.DataFrame
    embeddings: np.ndarray


class CentroidClassifier:
    def __init__(self, labels: list[str]) -> None:
        self.labels = labels
        self.label_to_index = {label: idx for idx, label in enumerate(labels)}
        self.centroids_: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> "CentroidClassifier":
        centroids = []
        for label in self.labels:
            members = x[y == label]
            if len(members) == 0:
                raise ValueError(f"Class {label} is absent from the training fold")
            centroid = members.mean(axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            centroids.append(centroid)
        self.centroids_ = np.vstack(centroids)
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.centroids_ is None:
            raise RuntimeError("Classifier has not been fitted")
        sims = np.clip(x @ self.centroids_.T, -1.0, 1.0)
        scaled = sims * 8.0
        scaled = scaled - scaled.max(axis=1, keepdims=True)
        exp = np.exp(scaled)
        return exp / exp.sum(axis=1, keepdims=True)


def predict_proba_aligned(model: Any, x: np.ndarray, labels: list[str]) -> np.ndarray:
    probs = model.predict_proba(x)
    model_classes = getattr(model, "classes_", None)
    if model_classes is None:
        return probs
    class_to_index = {label: idx for idx, label in enumerate(model_classes)}
    return np.column_stack([probs[:, class_to_index[label]] for label in labels])


def classifier_factory(name: str, random_state: int) -> Any:
    if name == "centroid":
        return CentroidClassifier(list(LABELS))
    if name == "logreg":
        base = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        )
        return calibrated_estimator(base)
    if name == "linear_svm":
        base = LinearSVC(class_weight="balanced", random_state=random_state)
        return calibrated_estimator(base)
    raise ValueError(f"Unsupported classifier: {name}")


def calibrated_estimator(base_estimator: Any, min_class_count: int = 3) -> CalibratedClassifierCV:
    cv = 3 if min_class_count >= 3 else 2
    return CalibratedClassifierCV(estimator=base_estimator, method="sigmoid", cv=cv)


def model_selection_score(metrics: dict[str, Any]) -> float:
    macro_f1 = metrics["macro_f1"]
    precision_bonus = np.mean([metrics["auto_precision"].get(label, 0.0) for label in PRIMARY_LABELS])
    return macro_f1 + 0.05 * precision_bonus


def slice_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    mixed = (
        frame["flag_mixed_ab"].astype(int)
        if "flag_mixed_ab" in frame.columns
        else frame["legacy_ab"].astype(int)
    )
    needs_context = (
        frame["flag_needs_context"].astype(int)
        if "flag_needs_context" in frame.columns
        else frame["heuristic_needs_context"].astype(int)
    )
    attestation = (
        (frame["c_subtype"].astype(str) == "attestation")
        if "c_subtype" in frame.columns
        else frame["legacy_hint_attestation"].astype(int) == 1
    )
    return {
        "mixed_AB": mixed.astype(bool),
        "needs_context": needs_context.astype(bool),
        "attestation": attestation.astype(bool),
        "short_sentence": frame["short_sentence"].astype(int) == 1,
        "legacy_AB": frame["legacy_ab"].astype(int) == 1,
        "legacy_negative": frame["legacy_negative"].astype(int) == 1,
    }


def _auto_accept_mask(
    predicted_labels: np.ndarray,
    probs: np.ndarray,
    labels: list[str],
    thresholds: dict[str, Any],
) -> np.ndarray:
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]
    mask = np.zeros(len(predicted_labels), dtype=bool)
    for idx, label in enumerate(predicted_labels):
        prob = probs[idx, label_to_idx[label]]
        min_prob = thresholds["per_class"].get(label, thresholds["default_prob"])
        mask[idx] = prob >= min_prob and margins[idx] >= thresholds["global_margin"]
    return mask


def search_class_thresholds(
    y_true: np.ndarray,
    probs: np.ndarray,
    labels: list[str],
    default_prob: float = DEFAULT_PROB_THRESHOLD,
    global_margin: float = DEFAULT_MARGIN_THRESHOLD,
    target_precision: float = TARGET_AUTO_PRECISION,
) -> dict[str, Any]:
    predicted = np.asarray(labels)[probs.argmax(axis=1)]
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    thresholds = {"per_class": {}, "default_prob": default_prob, "global_margin": global_margin}

    for label in labels:
        if label == OTHER_LABEL:
            thresholds["per_class"][label] = default_prob
            continue
        best_threshold = default_prob
        best_coverage = -1
        for threshold in THRESHOLD_GRID:
            subset = (predicted == label) & (probs[:, label_to_idx[label]] >= threshold) & (margins >= global_margin)
            if not subset.any():
                continue
            precision = float(np.mean(y_true[subset] == label))
            coverage = int(subset.sum())
            if precision >= target_precision and coverage > best_coverage:
                best_threshold = threshold
                best_coverage = coverage
        thresholds["per_class"][label] = best_threshold
    return thresholds


def evaluate_predictions(
    y_true: np.ndarray,
    probs: np.ndarray,
    row_frame: pd.DataFrame,
    thresholds: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    labels = list(LABELS)
    predicted = np.asarray(labels)[probs.argmax(axis=1)]
    auto_accept = _auto_accept_mask(predicted, probs, labels, thresholds)
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        predicted,
        labels=labels,
        zero_division=0,
    )
    auto_precision = {}
    auto_coverage = {}
    for label in labels:
        subset = (predicted == label) & auto_accept
        auto_coverage[label] = int(subset.sum())
        auto_precision[label] = float(np.mean(y_true[subset] == label)) if subset.any() else 0.0

    metrics = {
        "macro_f1": float(np.mean(f1)),
        "per_class": {
            label: {
                "precision": float(precision[idx]),
                "recall": float(recall[idx]),
                "f1": float(f1[idx]),
                "support": int(support[idx]),
            }
            for idx, label in enumerate(labels)
        },
        "confusion_matrix": confusion_matrix(y_true, predicted, labels=labels).tolist(),
        "review_rate": float((~auto_accept).mean()),
        "auto_precision": auto_precision,
        "auto_coverage": auto_coverage,
    }

    pred_frame = row_frame.copy()
    pred_frame["pred_label"] = predicted
    for idx, label in enumerate(labels):
        pred_frame[f"prob_{label}"] = probs[:, idx]
    pred_frame["prob_max"] = probs.max(axis=1)
    pred_frame["margin_top2"] = margins
    pred_frame["review_flag"] = (~auto_accept).astype(int)
    pred_frame["auto_accept"] = auto_accept.astype(int)

    slices = {}
    for slice_name, mask in slice_masks(pred_frame).items():
        subset_true = y_true[mask.to_numpy()]
        subset_pred = predicted[mask.to_numpy()]
        if len(subset_true) == 0:
            continue
        _, _, slice_f1, _ = precision_recall_fscore_support(
            subset_true,
            subset_pred,
            labels=labels,
            zero_division=0,
        )
        slices[slice_name] = {
            "support": int(mask.sum()),
            "macro_f1": float(np.mean(slice_f1)),
        }
    metrics["slice_metrics"] = slices
    return metrics, pred_frame


def _train_single_model(
    spec: dict[str, Any],
    x_train: np.ndarray,
    y_train: np.ndarray,
    random_state: int,
) -> Any:
    min_class_count = int(pd.Series(y_train).value_counts().min())
    if spec["classifier"] == "centroid":
        model = classifier_factory(spec["classifier"], random_state)
    else:
        model = calibrated_estimator(
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=random_state)
            if spec["classifier"] == "logreg"
            else LinearSVC(class_weight="balanced", random_state=random_state),
            min_class_count=min_class_count,
        )
    model.fit(x_train, y_train)
    return model


def encode_for_model(
    model_name: str,
    texts: list[str],
    cache_dir: Path,
    context_mode: str,
) -> np.ndarray:
    key = cache_key(model_name, context_mode, len(texts))
    cache_path = cache_dir / f"{key}.npy"
    if cache_path.exists():
        return np.load(cache_path)
    embedder = TransformerEmbedder(model_name=model_name)
    embeddings = embedder.encode(texts)
    save_embeddings(cache_path, embeddings)
    return embeddings


def _doc_level_cv(
    trainval_docs: pd.DataFrame,
    random_state: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    bucket_counts = trainval_docs["legacy_presence_bucket"].value_counts()
    min_bucket = int(bucket_counts.min())
    if min_bucket >= 3 and len(trainval_docs) >= 12:
        n_splits = min(4, min_bucket)
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        groups = trainval_docs["doc_id"].to_numpy()
        y = trainval_docs["legacy_presence_bucket"].to_numpy()
        dummy = np.zeros(len(trainval_docs))
        return list(splitter.split(dummy, y, groups))
    n_splits = 3 if len(trainval_docs) >= 6 else 2
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    return list(splitter.split(trainval_docs))


def choose_winner(results: list[EvaluationResult]) -> EvaluationResult:
    result_map = {result.model_name: result for result in results}
    e5 = result_map["e5_logreg"]
    bge = result_map["bge_svm"]
    if bge.cv_metrics["macro_f1"] >= e5.cv_metrics["macro_f1"] + 0.02:
        bge_ab = np.mean([bge.cv_metrics["auto_precision"][label] for label in PRIMARY_LABELS])
        e5_ab = np.mean([e5.cv_metrics["auto_precision"][label] for label in PRIMARY_LABELS])
        if bge_ab >= e5_ab - 0.01:
            return bge
    return e5


def prediction_frame_from_probs(
    row_frame: pd.DataFrame,
    probs: np.ndarray,
    thresholds: dict[str, Any],
) -> pd.DataFrame:
    labels = list(LABELS)
    predicted = np.asarray(labels)[probs.argmax(axis=1)]
    auto_accept = _auto_accept_mask(predicted, probs, labels, thresholds)
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]

    pred_frame = row_frame.copy()
    pred_frame["pred_label"] = predicted
    for idx, label in enumerate(labels):
        pred_frame[f"prob_{label}"] = probs[:, idx]
    pred_frame["prob_max"] = probs.max(axis=1)
    pred_frame["margin_top2"] = margins
    pred_frame["review_flag"] = (~auto_accept).astype(int)
    pred_frame["auto_accept"] = auto_accept.astype(int)
    return pred_frame


def run_model_suite(
    sentences_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    doc_splits_df: pd.DataFrame,
    output_dir: str | Path,
    context_mode: str = "sentence_only",
    random_state: int = 42,
) -> tuple[list[EvaluationResult], EvaluationResult]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    cache_dir = output_path / "embedding_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    merged = sentences_df.merge(labels_df, on="row_id", how="inner", suffixes=("", "_label"))
    if merged.empty:
        raise ValueError("No labeled rows available after merging annotations")
    if "split" not in merged.columns:
        merged = merged.merge(doc_splits_df[["doc_id", "split"]], on="doc_id", how="left")
    merged["split"] = merged["split"].fillna("trainval")

    all_texts = text_view(sentences_df, context_mode=context_mode).tolist()
    doc_table = make_doc_table(merged)
    if "split" not in doc_table.columns:
        doc_table = doc_table.merge(doc_splits_df[["doc_id", "split"]], on="doc_id", how="left")
    trainval_docs = doc_table[doc_table["split"] != "test"].reset_index(drop=True)
    test_docs = set(doc_table.loc[doc_table["split"] == "test", "doc_id"].tolist())

    trainval_mask = ~merged["doc_id"].isin(test_docs)
    test_mask = merged["doc_id"].isin(test_docs)

    trainval_frame = merged.loc[trainval_mask].reset_index(drop=True)
    test_frame = merged.loc[test_mask].reset_index(drop=True)
    if trainval_frame.empty:
        raise ValueError("No labeled rows available in the train/validation split")
    if test_frame.empty:
        raise ValueError(
            "No labeled rows landed in the fixed test split. Add labels from the held-out filings or run --label-source legacy_proxy."
        )

    results = []
    for spec in MODEL_SPECS:
        all_embeddings = encode_for_model(spec["embedding_model"], all_texts, cache_dir, context_mode)
        labeled_embeddings = all_embeddings[merged["row_id"].to_numpy() - 1]
        trainval_embeddings = labeled_embeddings[trainval_mask.to_numpy()]
        test_embeddings = labeled_embeddings[test_mask.to_numpy()]

        oof_probs = np.zeros((len(trainval_frame), len(LABELS)), dtype=float)
        doc_cv_table = trainval_docs[["doc_id", "legacy_presence_bucket"]].reset_index(drop=True)
        splits = _doc_level_cv(doc_cv_table, random_state=random_state)
        for fold_idx, (doc_train_idx, doc_val_idx) in enumerate(splits):
            train_docs = set(doc_cv_table.iloc[doc_train_idx]["doc_id"].tolist())
            val_docs = set(doc_cv_table.iloc[doc_val_idx]["doc_id"].tolist())
            row_train = trainval_frame["doc_id"].isin(train_docs).to_numpy()
            row_val = trainval_frame["doc_id"].isin(val_docs).to_numpy()
            model = _train_single_model(
                spec,
                trainval_embeddings[row_train],
                trainval_frame.loc[row_train, "label_main"].to_numpy(),
                random_state + fold_idx,
            )
            oof_probs[row_val] = predict_proba_aligned(model, trainval_embeddings[row_val], list(LABELS))

        thresholds = search_class_thresholds(
            trainval_frame["label_main"].to_numpy(),
            oof_probs,
            list(LABELS),
        )
        cv_metrics, _ = evaluate_predictions(
            trainval_frame["label_main"].to_numpy(),
            oof_probs,
            trainval_frame,
            thresholds,
        )

        trainval_model = _train_single_model(
            spec,
            trainval_embeddings,
            trainval_frame["label_main"].to_numpy(),
            random_state,
        )
        test_metrics, test_pred_frame = evaluate_predictions(
            test_frame["label_main"].to_numpy(),
            predict_proba_aligned(trainval_model, test_embeddings, list(LABELS)),
            test_frame,
            thresholds,
        )

        full_model = _train_single_model(
            spec,
            labeled_embeddings,
            merged["label_main"].to_numpy(),
            random_state,
        )
        full_probs = predict_proba_aligned(full_model, all_embeddings, list(LABELS))
        full_pred_frame = prediction_frame_from_probs(
            sentences_df,
            full_probs,
            thresholds,
        )
        full_pred_frame["model_version"] = spec["name"]

        result = EvaluationResult(
            model_name=spec["name"],
            embedding_model=spec["embedding_model"],
            classifier=spec["classifier"],
            thresholds=thresholds,
            cv_metrics=cv_metrics,
            test_metrics=test_metrics,
            predictions=full_pred_frame,
            embeddings=all_embeddings,
        )
        results.append(result)

        test_pred_frame.to_csv(output_path / f"test_predictions_{spec['name']}.csv", index=False)
        full_pred_frame.to_csv(output_path / f"predictions_{spec['name']}.csv", index=False)
        np.save(output_path / f"embeddings_{spec['name']}.npy", all_embeddings)

    winner = choose_winner(results)
    write_experiment_log(output_path / "experiment_log.json", results, winner, context_mode=context_mode, random_state=random_state)
    comparison_rows = []
    for result in results:
        comparison_rows.append(
            {
                "model_name": result.model_name,
                "embedding_model": result.embedding_model,
                "classifier": result.classifier,
                "cv_macro_f1": result.cv_metrics["macro_f1"],
                "test_macro_f1": result.test_metrics["macro_f1"],
                "test_review_rate": result.test_metrics["review_rate"],
                "test_auto_precision_issue": result.test_metrics["auto_precision"][ISSUE_LABEL],
                "test_auto_precision_remediation": result.test_metrics["auto_precision"][REMEDIATION_LABEL],
            }
        )
    pd.DataFrame(comparison_rows).sort_values("test_macro_f1", ascending=False).to_csv(
        output_path / "model_comparison.csv",
        index=False,
    )
    return results, winner


def write_experiment_log(
    path: str | Path,
    results: list[EvaluationResult],
    winner: EvaluationResult,
    context_mode: str,
    random_state: int,
) -> None:
    payload = {
        "dataset_version": "token404_sample_yh.xlsx",
        "label_version": "runtime_input",
        "split_seed": random_state,
        "context_mode": context_mode,
        "winner": winner.model_name,
        "models": [
            {
                "model_name": result.model_name,
                "embedding_model": result.embedding_model,
                "classifier": result.classifier,
                "calibration_method": "sigmoid" if result.classifier != "centroid" else None,
                "thresholds": result.thresholds,
                "cv_metrics": result.cv_metrics,
                "test_metrics": result.test_metrics,
            }
            for result in results
        ],
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_review_queue(
    prediction_frame: pd.DataFrame,
    size: int = 50,
) -> pd.DataFrame:
    queue = prediction_frame[prediction_frame["review_flag"] == 1].copy()
    if queue.empty:
        return queue
    queue["uncertainty_score"] = (1.0 - queue["prob_max"]) + (1.0 - queue["margin_top2"])
    queue = queue.sort_values(["uncertainty_score", "prob_max"], ascending=[False, True]).head(size)
    return queue


def select_diversity_examples(
    embeddings: np.ndarray,
    candidate_indices: np.ndarray,
    n_clusters: int,
    random_state: int,
) -> list[int]:
    if len(candidate_indices) == 0:
        return []
    cluster_count = min(n_clusters, len(candidate_indices))
    kmeans = MiniBatchKMeans(n_clusters=cluster_count, random_state=random_state, batch_size=max(cluster_count, 8))
    candidate_embeddings = embeddings[candidate_indices]
    assignments = kmeans.fit_predict(candidate_embeddings)
    selected = []
    for cluster_id in range(cluster_count):
        cluster_positions = np.where(assignments == cluster_id)[0]
        if len(cluster_positions) == 0:
            continue
        cluster_indices = candidate_indices[cluster_positions]
        centroid = kmeans.cluster_centers_[cluster_id]
        distances = np.linalg.norm(embeddings[cluster_indices] - centroid, axis=1)
        selected.append(int(cluster_indices[np.argmin(distances)]))
    return selected
