# Task contract / 태스크 계약

## 작업 사이클 / Work cycle

1. **시작 / Start.** REQ에 연결된(`requirement_ids`) task를 고르거나 만들고 `in_progress`로 바꾼다. `started_at`을 적는다. 연결할 REQ가 없으면 멈추고 사람에게 묻는다.
   Pick or create a task linked to a REQ (`requirement_ids`), set `in_progress`, write `started_at`. No REQ to link? Stop and ask a person.
2. **기록 / Record.** `owner`에 `역할@모델`을 쓴다 (예: `implementer@<model id>`). 작업한 에이전트가 바뀌면 고친다.
   Write `owner: role@model` (e.g. `implementer@<model id>`). Update it when another agent takes over.
3. **마무리 / Finish.** `definition_of_done`을 확인하고 `evidence`(테스트, 로그, 커밋)와 `done_at`을 채운 뒤 `done`으로 바꾼다. 무엇을 왜 바꿨는지 `note`에 한 줄 남긴다.
   Check `definition_of_done`, fill `evidence` (tests, logs, commits) and `done_at`, then set `done`. Leave one line in `note` on what changed and why.
4. **검사 / Check.** 커밋 전에 `vaultos validate`. 위반이 있으면 커밋하지 않는다.
   Run `vaultos validate` before committing. Do not commit with violations.
5. **종료 / End.** 세션 끝에 `vaultos sync`를 한 번 실행한다.
   Run `vaultos sync` once when the session ends.

## 필드 / Fields

| 필드 / Field | 필수 / Required | 뜻 / Meaning |
|---|---|---|
| `id` | yes | `T-<DOMAIN>-<NNN>`, 다시 쓰지 않는다 / never reused |
| `title` | yes | 한 줄 / one line |
| `status` | yes | planned, ready, in_progress, blocked, review, done, dropped |
| `requirement_ids` | yes | 비어 있으면 task를 만들지 않는다 / no task without one |
| `owner` | at done | `역할@모델` / `role@model` |
| `definition_of_done` | recommended | 판정 가능한 조건 / checkable conditions |
| `evidence` | at done | 증거 경로나 커밋 / paths or commits that prove it |
| `started_at`, `due`, `done_at` | `done_at` at done | `YYYY-MM-DD` |
| `note` | optional | 무엇을 왜 / what and why |

## 역할 / Roles

| 역할 / Role | 등급 / Tier | 일 / Work |
|---|---|---|
| `planner` | high | 기획, 요구사항 / planning, requirements |
| `reviewer` | high | 리뷰, done 전 검토 / review, the check before done |
| `implementer` | bulk | 구현 / implementation |
| `researcher` | bulk | 조사 / research |
| `mechanic` | fast | 작은 수정 / small edits |

등급은 가이드다. 개인 설정이 모델을 정한다. `vaultos validate`는 어긋나면 경고만 한다.
Tiers are a guide; your own setup chooses the model. `vaultos validate` only warns on a mismatch.

## YAML 형식 / YAML subset

VaultOS는 의존성 없이 YAML을 읽기 위해 다음 형식만 받는다. 벗어나면 줄 번호와 함께 오류를 낸다.
VaultOS reads YAML without dependencies and accepts only this subset. Anything else is an error with a line number.

- `key: value`, `key: "quoted"`, `key: 'quoted'`
- `key: [a, b]`, `key: {}`
- 들여쓴 맵과 `- ` 목록 / indented maps and `- ` lists
- `#` 주석 / `#` comments

받지 않는 것 / Not accepted: `|` `>` 여러 줄 값 / block scalars, `{a: b}`, 앵커·별칭·태그 / anchors, aliases, tags, 탭 들여쓰기 / tab indentation, 따옴표 없이 `: `가 든 값 / unquoted values containing `: `.
