# Definition of Done / 완료 정의

## 정의 / Definition

```
Requirement linked
+ Implementation complete
+ Acceptance criteria passed
+ Evidence exists
+ No unapproved drift
= done
```

구현만 끝난 상태는 done이 아니다. **No Evidence, No Done.**
Implemented is not done. **No Evidence, No Done.**

| 조건 / Condition | 확인 / How to check |
|---|---|
| Requirement linked | task의 `requirement_ids` / the task's `requirement_ids` |
| Implementation complete | 코드와 문서가 실제로 있다 / code and docs exist |
| Acceptance passed | REQ의 `acceptance`가 모두 통과 / every `acceptance` line of the REQ holds |
| Evidence exists | 테스트 결과, 로그, 커밋 / test output, logs, commits |
| No unapproved drift | 승인 없이 바뀐 범위나 구조가 없다 / no scope or structure changed without approval |

## 실패 상태 / Failure states

끝나지 않은 일은 done으로 적지 않는다. `status`와 `note`로 남긴다.
Unfinished work is never marked done. Record it with `status` and `note`.

| 상태 / State | `status` | `note`에 쓸 것 / What `note` says |
|---|---|---|
| 시도했고 실패 / tried and failed | `blocked` | 원인 / the cause |
| 일부만 됨 / partly done | `in_progress` | 남은 것 / what remains |
| 외부 의존 / waiting on something | `blocked` | 무엇을 기다리는가 / what it waits for |
| 승인 대기 / needs approval | `blocked` | 어느 승인 항목인가 / which approval item |
| 하지 않기로 함 / not doing it | `dropped` | 이유 / why |

실패를 성공으로 적는 것은 금지다.
Reporting a failure as a success is forbidden.

## 프로필별 / By profile

| profile | done에 필요한 것 / Needed for done |
|---|---|
| `light` | 구현 + 무엇을 확인했는지 한 줄 / implementation + one line on what was checked |
| `full` | 위 표 전체 / everything above |
