# SOX404 Sentence Classification Pilot

이 디렉터리는 [token404_sample_yh.xlsx](</Users/nmduk/PROJECTS/A:B:C Classifier/token404_sample_yh.xlsx>)를 기준으로 SOX404 문장을 `ISSUE / REMEDIATION / OTHER`로 분류하는 파일럿 파이프라인입니다.

## Outputs
- `data/sentences.csv`: canonical sentence table
- `data/seed_annotations_v1.csv`: 200-row seed annotation template
- `data/master_annotations.csv`: working master annotations used for current modeling runs
- `data/boundary_relabel_queue_v1.csv`: 50-row blind relabel queue
- `data/doc_splits.csv`: fixed doc-level holdout split
- `outputs/...`: baseline metrics, predictions, review queue, active-learning batch

## Quickstart
1. Canonical tables와 seed를 생성합니다.

```bash
python3 scripts/prepare_pilot_dataset.py
```

2. seed 기준 라벨이 있으면 working master를 준비하고 round batch를 분리합니다.

```bash
python3 scripts/prepare_round2_annotations.py --force
```

3. `data/master_annotations.csv`를 기준으로 현재 라벨을 누적 관리합니다.

4. 수동 라벨이 아직 없으면 proxy smoke run을 돌립니다.

```bash
python3 scripts/run_pilot_baselines.py --label-source legacy_proxy --output-dir outputs/proxy_smoke
```

5. 수동 라벨이 채워졌으면 실제 파일럿을 돌립니다.

```bash
python3 scripts/run_pilot_baselines.py --label-source annotations --output-dir outputs/pilot_run
```

6. 다음 active-learning 배치를 뽑습니다.

```bash
python3 scripts/run_active_learning_round.py \
  --winner-predictions outputs/pilot_run/winner_predictions.csv \
  --winner-embeddings outputs/pilot_run/winner_embeddings.npy \
  --output-file outputs/pilot_run/active_learning_batch_round1.csv
```

7. `needs_context` 후보만 `prev_sentence + sentence`로 비교하려면 context experiment를 실행합니다.

```bash
python3 scripts/run_context_experiment.py --label-source annotations
```

## Labeling Policy
- `ISSUE`: weakness, risk, misstatement, ineffective control, financial impact
- `REMEDIATION`: remediation plan/action, implementation step, control enhancement
- `OTHER`: background, status, effect, attestation, needs_context, mixed_AB

기존 `A/B/C` 값이 들어 있는 예전 CSV도 읽을 수 있지만, 현재 canonical 라벨은 `ISSUE / REMEDIATION / OTHER`입니다.

현재 round 기준 세부 기준은 [guideline_v1_1.md](/Users/nmduk/PROJECTS/A:B:C%20Classifier/docs/guideline_v1_1.md)에 정리돼 있습니다. round-1 기준은 [guideline_v1.md](/Users/nmduk/PROJECTS/A:B:C%20Classifier/docs/guideline_v1.md)에 보존돼 있습니다.
