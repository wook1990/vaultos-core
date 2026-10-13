# Task schema / 태스크 스키마

위치: 저장소의 `tracker/tasks.yaml`. 정본은 저장소다. 볼트에는 `vaultos sync`가 요약과 보드만 보낸다.
Location: `tracker/tasks.yaml` in the repository. The repository is the source of truth; `vaultos sync` sends only a summary and a board to the vault.

## 형식 / Format

```yaml
tasks:
  - id: T-APP-004
    title: "Google OAuth callback"
    status: in_progress        # planned | ready | in_progress | blocked | review | done | dropped
    requirement_ids: [REQ-APP-001]
    owner: implementer@<model id>
    definition_of_done:
      - "Callback success path works"
      - "Integration test passes"
    evidence: []               # required before done
    started_at: 2026-10-13     # optional
    due: 2026-10-20            # optional
    done_at: null              # required with done
```

## 검사 / What `vaultos validate` checks

| 항목 / Item | 결과 / Result |
|---|---|
| `requirement_ids`가 비었다 / empty `requirement_ids` | 위반 / violation |
| `done`인데 `evidence`가 없다 / `done` without `evidence` | 위반 / violation |
| 날짜가 `YYYY-MM-DD`가 아니다 / date not `YYYY-MM-DD` | 위반 / violation |
| id 중복, 읽을 수 없는 YAML / duplicate id, unreadable YAML | 위반 / violation |
| 볼트에 없는 REQ를 가리킨다 / links to a REQ that is not in the vault | 위반 / violation |
| `done`인데 `done_at`이나 `owner`(역할@모델)가 없다 / `done` without `done_at` or `owner` (role@model) | 경고 / warning |
| high 역할을 high가 아닌 모델이 했다 / a high-tier role done by a non-high model | 경고 / warning |
| task가 없는 REQ / a REQ with no task | 경고 / warning |

자세한 계약은 `governance/task-contract.md`.
The full contract: `governance/task-contract.md`.
