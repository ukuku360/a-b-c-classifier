from __future__ import annotations

import numpy as np
import pandas as pd

from .modeling import select_diversity_examples


def select_active_learning_batch(
    sentences_df: pd.DataFrame,
    winner_predictions: pd.DataFrame,
    alternate_predictions: pd.DataFrame | None,
    winner_embeddings: np.ndarray,
    labeled_row_ids: set[int],
    batch_size: int = 100,
    random_state: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    pool = winner_predictions.loc[~winner_predictions["row_id"].isin(labeled_row_ids)].copy()
    if pool.empty:
        return pool

    pool["selection_reason"] = ""
    selected_row_ids: list[int] = []

    def append_rows(frame: pd.DataFrame, n: int, reason: str) -> None:
        if n <= 0 or frame.empty:
            return
        available = frame.loc[~frame["row_id"].isin(selected_row_ids)]
        if available.empty:
            return
        take = available.head(n)
        for row_id in take["row_id"].tolist():
            selected_row_ids.append(int(row_id))
        pool.loc[pool["row_id"].isin(take["row_id"]), "selection_reason"] = reason

    margin_sorted = pool.sort_values(["margin_top2", "prob_max"], ascending=[True, True])
    append_rows(margin_sorted, 50, "margin")

    if alternate_predictions is not None:
        disagreement = pool.merge(
            alternate_predictions[["row_id", "pred_label", "prob_max"]],
            on="row_id",
            how="left",
            suffixes=("_winner", "_alt"),
        )
        disagreement["disagreement_score"] = (
            (disagreement["pred_label_winner"] != disagreement["pred_label_alt"]).astype(int) * 10
            + (disagreement["prob_max_winner"] - disagreement["prob_max_alt"]).abs()
        )
        disagreement = disagreement.sort_values("disagreement_score", ascending=False)
        append_rows(disagreement.rename(columns={"pred_label_winner": "pred_label"}), 20, "disagreement")

    remaining = pool.loc[~pool["row_id"].isin(selected_row_ids)]
    if not remaining.empty:
        index_lookup = {
            int(row_id): idx for idx, row_id in enumerate(winner_predictions["row_id"].tolist())
        }
        remaining_indices = np.array([index_lookup[int(row_id)] for row_id in remaining["row_id"]], dtype=int)
        diverse_indices = select_diversity_examples(
            winner_embeddings,
            remaining_indices,
            n_clusters=min(20, len(remaining_indices)),
            random_state=random_state,
        )
        diverse_row_ids = winner_predictions.iloc[diverse_indices]["row_id"].tolist() if diverse_indices else []
        diverse_frame = remaining.loc[remaining["row_id"].isin(diverse_row_ids)].copy()
        append_rows(diverse_frame, 20, "diversity")

    remaining = pool.loc[~pool["row_id"].isin(selected_row_ids)]
    if not remaining.empty:
        random_take = min(10, len(remaining), max(0, batch_size - len(selected_row_ids)))
        sampled = remaining.sample(n=random_take, random_state=int(rng.integers(0, 1_000_000)))
        append_rows(sampled, random_take, "random")

    selected = pool.loc[pool["row_id"].isin(selected_row_ids)].copy()
    selected["priority_rank"] = np.arange(1, len(selected) + 1, dtype=int)
    return selected.sort_values("priority_rank").reset_index(drop=True)
