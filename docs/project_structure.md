# Project Structure

이 문서는 동료와 파일을 공유할 때 빠르게 길을 찾을 수 있도록 폴더 구조와 핵심 파일을 요약한 안내서다.

## 먼저 볼 파일

- `data/annotations/master_annotations_full_round3.csv`: 최종 분석용 full master annotation
- `docs/annotation_process.md`: 이 파일이 어떻게 만들어졌는지 설명
- `docs/annotation_guidelines_round2.md`: 현재 annotation 기준
- `results/model_runs/pilot_round2_master/run_summary.json`: round2 기준 baseline 요약

## 폴더 구조

```text
.
├── data
│   ├── raw
│   ├── processed
│   └── annotations
├── docs
├── results
│   ├── annotation_quality
│   ├── context_experiments
│   ├── model_runs
│   ├── round3_reaudit
│   └── validation
├── scripts
└── src
```

## Directory Map

### `data/raw`

- 원본 입력 파일을 둔다.
- 현재 핵심 파일: `source_workbook_token404_sample_yh.xlsx`

### `data/processed`

- 원본에서 바로 파생된 정규화 데이터와 split 정보를 둔다.
- `sentences_canonical.csv`: 문장 단위 canonical table
- `doc_splits_fixed.csv`: 문서 단위 고정 train/test split
- `pilot_dataset_summary.json`: 초기 샘플링 및 분포 요약

### `data/annotations`

- 수동 라벨 파일과 최종 annotation 산출물을 둔다.
- `seed_annotations_round1.csv`: round1 seed annotation
- `boundary_relabel_queue_round1.csv`: round1 blind relabel queue
- `round2_stage_a_annotations.csv`, `round2_stage_a_blind_review.csv`, `round2_stage_b_annotations.csv`
- `round2_adjudicated_annotations.csv`: round2 adjudication 완료본
- `master_annotations_working.csv`: 모델링에 사용한 working master
- `master_annotations_full_round3.csv`: 최종 full-coverage master

### `docs`

- 연구 공유용 설명 문서를 둔다.
- `annotation_guidelines_round1.md`: round1 기준 보존본
- `annotation_guidelines_round2.md`: 현재 기준
- `annotation_process.md`: 데이터 생성 과정
- `project_structure.md`: 이 문서

### `results/model_runs`

- baseline 모델 실험 결과를 둔다.
- `proxy_smoke_legacy_proxy/`: legacy proxy 기준 smoke run
- `pilot_round1_seed/`: round1 seed 기준 pilot run
- `pilot_round2_master/`: round2 working master 기준 pilot run

### `results/context_experiments`

- 문맥 포함 여부 비교 실험 결과를 둔다.
- `working_master_round1/`
- `working_master_round2/`

### `results/annotation_quality`

- annotation 품질 점검용 비교 결과를 둔다.
- `round1_boundary_review/`
- `round2_adjudication/`

### `results/round3_reaudit`

- class별 round3 전수 재감사 파일을 둔다.
- `issue/`, `remediation/`, `other/` 아래에 각각:
  - `batches/`
  - `manifests/`
  - `merged_annotations.csv`
  - `overlay_annotations.csv`
  - `summary.json`
  - `summary.csv`

### `results/validation`

- 샘플 점검 메모나 검증 노트를 둔다.

## 이름 규칙

- `raw`: 원본 그대로의 입력
- `processed`: 원본에서 직접 파생된 정규화 결과
- `annotations`: 사람이 손댄 라벨 파일
- `working`: 중간 작업용 master
- `full_round3`: 최종 전수 검토 완료본
- `results/.../roundX_*`: 어떤 단계에서 나온 결과인지 드러내는 디렉터리 이름
