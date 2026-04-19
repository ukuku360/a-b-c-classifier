# SOX404 Sentence Classification Pilot

이 저장소는 SOX404 문장을 `ISSUE / REMEDIATION / OTHER`로 분류하기 위한 연구용 파일럿 파이프라인과 주석 데이터셋을 정리한 작업 공간입니다.

공유용으로 구조를 다시 정리해 두었기 때문에, 아래 네 파일부터 보면 전체 맥락을 빠르게 파악할 수 있습니다.

- `data/annotations/master_annotations_full_round3.csv`: 최종 full-coverage master annotation
- `docs/annotation_process.md`: 원본 파일에서 최종 master까지의 생성 과정
- `docs/annotation_guidelines_round2.md`: 현재 기준의 annotation guideline
- `docs/project_structure.md`: 폴더 구조와 핵심 파일 안내

## Directory Guide

- `data/raw/`: 원본 입력 파일
- `data/processed/`: canonical sentence table, fixed split, 데이터셋 요약
- `data/annotations/`: round별 수동 라벨 파일과 최종 master annotation
- `docs/`: annotation guideline, 생성 과정 설명, 구조 안내 문서
- `results/model_runs/`: baseline 실험, 예측값, embedding, active-learning batch
- `results/context_experiments/`: sentence-only vs prev-sentence 비교 실험
- `results/annotation_quality/`: round1/round2 품질 점검 결과
- `results/round3_reaudit/`: class별 round3 전수 재감사 배치와 병합 결과
- `scripts/`: 데이터 준비, 실험 실행, batch 생성/병합 스크립트
- `src/sox404_pilot/`: 공통 로직

## Key Files

- `data/raw/source_workbook_token404_sample_yh.xlsx`: 연구의 원본 소스 workbook
- `data/processed/sentences_canonical.csv`: 문장 단위 canonical table
- `data/processed/doc_splits_fixed.csv`: 문서 단위 고정 split
- `data/annotations/seed_annotations_round1.csv`: round1 seed annotation
- `data/annotations/master_annotations_working.csv`: 모델링에 쓰인 working master
- `data/annotations/master_annotations_full_round3.csv`: 최종 full master

## Quickstart

1. canonical table과 초기 seed annotation 파일을 생성합니다.

```bash
python3 scripts/prepare_pilot_dataset.py
```

2. round2 annotation batch와 working master를 준비합니다.

```bash
python3 scripts/prepare_round2_annotations.py --force
```

3. 수동 라벨이 아직 없으면 legacy proxy 기준 smoke run을 실행합니다.

```bash
python3 scripts/run_pilot_baselines.py \
  --label-source legacy_proxy \
  --output-dir results/model_runs/proxy_smoke_legacy_proxy
```

4. 수동 라벨이 채워졌으면 실제 pilot baseline을 실행합니다.

```bash
python3 scripts/run_pilot_baselines.py \
  --label-source annotations \
  --output-dir results/model_runs/pilot_round1_seed
```

5. 다음 active-learning batch를 생성합니다.

```bash
python3 scripts/run_active_learning_round.py \
  --winner-predictions results/model_runs/pilot_round1_seed/winner_predictions.csv \
  --winner-embeddings results/model_runs/pilot_round1_seed/winner_embeddings.npy \
  --output-file results/model_runs/pilot_round1_seed/active_learning_batch_round1.csv
```

6. `needs_context` 후보에 대해 문맥 효과를 비교합니다.

```bash
python3 scripts/run_context_experiment.py --label-source annotations
```

## Labeling Policy

- `ISSUE`: weakness, risk, misstatement, ineffective control, financial impact
- `REMEDIATION`: remediation plan/action, implementation step, control enhancement
- `OTHER`: background, status, effect, attestation, needs_context, mixed_AB

기존 `A/B/C` 값이 있는 예전 CSV도 읽을 수 있지만, 현재 canonical 라벨은 `ISSUE / REMEDIATION / OTHER`입니다.

현재 기준은 `docs/annotation_guidelines_round2.md`에, round1 보존본은 `docs/annotation_guidelines_round1.md`에 있습니다.
