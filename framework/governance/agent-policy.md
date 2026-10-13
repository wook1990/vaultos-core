# Agent Policy / 에이전트 정책

## 하지 않는 것 / Never

1. 요구사항을 말없이 바꾼다. / Change a requirement silently.
2. constitution을 고친다. / Edit the constitution.
3. ADR 없이 구조를 바꾼다. / Change structure without an ADR.
4. 범위를 조용히 넓힌다. / Widen the scope quietly.
5. 요구사항 없는 기능을 넣는다. / Add a feature without a requirement.
6. evidence 없이 done으로 바꾼다. / Mark a task done without evidence.
7. 변경 이유를 지운다. / Delete the reason for a change.
8. 과거 결정과 현재 상태를 섞는다. / Mix past decisions with the current state.
9. 실패를 성공으로 적는다. / Report a failure as a success.
10. 비밀값을 볼트, 저장소, remote URL에 쓴다. / Write a secret into the vault, the repository or a remote URL.

## 보고 / Reporting

사람에게 올리는 보고는 이 질문에 답한다.
A report to a person answers these questions.

```
1. What changed?            무엇이 바뀌었나
2. Why?                     왜 바꿨나
3. What is affected?        무엇에 영향이 있나
4. Is approval required?    승인이 필요한가
5. What was implemented?    무엇을 구현했나
6. What was verified?       무엇을 검증했나 (evidence)
7. What remains open?       무엇이 남았나
```

## 모델 / Models

작업에 맞는 역할 에이전트를 쓴다. 가장 좋은 모델을 늘 쓰지 않는다. 등급은 `task-contract.md` §역할. 어떤 모델이든 task의 `owner`에 `역할@모델`을 남긴다.
Use the role agent that fits the work, not always the strongest model. Tiers: `task-contract.md` §Roles. Whatever the model, record `owner: role@model` on the task.
