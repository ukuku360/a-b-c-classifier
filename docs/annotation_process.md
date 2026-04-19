# Annotation Process: From `source_workbook_token404_sample_yh` to `master_annotations_full_round3`

## Overview

이 문서는 원본 파일인 `data/raw/source_workbook_token404_sample_yh.xlsx`에서 출발해 최종 파일인 `data/annotations/master_annotations_full_round3.csv`가 만들어지기까지의 전체 과정을 단계별로 설명한다.

핵심은 다음과 같다.

- 원본 엑셀의 기존 컬럼(`impact`, `remediation`, `attestation`)을 최종 정답으로 그대로 사용하지 않았다.
- 먼저 문장 단위 canonical table을 만들고, 소규모 seed 라벨링을 수행했다.
- 그 뒤 경계 사례를 재검토하고, 모델 기반 active learning으로 정보량이 큰 문장을 추가 라벨링했다.
- round2에서 기준을 정교화한 뒤 working master를 만들었다.
- 마지막 round3에서는 전체 1,636문장을 class별로 전수 재감사해 full master를 완성했다.

즉, 최종 파일은 단순한 자동 변환물이 아니라, `표준화 -> 초기 수동 라벨링 -> 기준 점검 -> active learning -> 추가 adjudication -> 전수 재감사 -> 최종 병합`을 거친 결과물이다.

## Final Output

- 최종 파일: `data/annotations/master_annotations_full_round3.csv`
- 최종 커버리지: 1,636개 문장 전체
- 최종 label 분포:
  - `OTHER`: 651
  - `ISSUE`: 515
  - `REMEDIATION`: 470

이 파일은 현재 기준에서 가장 완성도가 높은 full-coverage master annotation 파일이다.

## Step 1. 원본 엑셀을 canonical sentence table로 정리

### 목적

원본 `data/raw/source_workbook_token404_sample_yh.xlsx`는 문장 데이터와 메타데이터, 그리고 기존 힌트 컬럼이 함께 섞여 있는 원시 자료다. 이 상태로는 어노테이션, 모델링, 추적 관리가 어렵기 때문에 먼저 모든 후속 작업의 기준이 되는 canonical sentence table이 필요했다.

### 입력

- 원본 파일: `data/raw/source_workbook_token404_sample_yh.xlsx`
- 원본 크기: 1,636행, 48개 컬럼

### 수행한 작업

- 각 행에 고유한 `row_id`를 부여했다.
- `text_key`를 문서 ID 역할의 `doc_id`로 정리했다.
- `seq`를 문장 순서를 나타내는 `sent_id`로 정리했다.
- 원문 문장(`text_raw`)과 정규화 문장(`text_norm`)을 분리했다.
- 문맥 확인용으로 직전 문장(`prev_text_raw`, `prev_text_norm`)을 추가했다.
- 문장 길이, 짧은 문장 여부, 문맥 필요 가능성(`heuristic_needs_context`) 같은 보조 변수를 만들었다.
- 기존 `impact`, `remediation`, `attestation` 컬럼을 이용해 임시 proxy label을 만들었다.

### 중요한 해석

이 단계의 proxy label은 어디까지나 출발용 힌트였다.  
즉, "기존 컬럼 = 최종 정답"이 아니라 "초기 샘플링과 우선순위 선정을 돕는 약한 신호"로만 사용되었다.

### 산출물

- `data/processed/sentences_canonical.csv`

### 결과

- 전체 1,636개 문장이 canonical form으로 정리되었다.
- 이후 모든 라벨 파일은 `row_id`를 기준으로 이 파일과 연결된다.

## Step 2. 문서 단위 split 고정

### 목적

모델 평가 시 같은 문서의 문장이 train과 test에 동시에 들어가면 leakage가 생긴다. 이를 막기 위해 문장 단위가 아니라 문서 단위로 split을 고정했다.

### 수행한 작업

- 문서별로 기존 legacy signal 분포를 요약했다.
- 이를 바탕으로 문서 단위 `trainval` / `test` split을 만들었다.
- 가능하면 stratified split을 사용하고, 불가능하면 fallback 방식으로 test 문서를 뽑았다.

### 산출물

- `data/processed/doc_splits_fixed.csv`

### 결과

- 전체 문서 100개 중:
  - `trainval`: 80개
  - `test`: 20개

이 split은 이후 pilot, round2, round3 과정에서 일관되게 재사용되었다.

## Step 3. 초기 seed 200개 샘플링

### 목적

전체 1,636문장을 처음부터 전부 수동 라벨링하지 않고, 먼저 작지만 균형 잡힌 초기 gold seed를 만드는 것이 목적이었다.

### 수행한 작업

기존 legacy hint를 기반으로 여러 유형을 대표하도록 샘플을 뽑았다.

- `legacy_issue_only`: 60개
- `legacy_remediation_only`: 60개
- `legacy_issue_and_remediation`: 30개
- `legacy_attestation`: 10개
- `legacy_background`: 10개
- `legacy_negative`: 30개

총 200개를 seed로 구성했다.

### 중요한 해석

여기서도 기존 legacy hint는 "정답 복사"가 아니라 "균형 잡힌 seed 구성을 위한 샘플링 기준"으로만 사용되었다.

### 산출물

- `data/annotations/seed_annotations_round1.csv`
- `data/annotations/boundary_relabel_queue_round1.csv`
- `data/processed/pilot_dataset_summary.json`

### 결과

`data/processed/pilot_dataset_summary.json` 기준:

- 전체 문장 수: 1,636
- 전체 문서 수: 100
- seed 문장 수: 200
- boundary case 후보 수: 50

seed sampling 분포:

- `legacy_issue_only`: 60
- `legacy_remediation_only`: 60
- `legacy_issue_and_remediation`: 30
- `legacy_negative`: 30
- `legacy_attestation`: 10
- `legacy_background`: 10

현재 `seed_annotations_round1.csv`에는 round1 수동 라벨이 반영되어 있으며, 실제 분포는:

- `ISSUE`: 101
- `OTHER`: 50
- `REMEDIATION`: 49

즉, 초기 human labeling 결과는 원본 proxy 분포와 꽤 달랐고, 특히 실제 `ISSUE` 비중이 더 높게 나타났다.

## Step 4. 경계 사례 50개 blind re-label

### 목적

초기 라벨링에서 가장 위험한 부분은 애매한 문장이다.  
따라서 seed 200개를 한 번 라벨링하는 데서 끝내지 않고, 경계 사례 50개를 따로 뽑아 blind re-label을 수행해 기준의 흔들리는 지점을 찾고자 했다.

### 경계 사례 선정 기준

다음 유형이 우선 포함되었다.

- `mixed_AB` 가능성이 높은 문장
- `needs_context` 가능성이 높은 문장
- opinion/attestation 관련 문장
- remediation header 근처 문장
- 짧은 fragment 문장

### 수행한 작업

- seed 200개 중 boundary priority 50개를 선정했다.
- 이 50개에 대해 blind pass를 수행했다.
- 1차 라벨과 2차 라벨을 비교해 어디서 기준이 흔들리는지 확인했다.

### 산출물

- `data/annotations/boundary_relabel_queue_round1.csv`
- `results/annotation_quality/round1_boundary_review/boundary_disagreements.csv`
- `results/annotation_quality/round1_boundary_review/boundary_disagreement_summary.json`

### 결과

`boundary_disagreement_summary.json` 기준:

- boundary rows: 50
- disagreement rows: 12
- disagreement rate: 24%

불일치 방향:

- `ISSUE -> OTHER`: 11
- `OTHER -> ISSUE`: 1

### 의미

이 결과는 초기 기준에서 `ISSUE`를 과도하게 넓게 잡는 경향이 있었다는 신호다.  
특히 restatement 결과 보고, effect-only 문장, status 문장, fragment, standalone 의미가 약한 문장들이 `ISSUE`처럼 보이지만 실제로는 `OTHER`로 가야 하는 경우가 많다는 점이 드러났다.

이 단계는 이후 guideline refinement의 중요한 근거가 되었다.

## Step 5. round1 seed로 첫 pilot 모델 학습

### 목적

이미 사람이 본 200개 seed만으로도 1차 분류기를 만들 수 있다.  
이 분류기를 사용해 "다음에 사람이 보면 가장 도움이 되는 문장"을 효율적으로 고르기 위한 준비 단계다.

### 수행한 작업

세 가지 모델 조합을 비교했다.

- `centroid_e5`
- `e5_logreg`
- `bge_svm`

이들은 fixed doc split 위에서 비교되었고, 최종 winner를 선정했다.

### 산출물

- `results/model_runs/pilot_round1_seed/model_comparison.csv`
- `results/model_runs/pilot_round1_seed/run_summary.json`
- `results/model_runs/pilot_round1_seed/winner_predictions.csv`
- `results/model_runs/pilot_round1_seed/winner_embeddings.npy`
- `results/model_runs/pilot_round1_seed/review_queue_top50.csv`

### 결과

`results/model_runs/pilot_round1_seed/run_summary.json` 기준:

- winner: `e5_logreg`
- test macro F1: `0.8946368770930174`
- test review rate: `0.25`
- auto precision:
  - `ISSUE`: `1.0`
  - `REMEDIATION`: `0.8333333333333334`

### 의미

이 단계에서 모델은 최종 판정기를 만드는 것이 아니라, 다음 라벨링 라운드에서 어떤 문장을 우선 봐야 할지 정하는 "우선순위 도구"로 쓰이기 시작했다.

## Step 6. active learning으로 round2용 100개 선정

### 목적

추가 라벨링 비용을 가장 효율적으로 쓰기 위해, 아직 사람이 보지 않은 문장 중 정보량이 큰 100개를 뽑는 것이 목적이다.

### 수행한 작업

winner model의 전체 예측 결과를 바탕으로 100개를 네 가지 방식으로 구성했다.

- `margin`: 50개
  - 모델이 가장 헷갈려한 문장
- `disagreement`: 20개
  - winner model과 alternate model이 서로 다르게 본 문장
- `diversity`: 20개
  - embedding 공간에서 다양한 유형을 대표하도록 뽑은 문장
- `random`: 10개
  - 탐색 목적의 무작위 샘플

### 산출물

- `results/model_runs/pilot_round1_seed/active_learning_batch_round1.csv`

### 결과

100개 batch의 분포:

- `selection_reason=margin`: 50
- `selection_reason=disagreement`: 20
- `selection_reason=diversity`: 20
- `selection_reason=random`: 10

즉, round2는 임의의 100개를 본 것이 아니라, 정보량이 높고 기준을 흔들 수 있는 100개를 의도적으로 골라 본 것이다.

## Step 7. round2를 Stage A / Blind Pass / Stage B로 분리

### 목적

round2의 목적은 단순한 추가 100개 라벨링이 아니었다.  
오히려 "어디서 판단이 흔들리는지"를 구조적으로 확인하고, 그 결과를 반영해 guideline을 더 정교화하는 것이 핵심이었다.

### 수행한 작업

active learning 100개를 세 갈래로 나눴다.

1. `Stage A` 50개
   - disagreement와 high-uncertainty 사례 중심
2. `Stage A Blind Pass 2` 30개
   - Stage A 일부를 blind re-check
3. `Stage B` 50개
   - Stage A에서 나온 쟁점을 반영해 더 정교한 기준(`guideline_v1.1`)으로 판정

### 산출물

- `data/annotations/round2_stage_a_annotations.csv`
- `data/annotations/round2_stage_a_blind_review.csv`
- `data/annotations/round2_stage_b_annotations.csv`
- `results/annotation_quality/round2_adjudication/stage_a_double_check_comparison.csv`
- `results/annotation_quality/round2_adjudication/round2_annotation_summary.json`

### 결과

`round2_annotation_summary.json` 기준:

- stage A rows: 50
- double check rows: 30
- double check disagreement rows: 6
- double check disagreement rate: 20%
- stage B rows: 50
- round2 final rows: 100

double-check disagreement bucket:

- `REMEDIATION_vs_OTHER_intro_status`: 2
- `ISSUE_vs_OTHER_effect_status`: 2
- `true_needs_context`: 2

### 의미

round2에서 가장 많이 흔들린 지점은 다음 세 가지였다.

- 실제 action인지, 아니면 action list를 여는 intro/status 문장인지
- 실제 issue 진술인지, 아니면 effect/status 보고인지
- standalone 의미가 부족해서 `needs_context`로 처리해야 하는지

즉, round2는 라벨 수를 늘린 것 이상으로 "기준을 sharpening"한 단계였다.

## Step 8. guideline v1에서 guideline v1.1로 기준 정교화

### 목적

round1과 round2에서 드러난 혼동 포인트를 규칙 수준에서 정리해, 이후 large-scale 재감사에서 같은 흔들림이 반복되지 않게 하는 것이 목적이었다.

### 관련 문서

- `docs/annotation_guidelines_round1.md`
- `docs/annotation_guidelines_round2.md`

### round2 이후 더 분명해진 핵심 기준

- 문장 안에 구체적 action이 있으면 `REMEDIATION`
- weakness, control gap, misstatement risk를 직접 진술하면 `ISSUE`
- 문제와 해결이 동등하게 섞이면 `OTHER + mixed_AB=1`
- standalone 의미가 부족하면 `OTHER + needs_context=1`
- attestation/auditor report 문장은 `OTHER + attestation`
- 결과 보고, status, effect-only 문장은 `OTHER`

### 특히 중요해진 구분

- `ISSUE vs OTHER`
  - restatement 자체, material misstatement risk, ineffective control은 `ISSUE`
  - "adjustment was recorded", "fairly present", "no impact" 같은 결과 보고는 `OTHER`

- `REMEDIATION vs OTHER`
  - `implemented`, `hired`, `instituted`, `added review controls` 같은 구체적 행동은 `REMEDIATION`
  - `the following actions`, `as follows`, `remediation plan`, `has been remediated`, `ongoing`, `not yet tested`는 `OTHER`

### 의미

이 guideline 정교화는 최종 round3 재감사의 질을 결정한 핵심 기반이었다.

## Step 9. round2 adjudication 완료 후 100개 확정

### 목적

round2의 100개를 blind double-check와 guideline refinement를 반영해 최종 확정하고, round1 seed 200개와 합쳐 더 강한 working master를 만드는 단계다.

### 수행한 작업

- Stage A pass1과 blind pass2 차이를 비교했다.
- 차이가 나는 경우 adjudication을 통해 최종 라벨을 정했다.
- Stage B의 refined guideline 판정을 포함해 100개를 최종 확정했다.

### 산출물

- `data/annotations/round2_adjudicated_annotations.csv`
- `results/annotation_quality/round2_adjudication/round2_annotation_summary.json`

### 결과

`round2_adjudicated_annotations.csv` 기준 최종 분포:

- `OTHER`: 44
- `ISSUE`: 32
- `REMEDIATION`: 24

flag counts:

- `mixed_AB`: 1
- `needs_context`: 12

### 의미

이 100개는 단순한 추가 데이터가 아니라, 가장 헷갈리는 문장들을 정제된 기준으로 확정한 고가치 라벨 세트였다.

## Step 10. 300개 working master 완성

### 목적

round1의 200개와 round2의 최종 100개를 합쳐, 다음 모델 학습과 full-corpus 재감사의 기준이 되는 working master를 만드는 단계다.

### 수행한 작업

- seed 200개를 기본 master로 삼았다.
- round2 adjudicated final 100개를 합쳤다.
- 동일 `row_id` 기준으로 deduplicate해 master를 정리했다.

### 산출물

- `data/annotations/master_annotations_working.csv`

### 결과

현재 `master_annotations_working.csv`는 300행이며 분포는:

- `ISSUE`: 133
- `OTHER`: 94
- `REMEDIATION`: 73

구성:

- `guideline_v1_round1`: 200개
- `guideline_v1_1_round2_final`: 100개

### 의미

이 파일은 full final master는 아니다.  
이 시점의 역할은 "정교화된 partial gold set"이다.  
즉, 전체 1,636개를 다 보지는 않았지만, 충분히 신뢰할 만한 300개를 기반으로 다음 단계의 모델과 재감사를 이끌 수 있는 상태가 된 것이다.

## Step 11. 300개 master로 다시 모델 학습

### 목적

round2까지 반영된 300개 master를 사용해 더 나은 전체 예측을 만들고, 이를 round3 전수 재감사의 출발점으로 삼기 위함이다.

### 수행한 작업

- `master_annotations_working.csv`를 기준으로 baseline 모델을 다시 학습했다.
- 전체 1,636문장에 대한 새로운 winner prediction을 만들었다.
- class별 predicted pool을 확보했다.

### 산출물

- `results/model_runs/pilot_round2_master/model_comparison.csv`
- `results/model_runs/pilot_round2_master/run_summary.json`
- `results/model_runs/pilot_round2_master/winner_predictions.csv`
- `results/model_runs/pilot_round2_master/winner_embeddings.npy`
- `results/model_runs/pilot_round2_master/active_learning_batch_round2.csv`

### 결과

`results/model_runs/pilot_round2_master/run_summary.json` 기준:

- winner: `e5_logreg`
- test macro F1: `0.8883861744176268`
- test review rate: `0.5`
- auto precision:
  - `ISSUE`: `0.9583333333333334`
  - `REMEDIATION`: `1.0`

### 의미

이 단계의 모델도 최종 판정기가 아니라, 전체 1,636개를 재감사하기 좋게 class별로 정리해 주는 도구였다.

## Step 12. round3에서 class별 전수 재감사 준비

### 목적

이제 목표는 부분 master를 full master로 바꾸는 것이다.  
따라서 모델 예측 결과를 그대로 채택하는 것이 아니라, 전체 1,636문장을 세 개의 predicted class pool로 나눈 뒤 전부 다시 감사하는 구조를 만들었다.

### 수행한 작업

winner prediction 기준으로 전체를 세 class pool로 분리했다.

- predicted `ISSUE`: 619개
- predicted `REMEDIATION`: 552개
- predicted `OTHER`: 465개

이 세 pool 각각을 별도의 재감사 batch로 나누었다.

### 산출물

- `results/round3_reaudit/issue/batches/*.csv`
- `results/round3_reaudit/remediation/batches/*.csv`
- `results/round3_reaudit/other/batches/*.csv`
- 각 폴더의 `manifests/batch_manifest.csv`
- 각 폴더의 `manifests/batch_summary.csv`

### batch 수

- `ISSUE` 재감사 batch: 31개
- `REMEDIATION` 재감사 batch: 23개
- `OTHER` 재감사 batch: 22개

### 배치 전략의 차이

- `ISSUE`와 `OTHER`는 문맥 흐름 보존을 위해 doc 단위 pack을 많이 사용했다.
- `REMEDIATION`은 25행 fixed chunk 방식으로 더 균일하게 나눴다.

### 의미

round3는 "추가 샘플링"이 아니라 사실상 full-corpus audit 단계였다.

## Step 13. ISSUE predicted pool 전수 재감사

### 목적

모델이 `ISSUE`로 본 문장 619개를 전부 다시 보고, 진짜 issue인지 아니면 effect/status/background로 `OTHER`가 맞는지 검증하는 단계였다.

### 수행한 작업

- `pred_label == ISSUE`인 619개를 batch로 나눠 재감사했다.
- note, needs_context, mixed_AB를 포함해 annotation schema를 모두 채웠다.
- 특히 `ISSUE -> OTHER` 수정 시에는 note를 남기도록 강하게 검증했다.

### 산출물

- `results/round3_reaudit/issue/merged_annotations.csv`
- `results/round3_reaudit/issue/overlay_annotations.csv`
- `results/round3_reaudit/issue/summary.json`
- `results/round3_reaudit/issue/summary.csv`

### 결과

`issue_reaudit_summary.json` 기준:

- total: 619
- `ISSUE` 유지: 489
- `REMEDIATION`로 수정: 7
- `OTHER`로 수정: 123
- `needs_context`: 46
- `mixed_AB`: 1

### 의미

이 결과는 초기 round1, round2에서 관찰된 것과 같은 방향을 보여준다.  
즉, issue처럼 보이지만 사실은 effect-only, status, background, incomplete lead-in이라 `OTHER`가 더 맞는 문장이 상당수 존재했다.

## Step 14. REMEDIATION predicted pool 전수 재감사

### 목적

모델이 `REMEDIATION`으로 본 552개를 전부 다시 보고, 실제 concrete action인지 아니면 status, intro, effect라서 `OTHER`가 맞는지 확인하는 단계였다.

### 수행한 작업

- `pred_label == REMEDIATION`인 552개를 batch로 나눠 재감사했다.
- concrete action인지, intro/header인지, status-only인지 세밀하게 구분했다.
- 기존 `master_annotations_working.csv`와 겹치는 73개에 대해서는 overlap comparison도 수행했다.

### 산출물

- `results/round3_reaudit/remediation/merged_annotations.csv`
- `results/round3_reaudit/remediation/overlay_annotations.csv`
- `results/round3_reaudit/remediation/summary.json`
- `results/round3_reaudit/remediation/summary.csv`
- `results/round3_reaudit/remediation/master_overlap_comparison.csv`

### 결과

`remediation_reaudit_summary.json` 기준:

- total: 552
- `REMEDIATION` 유지: 412
- `ISSUE`로 수정: 10
- `OTHER`로 수정: 130
- `needs_context`: 70
- `mixed_AB`: 6

기존 master와 겹치는 73개 중:

- 완전 일치: 64
- 불일치: 9

### 의미

remediation pool에서는 특히 `header`, `lead-in`, `generic plan`, `ongoing status`, `not yet remediated until tested` 같은 문장들이 `OTHER`로 많이 이동했다.  
즉, "remediation section 안에 있는 문장"과 "문장 자체가 remediation action인 것"을 엄격히 분리한 결과다.

## Step 15. OTHER predicted pool 전수 재감사

### 목적

모델이 `OTHER`로 본 465개가 정말 background/status/effect/attestation인지, 혹은 놓친 `ISSUE`와 `REMEDIATION`이 숨어 있는지 검증하는 단계였다.

### 수행한 작업

- `pred_label == OTHER`인 465개를 batch로 나눠 전수 재감사했다.
- `c_subtype`을 구체적으로 채웠다.
- `OTHER` 안에서도 `background`, `status`, `effect`, `attestation`, `other`를 세분화했다.

### 산출물

- `results/round3_reaudit/other/merged_annotations.csv`
- `results/round3_reaudit/other/overlay_annotations.csv`
- `results/round3_reaudit/other/summary.json`
- `results/round3_reaudit/other/summary.csv`

### 결과

`other_reaudit_summary.json` 기준:

- total: 465
- `OTHER` 유지: 398
- `ISSUE`로 수정: 16
- `REMEDIATION`로 수정: 51
- `needs_context`: 86
- `mixed_AB`: 0

`OTHER` subtype 분포:

- `background`: 111
- `status`: 116
- `effect`: 34
- `attestation`: 50
- `other`: 154

### 의미

이 단계는 반대로 "모델이 OTHER라고 본 것 중 사실은 issue나 remediation인 것"을 다시 끌어올리는 역할을 했다.  
즉, round3는 특정 클래스만 정리한 것이 아니라 세 클래스 전체를 균형 있게 다시 본 과정이었다.

## Step 16. 세 overlay를 합쳐 최종 full master 생성

### 목적

class별로 따로 수행한 round3 재감사 결과를 하나의 authoritative master로 합치는 마지막 단계다.

### 수행한 작업

세 overlay를 병합하면서 다음을 검증했다.

- 세 overlay의 컬럼 스키마가 동일한지
- 라벨 값과 flag 값이 유효한지
- `annotator`, `label_version`이 비어 있지 않은지
- overlay 사이에 `row_id` 충돌이 없는지
- 최종 병합 결과가 `data/processed/sentences_canonical.csv`의 1,636개 `row_id`를 정확히 모두 덮는지

### 산출물

- `data/annotations/master_annotations_full_round3.csv`

### 결과

병합 결과:

- total rows: 1,636
- 기존 `master_annotations_working.csv`와 overlap: 300
- 새롭게 full coverage로 추가된 rows: 1,336

최종 label 분포:

- `OTHER`: 651
- `ISSUE`: 515
- `REMEDIATION`: 470

### 의미

이 단계에서 비로소 전체 corpus에 대해 누락 없는 final master가 완성되었다.

## Step 17. 기존 300개 master와 최종 round3 master의 관계

### 목적

최종 round3 파일이 기존 `master_annotations_working.csv`를 완전히 뒤엎은 것인지, 아니면 일부 보정한 것인지 이해하는 것이 중요하다.

### 비교 결과

기존 master 300행과 최종 round3 master 300행의 overlap을 비교하면:

- `label_main` 동일: 267
- `label_main` 변경: 33
- `flag_mixed_ab` 변경: 3
- `flag_needs_context` 변경: 14
- `c_subtype` 변경: 183

label 변경 방향:

- `ISSUE -> OTHER`: 22
- `REMEDIATION -> OTHER`: 8
- `OTHER -> REMEDIATION`: 2
- `OTHER -> ISSUE`: 1

### 의미

최종 round3는 기존 master를 폐기한 것이 아니라, 주로 다음 유형을 더 엄격하게 정리한 것이다.

- effect-only 문장
- status-only 문장
- lead-in / header 문장
- fragment / incomplete standalone 문장

즉, 전체적인 방향은 "과하게 `ISSUE` 또는 `REMEDIATION`로 잡혔던 문장을 더 신중하게 `OTHER`로 정리"하는 쪽이었다.

## 핵심 파일 흐름 요약

### 원본 및 정규화

- `data/raw/source_workbook_token404_sample_yh.xlsx`
- `data/processed/sentences_canonical.csv`
- `data/processed/doc_splits_fixed.csv`

### 초기 seed와 round1

- `data/annotations/seed_annotations_round1.csv`
- `data/annotations/boundary_relabel_queue_round1.csv`
- `results/annotation_quality/round1_boundary_review/boundary_disagreements.csv`

### pilot 및 active learning

- `results/model_runs/pilot_round1_seed/winner_predictions.csv`
- `results/model_runs/pilot_round1_seed/active_learning_batch_round1.csv`

### round2

- `data/annotations/round2_stage_a_annotations.csv`
- `data/annotations/round2_stage_a_blind_review.csv`
- `data/annotations/round2_stage_b_annotations.csv`
- `data/annotations/round2_adjudicated_annotations.csv`
- `data/annotations/master_annotations_working.csv`

### round3

- `results/model_runs/pilot_round2_master/winner_predictions.csv`
- `results/round3_reaudit/issue/overlay_annotations.csv`
- `results/round3_reaudit/remediation/overlay_annotations.csv`
- `results/round3_reaudit/other/overlay_annotations.csv`
- `data/annotations/master_annotations_full_round3.csv`

## 한 줄 요약

`master_annotations_full_round3.csv`는 `data/raw/source_workbook_token404_sample_yh.xlsx`의 기존 힌트를 그대로 옮긴 파일이 아니라, 문장 표준화, seed 수동 라벨링, 경계 사례 blind 재검토, active learning 기반 추가 라벨링, round2 adjudication, 그리고 round3 전체 1,636문장 전수 재감사를 거쳐 완성된 최종 full master annotation 파일이다.
