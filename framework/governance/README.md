# Governance / 공통 계약

모든 프로젝트가 같이 쓰는 계약이다. 프로젝트마다 복사하지 않고 여기를 가리킨다.
Contracts every project shares. Projects point here; they never copy them.

| 문서 / Document | 정하는 것 / Defines |
|---|---|
| `grill-gate.md` | 만들기 전에 캐묻는 게이트 / the gate that questions a project before building |
| `task-contract.md` | task 필드, 작업 사이클, YAML 형식 / task fields, the work cycle, the YAML subset |
| `definition-of-done.md` | done의 조건과 실패 상태 / when a task is done, and failure states |
| `approval-policy.md` | 사람이 승인해야 하는 변경 / changes a person must approve |
| `agent-policy.md` | 에이전트가 하지 않는 것, 보고 형식 / what an agent never does, how it reports |

바꾸고 싶은 계약은 `system/upgrade-keep.txt`에 적고 고친다. `vaultos upgrade`가 덮어쓰지 않는다.
To own a contract, list it in `system/upgrade-keep.txt` and edit it. `vaultos upgrade` will leave it alone.
