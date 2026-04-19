# SOX404 Sentence Labeling Guideline v1.1

## Goal
- `ISSUE`: 문장의 주된 기능이 weakness, risk, misstatement, ineffective control, financial impact를 설명한다.
- `REMEDIATION`: 문장의 주된 기능이 remediation plan, action, implementation step, control enhancement를 설명한다.
- `OTHER`: 배경, 현황, 효과 설명, attestation 언급, 문장 단독으로는 판단 불가, 또는 문제와 해결이 동등하게 섞여 있다.

기존 `A/B/C` 표기는 각각 `ISSUE/REMEDIATION/OTHER`의 legacy alias로만 취급한다.

## Dominant Label Rules
- action/plan이 중심이면 `REMEDIATION`
- weakness/impact가 중심이면 `ISSUE`
- 문제와 해결이 동등하면 `OTHER + mixed_AB=1`
- 이전 문맥 없이는 해석이 안 되면 `OTHER + needs_context=1`
- attestation 문장은 `OTHER + c_subtype=attestation`

## Included / Excluded
### ISSUE 포함
- ineffective control
- material weakness impact
- misstatement 가능성 또는 실제 misstatement
- financial reporting risk
- unmet need phrasing that still states a control or process gap

### ISSUE 제외
- 중립적 현황 설명
- remediation 의도만 있는 문장
- 감사인 attestation 언급
- generic definition or framework language
- remediation section intro or status-only sentence
- fragment/header that cannot stand on its own as a problem statement

### REMEDIATION 포함
- remediation action list
- control enhancement
- review 또는 monitoring step
- future fix plan with concrete action
- compensating review step or temporary control step when the sentence itself states the action

### REMEDIATION 제외
- 막연한 기대효과
- 단순 효과 보고
- 문맥이 없으면 action 대상이 불명확한 문장
- remediation progress/status without a concrete action
- section header or lead-in that only announces actions below

## Round-1 Rules Kept
- `restatement`, `audit adjustment`, `misstatement risk`, `ineffective control`을 직접 설명하면 기본적으로 `ISSUE`다.
- `no impact`, `immaterial adjustment only`, `management believes statements were prepared in accordance with GAAP`처럼 결과/효과만 보고하는 문장은 `OTHER + effect`로 둔다.
- `remediation plan is still in process`, `further actions remain ongoing`, `has been remediated`, `testing is not yet complete` 같은 진행상황 문장은 `REMEDIATION`이 아니라 `OTHER + status`다.
- bullet fragment라도 문장 자체가 구체적 action을 말하면 `REMEDIATION`을 줄 수 있다.
- generic definitions of material weakness or COSO framework text는 회사별 문제 진술이 아니므로 `OTHER + background`다.

## Round-2 Clarifications
### ISSUE vs OTHER: effect / outcome / status
- 통제 미비의 결과로 발생한 `restatement`, `material adjustment`, `misstatement risk`, `controls were not effective`는 `ISSUE`다.
- 이미 기록된 조정의 처리 결과, “fairly present”, “no impact”, “adjustment was recorded prior to issuance”, “report appears below”처럼 결과나 공시 상태만 설명하면 `OTHER`다.
- `the company identified material weaknesses ... described below`처럼 아래 설명을 여는 문장이라도 주된 행위가 문제 인식 자체면 `ISSUE`를 유지한다.

### REMEDIATION vs OTHER: intro / header / status
- `we implemented`, `hired`, `instituted`, `developed`, `revoked access`, `added review controls`처럼 문장 안에 구체적 행동이 있으면 `REMEDIATION`이다.
- `the following actions`, `remediation plan`, `efforts included`, `preliminary steps`, `as follows`처럼 아래 리스트를 여는 문장은 `OTHER + needs_context=1`이다.
- `we have taken steps`, `continues to remediate`, `remains ongoing`, `will not be considered remediated until tested`, `management expects the plan to extend`처럼 진척이나 상태만 보고하면 `OTHER + status`다.

### needs_context
- 아래 중 하나면 기본적으로 `OTHER + needs_context=1` 후보로 본다.
  - `as follows`, `the following`, `included`, `preliminary steps`, `described above/below`
  - 단독 fragment라서 action/object가 잘린 경우
  - 지시어/연결어가 강하지만 standalone 의미가 부족한 경우
- 다만 fragment여도 문장 자체가 명백한 weakness이면 `ISSUE`, 명백한 action이면 `REMEDIATION`을 줄 수 있다.

### attestation
- auditor report, attestation report, unqualified audit report, report appears elsewhere/how appears below는 계속 `OTHER + attestation` 또는 `OTHER + background`로 둔다.
- `not effective`라는 표현이 있어도 auditor report나 management report 내용을 전달하는 문장이라면 우선 `OTHER`를 검토한다.

## Canonical Examples
### explicit ISSUE
`the control deficiency resulted in a restatement of previously issued financial statements.`

### explicit REMEDIATION
`management added a secondary review to improve the accuracy of the review.`

### dominant REMEDIATION
`management developed a regular cadence for reporting the results of control testing to the board of directors.`

### mixed_AB
`the company lacked sufficient accounting personnel and hired additional experienced personnel to remediate that weakness.`

### needs_context
`we have taken, or will take, the following actions.`

### effect-only OTHER
`this adjustment was recorded prior to the issuance of the company’s consolidated financial statements.`

### remediation status OTHER
`the remediation efforts in process or expected to be implemented include the following.`

### attestation OTHER
`we also received an unqualified audit report from our independent registered public accounting firm on those consolidated financial statements.`

## Annotation Notes
- `mixed_AB`와 `needs_context`는 semantic main label과 별개로 기록한다.
- `OTHER`를 `모델이 확신이 없는 상태`와 혼동하지 않는다.
- `note`에는 판정 근거 또는 경계 이유를 짧게 남긴다.
- `mixed_AB=1` 또는 `needs_context=1`이면 `note`를 반드시 남긴다.
