# Approval Policy / 승인 정책

**AI Executes, Human Governs.** AI는 실행하고, 사람은 방향, 우선순위, 범위, 주요 변경을 정한다.
**AI Executes, Human Governs.** The AI executes; a person decides direction, priority, scope and major changes.

## 1. 사람 승인이 필요한 변경 / Changes that need a person

아래 중 하나에 해당하면 에이전트는 실행하지 않고 멈춘다.
If any of these applies, the agent stops instead of executing.

| # | 변경 / Change |
|---|---|
| 1 | 미션, 범위 / mission, scope |
| 2 | 요구사항 삭제, 핵심 요구사항 수정 / deleting a requirement, editing a core requirement |
| 3 | 구조, 데이터 모델, 외부 인터페이스 / architecture, data model, external interface |
| 4 | 보안, 개인정보 처리 / security, personal data handling |
| 5 | 비용, 일정에 큰 영향 / large cost or schedule impact |
| 6 | 릴리스, push, 배포 / release, push, deploy |
| 7 | CR 승인 / approving a CR |

## 2. 멈췄을 때 / When stopped

1. 멈춘다. 구현, 수정, 삭제를 시작하지 않는다. / Stop. Do not start implementing, editing or deleting.
2. 영향 분석을 보여 준다: 영향받는 요구사항, 구성 요소, 데이터, 테스트, 위험, 몇 번 항목인지. / Show an impact analysis: affected requirements, components, data, tests, risks, and which item above.
3. 선택지를 주고 묻는다. 승인 없이 할 수 있는 작은 범위가 있으면 같이 제안한다. / Offer options and ask. Suggest a smaller scope that needs no approval, if one exists.
4. 승인을 받으면 근거를 CR이나 ADR에 남긴다. / After approval, record it in a CR or an ADR.
5. 승인을 못 받으면 task를 `blocked`로 두고 이유를 적는다. / Without approval, leave the task `blocked` with the reason.

"일단 해 보고 나중에 묻는다"는 금지다.
"Do it first, ask later" is forbidden.
