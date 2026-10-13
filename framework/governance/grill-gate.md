# Grill Gate

## 왜 / Why

"이거 만들어 줘"로 바로 시작한 프로젝트는 나중에 왜 그렇게 만들었는지 답할 수 없다. Grill Gate는 구현 전에 결과, 문제, 비목표, 성공 기준, 검증 방법, 멈추는 조건을 정한다.

A project that starts from "build me this" cannot later explain why it was built that way. The Grill Gate fixes the outcome, problem, non-goals, success criteria, verification and stop condition before implementation.

## 방식 / Modes

| mode | 언제 / When |
|---|---|
| `grill-me` | 아이디어만 있다. 질문에 답한다. / Only an idea. Answer the questions. |
| `grill-with-docs` | 메모, 자료 폴더가 있다 (`--docs`). 후보 사실을 뽑고 빈 곳만 묻는다. / A folder of notes (`--docs`). Candidate facts are extracted; only the gaps are asked. |
| `grill-from-plan` | 저장소에 기획서(`plan.md`, `prd.md`)와 요구사항(`requirements.md`)이 있다. 답과 요건을 옮겨 적는다. / The repository has a plan (`plan.md`, `prd.md`) and requirements (`requirements.md`). Answers and requirements are copied from them. |

## 필수 항목 / Required answers

outcome, problem, non_goals, features, success, verification, stop.
하나라도 비면 게이트는 `pending`이다. `pending`이면 구현하지 않는다.
If any is empty the gate stays `pending`. No implementation while it is `pending`.

## 산출물 / Outputs

`intake/sources.md`, `intake/grill.md`, `governance/constitution.md`, `requirements/requirements.yaml`, `status/timeline.md`, 그리고 tracker가 비어 있으면 `tracker/tasks.yaml`.
`intake/sources.md`, `intake/grill.md`, `governance/constitution.md`, `requirements/requirements.yaml`, `status/timeline.md`, and `tracker/tasks.yaml` when the tracker is empty.

## 멈추는 조건 / Stop condition

성공 기준이 충족되면 멈춘다. 더 다듬을 것이 보이면 후속 task로 남긴다.
Stop when the success criteria hold. Record anything else as a follow-up task.
