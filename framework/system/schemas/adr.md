# Architecture Decision Record (ADR) schema / 구조 결정 기록 스키마

위치: `projects/<slug>/architecture/adr/ADR-<NNN>-<slug>.md`. 번호는 다시 쓰지 않는다.
Location: `projects/<slug>/architecture/adr/ADR-<NNN>-<slug>.md`. Numbers are never reused.

## 형식 / Format

```markdown
---
status: proposed        # proposed | accepted | superseded
date: YYYY-MM-DD
superseded_by: null
---
# ADR-001 — <title>

## Context
## Options
A. ...
B. ...
## Decision
## Reason
## Consequences
```

## 규칙 / Rules

| 절 / Section | 규칙 / Rule |
|---|---|
| Context | 왜 지금 결정이 필요한가. / Why a decision is needed now. |
| Options | 최소 2개. 하나뿐이면 결정이 아니라 통보다. / At least two. One option is an announcement, not a decision. |
| Decision | 고른 것 하나. / The one chosen. |
| Reason | 왜 그것인가, 다른 것은 왜 버렸는가. / Why this one, and why not the others. |
| Consequences | 좋은 결과와 나쁜 결과를 둘 다 쓴다. 감수한 비용이 여기 남는다. / Both good and bad results. The accepted cost stays here. |

`superseded`가 되면 대체한 ADR을 적는다.
When `superseded`, name the ADR that replaced it.
