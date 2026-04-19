# SOX404 Sentence Labeling Guideline v1

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

### ISSUE 제외
- 중립적 현황 설명
- remediation 의도만 있는 문장
- 감사인 attestation 언급
- generic definition or framework language
- remediation section intro or status-only sentence
- fragment/header that cannot stand on its own

### REMEDIATION 포함
- remediation action list
- control enhancement
- review 또는 monitoring step
- future fix plan with concrete action

### REMEDIATION 제외
- 막연한 기대효과
- 단순 효과 보고
- 문맥이 없으면 action 대상이 불명확한 문장
- remediation progress/status without a concrete action

## Clarifications From Round 1
- `restatement`, `audit adjustment`, `misstatement risk`, `ineffective control`을 직접 설명하면 기본적으로 `ISSUE`다.
- 다만 `no impact`, `immaterial adjustment only`, `management believes statements were prepared in accordance with GAAP`처럼 결과/효과만 보고하는 문장은 `OTHER + effect`로 둔다.
- `remediation plan is still in process`, `further actions remain ongoing`, `has been remediated`, `testing is not yet complete` 같은 진행상황 문장은 `REMEDIATION`이 아니라 `OTHER + status`다.
- `principally the remediation efforts included`, `in order to improve controls we intend to`, `the material weakness identified specifically resulted in the following`처럼 다음 문장을 여는 lead-in/header 문장은 `OTHER + needs_context=1`로 둔다.
- bullet fragment라도 문장 자체가 구체적 action을 말하면 `REMEDIATION`을 줄 수 있다.
  예: `finalize the system implementation related to sap`
- generic definitions of material weakness or COSO framework text는 회사별 문제 진술이 아니므로 `OTHER + background`다.

## Canonical Examples
### explicit ISSUE
`the material weakness did not result in any identified misstatement to the financial statements, and there were no changes to previously released financial results.`

### explicit REMEDIATION
`the remediation actions include restricting user access of individuals able to make manual journal entries, ensuring the completeness of manual journal entries included in the review, and ensuring accurate and appropriate documentation is retained to support the journal entry.`

### dominant REMEDIATION
`although we plan to complete this remediation process as quickly as possible, the material weakness in our internal control over financial reporting will not be considered remediated until the applicable remedial processes operate for a sufficient period of time.`

### mixed_AB
`although no adjustment was required to our consolidated financial statements, management concluded that there is a reasonable possibility that a material misstatement could occur in consulting revenue and travel and entertainment expenses if the control deficiency was not remediated.`

### needs_context
`to address this issue, management implemented additional review procedures.`

### status vs ISSUE
- `currently, the company maintains disclosure controls and procedures.` -> `OTHER`
- `currently, most of the review remains manual and management could not ensure that all entries were accurate.` -> `ISSUE`

### effect vs REMEDIATION
- `this approach improves the accuracy of the review.` -> `OTHER`
- `management added a secondary review to improve the accuracy of the review.` -> `REMEDIATION`

### effect vs ISSUE
- `the control deficiency resulted in a restatement of previously issued financial statements.` -> `ISSUE`
- `the change in presentation required by the restatement does not impact cash flow or liquidity.` -> `OTHER + effect`

### remediation status vs REMEDIATION
- `our remediation plan is still in process and most of these material weaknesses continued to exist as of year-end.` -> `OTHER + status`
- `we implemented additional review controls and hired experienced accounting personnel.` -> `REMEDIATION`

### lead-in / header
- `principally the remediation efforts included` -> `OTHER + needs_context`
- `the material weakness identified specifically resulted in the following` -> `OTHER + needs_context`

### attestation
`our independent registered public accounting firm has audited our internal control over financial reporting and issued an attestation report.` -> `OTHER + attestation`

## Annotation Notes
- `mixed_AB`와 `needs_context`는 semantic main label과 별개로 기록한다.
- `OTHER`를 `모델이 확신이 없는 상태`와 혼동하지 않는다.
- `note`에는 판정 근거 또는 경계 이유를 짧게 남긴다.
