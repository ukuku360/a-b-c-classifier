# `master_annotations_round3_reaudit.csv` 랜덤 표본 검정

## 방법

- 원본 라벨 파일: `/Users/nmduk/PROJECTS/A:B:C Classifier/data/master_annotations_round3_reaudit.csv`
- 문장 원문 조인 파일: `/Users/nmduk/PROJECTS/A:B:C Classifier/data/sentences.csv`
- 조인 키: `row_id`
- 표본추출 방식: `label_main`별 무작위 10개씩, 고정 시드 `20260419`
- 검정 기준:
  - `ISSUE`: 통제 실패, 중대한 취약점, 비효과성, 또는 그 직접적 결과를 진술
  - `REMEDIATION`: 구체적인 개선 조치나 시정 활동을 진술
  - `OTHER`: 배경, 정의, 감사인 attestation, 상태 보고, list intro, 문장 파편

## 요약

| 분류 | 표본 수 | 라벨 일치 | 재분류 필요 |
|---|---:|---:|---:|
| ISSUE | 10 | 10 | 0 |
| REMEDIATION | 10 | 9 | 1 |
| OTHER | 10 | 10 | 0 |

재분류 후보는 `row_id 915` 1건입니다. 현재 라벨은 `REMEDIATION`이지만, 문장 자체는 구체 조치가 아니라 "추가 변화 없음"이라는 상태 공시이므로 `OTHER`가 더 타당해 보입니다.

## ISSUE 표본 10건

1. `row_id 168`
원문: "specifically, the company lacks sufficient resources to have an effective control function that involves assessments of risk at an appropriate level of detail, controls designed with the right level of precision and responsive to those risks, and control implementation, including evidence of operating effectiveness."

한글 해석: "구체적으로, 회사는 적절한 수준의 세부 위험평가, 그 위험에 대응할 수 있을 정도의 정밀도로 설계된 통제, 그리고 운영효과성의 증거를 포함한 통제 실행을 수행할 수 있는 효과적인 통제 기능을 갖추기에 충분한 자원이 부족하다."

검정: 자원 부족으로 인해 효과적인 통제 기능이 없다고 직접 진술한다. 결함의 원인과 부족한 통제 요소를 설명하는 문장이므로 `ISSUE`가 맞다.

판정: 맞음

2. `row_id 315`
원문: "specifically, the company lacked . adequate policies and procedures to ensure the timely reporting of asserted cargo claims by personnel responsible for the daily management of those claims, and . adequate management supervision and review of the reserve for cargo claims."

한글 해석: "구체적으로, 회사는 (1) 해당 클레임을 일상적으로 관리하는 인력이 제기된 화물 클레임을 적시에 보고하도록 보장하는 적절한 정책과 절차, 그리고 (2) 화물 클레임 충당부채에 대한 적절한 경영진 감독과 검토가 부족했다."

검정: 정책과 절차의 부재, 경영진 감독 부족을 직접 지적한다. 개선 행동이 아니라 통제 결함의 진술이므로 `ISSUE`가 타당하다.

판정: 맞음

3. `row_id 280`
원문: "based on the trustee’s evaluation under the coso criteria, the trustee identified a deficiency in its internal control over financial reporting that it considers to represent a “material weakness.”"

한글 해석: "COSO 기준에 따른 수탁자의 평가에 근거해, 수탁자는 내부회계관리에서 '중대한 취약점(material weakness)'에 해당한다고 판단되는 결함을 식별했다."

검정: material weakness를 명시적으로 식별한 문장이다. 문제 인식 그 자체이므로 `ISSUE`가 맞다.

판정: 맞음

4. `row_id 777`
원문: "december 31, 2014, our disclosure controls and procedures were not effective."

한글 해석: "2014년 12월 31일 현재, 우리의 공시통제 및 절차는 효과적이지 않았다."

검정: 통제가 비효과적이었다고 직접 선언한다. 개선 활동이나 배경 설명이 아니므로 `ISSUE`가 맞다.

판정: 맞음

5. `row_id 125`
원문: "the company did not design and maintain adequate controls over the inventory process, to ensure that accounting determinations related to inventory were appropriately considered and recorded in accordance with gaap, that the inventory balance was complete and accurate and that disclosures related to the inventory balance were appropriately reflected within the financial statements."

한글 해석: "회사는 재고 관련 회계 판단이 GAAP에 따라 적절히 고려되고 기록되며, 재고 잔액이 완전하고 정확하고, 재고 관련 공시가 재무제표에 적절히 반영되도록 보장하는 재고 프로세스 통제를 적절히 설계하고 유지하지 못했다."

검정: 재고 프로세스 통제를 적절히 설계·유지하지 못했다고 명시한다. 전형적인 통제 실패 진술이므로 `ISSUE`다.

판정: 맞음

6. `row_id 255`
원문: "as described in item 4 of part i of our quarterly report on form 10-q for the quarter ended september 30, 2007, management identified the following material weaknesses that existed as of september 30, 2007."

한글 해석: "2007년 9월 30일 종료 분기에 대한 10-Q Part I Item 4에서 설명한 바와 같이, 경영진은 2007년 9월 30일 현재 존재하던 다음의 중대한 취약점을 식별했다."

검정: 구체 항목의 서두이긴 하지만, 그 자체로 material weaknesses의 존재를 직접 진술한다. 리스트 intro라 해도 문제의 존재를 명시하므로 `ISSUE`로 보는 것이 맞다.

판정: 맞음

7. `row_id 813`
원문: "we did not maintain effective controls related to the accuracy of revenue recorded at a business unit within our brooks life sciences segment."

한글 해석: "우리는 Brooks Life Sciences 부문의 한 사업단위에서 기록된 매출의 정확성과 관련된 효과적인 통제를 유지하지 못했다."

검정: 매출 정확성과 관련된 효과적 통제를 유지하지 못했다고 직접 말한다. 명백한 통제 실패이므로 `ISSUE`가 맞다.

판정: 맞음

8. `row_id 689`
원문: "monitoring – as a result of the material weaknesses described above, we have not completed the design and operation of certain monitoring activities to ascertain whether the components of internal control are present and functioning."

한글 해석: "모니터링 - 위에서 설명한 중대한 취약점의 결과로, 우리는 내부통제의 구성요소가 존재하고 기능하는지를 확인하기 위한 일부 모니터링 활동의 설계와 운영을 완료하지 못했다."

검정: 모니터링 활동의 설계·운영 미완료를 직접 기술한다. 이는 remediation 계획이 아니라 현재 남아 있는 결함 설명이므로 `ISSUE`다.

판정: 맞음

9. `row_id 1353`
원문: "these practices could result in unauthorized or undocumented purchases."

한글 해석: "이러한 관행은 승인되지 않았거나 문서화되지 않은 구매를 초래할 수 있다."

검정: 앞 문장의 통제 미준수 관행이 낳는 부정적 결과를 진술한다. 스키마상 `effect` subtype의 문제 결과 문장으로 볼 수 있어 `ISSUE`가 타당하다.

판정: 맞음

10. `row_id 1308`
원문: "in addition, a third material weakness was identified in connection with the company’s implementation of fasb’s accounting standard, “financial instruments-credit losses (topic 326), measurement of credit losses on financial instruments,” which replaced the “incurred loss” model for recognizing credit losses with an “expected loss” model referred to as the current expected credit loss (“cecl”) model."

한글 해석: "또한, 회사의 FASB 회계기준 '금융상품-신용손실(Topic 326)' 도입과 관련하여 세 번째 중대한 취약점이 식별되었는데, 이 기준은 신용손실 인식에 있어 기존의 '발생손실' 모델을 현재기대신용손실(CECL)이라는 '기대손실' 모델로 대체했다."

검정: 세 번째 material weakness가 식별되었다고 직접 밝힌다. 배경 설명이 조금 섞여 있어도 핵심 서술은 문제 식별이므로 `ISSUE`가 맞다.

판정: 맞음

## REMEDIATION 표본 10건

1. `row_id 1579`
원문: "the company enhanced the onboarding training provided to newly hired salespeople to emphasize the importance of compliance with the various regulations specific to the life sciences industry to which the company is subject."

한글 해석: "회사는 신규 채용 영업사원에게 제공하는 입문 교육을 강화하여, 회사가 적용받는 생명과학 산업 특유의 각종 규제를 준수하는 것의 중요성을 강조했다."

검정: 교육을 강화했다는 구체적인 시정 조치가 명시되어 있다. 따라서 `REMEDIATION`이 맞다.

판정: 맞음

2. `row_id 644`
원문: "implementing controls over calculations associated with non-routine transactions at a more precise level of operation."

한글 해석: "비경상적 거래와 관련된 계산에 대해 더 정밀한 운영 수준의 통제를 도입하고 있다."

검정: 통제 도입이라는 구체 조치가 드러난다. 문장 형태는 파편적이지만 remediation bullet의 본문으로 기능하므로 `REMEDIATION`이 타당하다.

판정: 맞음

3. `row_id 798`
원문: "evidence the performance of each management review activity prescribed in the control; and ."

한글 해석: "통제에서 규정한 각 경영진 검토 활동의 수행을 증빙한다."

검정: 수행 증빙을 남기도록 하는 구체적 개선 행동이다. 체크리스트형 파편 문장이지만 의미상 분명한 remediation action이다.

판정: 맞음

4. `row_id 1296`
원문: "remediation our management has been implementing and continues to implement measures designed to ensure that control deficiencies contributing to the material weaknesses are remediated, including establishing and improving policies, procedures and control activities primarily associated with end-user and privileged access to certain information technology systems that support our financial reporting process."

한글 해석: "시정(remediation)과 관련해, 경영진은 중대한 취약점에 기여한 통제 결함이 시정되도록 하기 위한 조치를 시행해 왔고 계속 시행하고 있으며, 여기에는 재무보고 프로세스를 지원하는 특정 정보기술 시스템의 일반 사용자 및 특권 접근권한과 주로 관련된 정책, 절차, 통제활동의 수립과 개선이 포함된다."

검정: 시행 중인 시정 조치를 구체적으로 서술한다. 정책·절차·통제활동 개선이라는 액션이 분명하므로 `REMEDIATION`이 맞다.

판정: 맞음

5. `row_id 898`
원문: "we have reduced the number of segregation of duties conflicts and continue to evaluate the extent it is necessary to limit access and modify responsibilities of certain personnel, as well as designing and implementing additional user access controls and compensating controls."

한글 해석: "우리는 직무분리 충돌의 수를 줄였고, 특정 인력의 접근 제한과 책임 조정이 어느 정도 필요한지 계속 평가하는 한편, 추가적인 사용자 접근통제와 보완통제를 설계하고 구현하고 있다."

검정: 이미 줄인 조치와 추가 설계·구현 조치가 함께 나온다. 명백한 remediation 진행 상황이므로 `REMEDIATION`이 타당하다.

판정: 맞음

6. `row_id 752`
원문: "with respect to both the refundable fees for club member services and classification of club member intangible asset items above, to remediate the material weaknesses in our internal control over financial reporting, subsequent to year end we have modified our application of accounting principles and improved training at our consolidated subsidiary to ensure application of the correct generally accepted accounting principles to support understanding of those accounting principles."

한글 해석: "위의 클럽 회원 서비스 환불수수료와 클럽 회원 무형자산 항목 분류 모두와 관련하여, 내부회계관리의 중대한 취약점을 시정하기 위해 우리는 연말 이후 회계원칙의 적용을 수정하고 연결 자회사에 대한 교육을 개선하여 올바른 일반적으로 인정된 회계원칙이 적용되고 그 이해가 뒷받침되도록 했다."

검정: 회계원칙 적용 수정과 교육 개선이라는 구체 조치를 명시한다. 전형적인 remediation 문장이다.

판정: 맞음

7. `row_id 623`
원문: "implement a billing, disbursement and stock option accounting system and integrate with sap."

한글 해석: "청구, 지출, 스톡옵션 회계 시스템을 도입하고 이를 SAP와 통합한다."

검정: 시스템 도입 및 통합이라는 명확한 시정 계획이다. `REMEDIATION`이 맞다.

판정: 맞음

8. `row_id 915`
원문: "based on that evaluation, other than the identification of the material weaknesses noted above, no such changes to our internal control over financial reporting occurred during the fourth quarter of the year ended december 31, 2021."

한글 해석: "그 평가에 근거해, 위에서 식별된 중대한 취약점을 제외하면 2021년 12월 31일 종료연도 4분기 동안 내부회계관리에는 그러한 변경이 발생하지 않았다."

검정: 문장 자체는 구체적 시정 조치가 아니라 '해당 분기에 추가적인 변화가 없었다'는 상태 공시다. 바로 앞 문장은 remediation 진행 보고지만, 현재 표본 문장은 no-change disclosure에 가깝다.

판정: 재분류 필요. `REMEDIATION`보다는 `OTHER`가 더 타당

9. `row_id 399`
원문: "designed and implemented controls with regards to excess and obsolete inventory and inventory pricing and purchase arrangements."

한글 해석: "과잉 및 진부화 재고, 재고 가격, 구매 약정과 관련된 통제를 설계하고 구현했다."

검정: 통제를 설계·구현했다는 구체적인 시정 조치다. `REMEDIATION`이 맞다.

판정: 맞음

10. `row_id 1289`
원문: "&#9679;conduct training regarding the design and operation of controls with those responsible for performing and reviewing the process level control activities over revenue, accounts receivable and in transit inventory."

한글 해석: "매출, 매출채권, 운송 중 재고에 대한 프로세스 수준 통제 활동을 수행하고 검토하는 책임자들을 대상으로 통제의 설계와 운영에 관한 교육을 실시한다."

검정: 교육 실시라는 분명한 remediation action이다. `REMEDIATION`이 맞다.

판정: 맞음

## OTHER 표본 10건

1. `row_id 352`
원문: "bdo usa, llp, an independent registered public accounting firm, has audited the effectiveness of our internal control over financial reporting and has issued an attestation report, which contains an adverse opinion, as of july 31, 2018."

한글 해석: "독립 등록 공인회계법인인 BDO USA, LLP가 2018년 7월 31일 현재 우리의 내부회계관리의 효과성을 감사했으며, 부적정 의견(adverse opinion)을 담은 검증보고서를 발행했다."

검정: adverse opinion이 언급되지만, 문장 기능은 문제 자체가 아니라 감사인의 attestation 보고를 설명하는 데 있다. 따라서 `OTHER`가 맞다.

판정: 맞음

2. `row_id 361`
원문: "the company has implemented the following remedial measures designed to address these material weaknesses."

한글 해석: "회사는 이러한 중대한 취약점을 해결하기 위해 다음과 같은 시정 조치를 시행했다."

검정: 언뜻 remediation처럼 보이지만, 이 문장 자체는 구체 조치를 말하지 않고 뒤의 리스트를 소개하는 lead-in이다. sentence-level 분류 기준에서는 `OTHER`가 더 적절하다.

판정: 맞음

3. `row_id 58`
원문: "a “significant deficiency” is a deficiency, or combination of deficiencies, in internal control over financial reporting that is less severe than a material weakness, yet important enough to merit attention by those responsible for oversight of financial reporting."

한글 해석: "'유의적 미비(significant deficiency)'란 내부회계관리의 결함 또는 결함들의 결합으로서, 중대한 취약점보다는 덜 심각하지만 재무보고 감독 책임자의 주의를 기울일 만큼 중요한 것을 말한다."

검정: 회사 고유의 결함이나 개선 행동이 아니라 일반적 정의 문장이다. 따라서 `OTHER`가 맞다.

판정: 맞음

4. `row_id 497`
원문: "there was no change in our internal control over financial reporting that occurred during our fourth quarter of the year ended december 31, 2013 that has materially affected, or is reasonably likely to materially affect our internal control over financial reporting, except as noted above."

한글 해석: "위에서 언급한 사항을 제외하면, 2013년 12월 31일 종료연도 4분기 동안 우리의 내부회계관리에 중대한 영향을 미쳤거나 합리적으로 그럴 가능성이 있는 변화는 없었다."

검정: 변화 없음(no-change)을 공시하는 상태 문장이다. 문제 진술이나 시정 행동이 아니므로 `OTHER`가 타당하다.

판정: 맞음

5. `row_id 158`
원문: "changes in internal control over financial reporting other than the changes described above in “remediation plan and status,” there were no changes during the quarter ended december 31, 2020 in our internal control over financial reporting (as such term is defined in the exchange act) that have materially affected, or are reasonably likely to materially affect, our internal control over financial reporting."

한글 해석: "내부회계관리의 변경 사항: 위 '시정 계획 및 현황'에서 설명한 변경을 제외하면, 2020년 12월 31일 종료 분기 동안 우리의 내부회계관리에는 중대한 영향을 미쳤거나 합리적으로 그럴 가능성이 있는 변화가 없었다."

검정: 이것도 no-change status disclosure다. remediation section 안에 있더라도 문장 자체 기능은 상태 공시이므로 `OTHER`가 맞다.

판정: 맞음

6. `row_id 1541`
원문: "culpepper’s travel expenses concluded that mr."

한글 해석: "컬페퍼의 출장비에 대해, Mr. ...라고 결론지었다."

검정: 문장 분절 오류 또는 OCR 파편으로 보이며, 단독으로는 명확한 문제 진술이나 시정 조치를 담고 있지 않다. 이런 파편 문장은 `OTHER`로 두는 것이 안전하다.

판정: 맞음

7. `row_id 1037`
원문: "actuarial finance and valuation ."

한글 해석: "계리, 재무 및 가치평가."

검정: 완전한 문장이 아니라 항목명 또는 파편이다. 문제나 시정 조치가 직접 진술되지 않으므로 `OTHER`가 적절하다.

판정: 맞음

8. `row_id 950`
원문: "the effectiveness of our internal control over financial reporting as of september 30, 2023, has been audited by forvis, llp, independent registered public accounting firm, as stated in their report which is included herein."

한글 해석: "2023년 9월 30일 현재 우리의 내부회계관리의 효과성은 독립 등록 공인회계법인 Forvis, LLP에 의해 감사되었으며, 그 내용은 본 문서에 포함된 보고서에 기재되어 있다."

검정: 감사인 attestation 보고에 관한 문장이다. 내부통제 문제가 앞문장에 있더라도, 현재 문장 자체는 `OTHER`가 맞다.

판정: 맞음

9. `row_id 982`
원문: "bdo seidman, llp, the independent registered public accounting firm who also audited our consolidated financial statements, has issued an attestation report on the effectiveness of internal control over financial reporting as of december 31, 2007, which is filed herewith. /s/ matthew m."

한글 해석: "연결재무제표도 감사한 독립 등록 공인회계법인 BDO Seidman, LLP가 2007년 12월 31일 현재 내부회계관리의 효과성에 대한 검증보고서를 발행했으며, 그 보고서는 본 문서에 첨부되어 있다. /s/ Matthew M."

검정: attestation report 언급과 서명 블록 일부가 섞인 문장이다. 이 역시 문제나 시정이 아니라 보고서 부속 설명이므로 `OTHER`가 타당하다.

판정: 맞음

10. `row_id 638`
원문: "remediation the company is still considering the full extent of the procedures to implement in order to remediate the three material weaknesses described above, however, the current remediation plan includes."

한글 해석: "시정(remediation): 회사는 위에서 설명한 세 가지 중대한 취약점을 시정하기 위해 도입할 절차의 전체 범위를 아직 검토 중이지만, 현재의 시정 계획에는 다음이 포함된다."

검정: remediation section의 도입 문장일 뿐, 아직 구체적 행동이 나오지 않는다. sentence-level 분류 기준에서는 list intro이므로 `OTHER`가 맞다.

판정: 맞음

## 결론

- 이번 랜덤 표본 30건 기준으로는 `29/30`이 현재 라벨과 일치했다.
- `ISSUE`와 `OTHER`는 표본상 모두 타당했다.
- `REMEDIATION`에서는 `row_id 915` 1건이 재분류 후보였다.
- 특히 `OTHER`에는 attestation, 정의 문장, no-change disclosure, list intro, 문장 파편이 많이 포함되어 있어 `ISSUE/REMEDIATION`과 구분할 때 "구체적인 문제/행동이 현재 문장 안에 직접 들어 있는가"를 기준으로 보는 것이 안정적이다.
