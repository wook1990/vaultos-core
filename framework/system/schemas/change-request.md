# Change Request (CR) schema / 변경 요청 스키마

위치: `projects/<slug>/changes/CR-<NNN>.md`. 번호는 다시 쓰지 않는다.
Location: `projects/<slug>/changes/CR-<NNN>.md`. Numbers are never reused.

## 형식 / Format

```yaml
id: CR-001
request: "Change sign-in from email to Google"
reason: "Sign-up friction"
affected_requirements: [REQ-APP-001]
affected_architecture: []        # if not empty, an ADR is needed too
risks:
  - "Existing users need a migration"
decision: proposed               # proposed | approved | rejected | deferred
approved_by: null                # a person. Never an AI.
```

## 규칙 / Rules

| 필드 / Field | 규칙 / Rule |
|---|---|
| `request` | 무엇을 바꾸는가, 한 문장. / What changes, in one sentence. |
| `reason` | 왜 바꾸는가. 없으면 되돌릴지 판단할 수 없다. / Why. Without it nobody can decide whether to revert. |
| `affected_requirements` | 비어 있으면 CR이 아니라 task다. / Empty means it is a task, not a CR. |
| `risks` | 비운 채로 승인하지 않는다. / Never approved while empty. |
| `approved_by` | 사람만 쓴다. AI는 `approved`를 스스로 쓰지 않는다. / Only a person. An AI never writes `approved` for itself. |

거부된 CR도 지우지 않고 `rejected`로 남긴다. 거부 이력도 기록이다.
A rejected CR is kept as `rejected`. The rejection is part of the record.
