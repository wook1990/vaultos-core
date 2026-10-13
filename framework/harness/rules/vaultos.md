# VaultOS — agent rules / 에이전트 규칙

이 파일은 VaultOS가 소유한다. `python3 install.py`가 덮어쓴다 (이전 판은 `~/.agents/backups/`).
VaultOS owns this file. `python3 install.py` overwrites it (previous copy in `~/.agents/backups/`).

개인 규칙은 이 파일을 가리키고 내용을 다시 쓰지 않는다. 볼트와 연결 저장소에서는 이 파일을 따른다.
Your personal rules point at this file and do not repeat it. In the vault and linked repositories, this file applies.

VaultOS의 목적은 사람이 AI의 작업을 점검하는 것이다: 무엇을 했나, 기획이 좋았나, 태스크를 잘 나눴나, 잘 마무리했나.
VaultOS exists so a person can audit AI work: what was done, was the plan good, were tasks split well, was it finished properly.

## 1. 볼트와 저장소 / Vault and repository

- VaultOS 폴더는 사용자 볼트 안의 한 폴더다 (`vaultos status`가 위치를 알려 준다). 그 밖의 볼트 파일은 건드리지 않는다.
  The VaultOS folder is one folder inside the user's vault (`vaultos status` shows where). Never touch other files in the vault.
- 의도(기획, 요구사항, 결정 이유)는 볼트에, 실행(코드, 테스트, `tracker/*.yaml`)은 저장소에 둔다. 한쪽을 다른 쪽에 복사하지 않는다.
  Intent (plans, requirements, reasons) lives in the vault; execution (code, tests, `tracker/*.yaml`) in the repository. Never copy one into the other.
- 연결 저장소(`.vaultos/link`가 있음)에서는 볼트 밖에 두 번째 기획서, 트래커, 문서 트리를 만들지 않는다.
  In a linked repository (`.vaultos/link` exists), do not create a second plan, tracker or document tree outside the vault.
- Grill Gate가 `pending`이면 구현하지 않는다. 요구사항을 바꾸려면 CR(`changes/`), 구조를 바꾸려면 ADR(`architecture/adr/`)을 먼저 쓴다.
  No implementation while the Grill Gate is `pending`. Write a CR (`changes/`) before changing a requirement and an ADR (`architecture/adr/`) before changing structure.

## 2. 작업 사이클 / Work cycle

필드의 정본은 VaultOS 폴더의 `governance/task-contract.md`다.
The field definitions live in `governance/task-contract.md` in the VaultOS folder.

1. **시작 / Start.** `vaultos status`로 상태를 본다. REQ에 연결된 task를 고르거나 만들고 `in_progress`로 바꾼다. 연결할 REQ가 없으면 멈추고 묻는다.
   Check `vaultos status`. Pick or create a task linked to a REQ and set `in_progress`. No REQ to link? Stop and ask.
2. **기록 / Record.** task의 `owner`에 `역할@모델`을 쓴다.
   Write `owner: role@model` on the task.
3. **마무리 / Finish.** `definition_of_done`을 확인하고 `evidence`, `done_at`, 무엇을 왜 바꿨는지 한 줄(`note`)을 채운 뒤 `done`으로 바꾼다.
   Check `definition_of_done`; fill `evidence`, `done_at` and a one-line `note` on what changed and why; then set `done`.
4. **검사 / Check.** 커밋 전에 `vaultos validate`. 위반이 있으면 커밋하지 않는다.
   Run `vaultos validate` before committing. Do not commit with violations.
5. **종료 / End.** 세션 끝에 `vaultos sync`를 한 번 실행한다.
   Run `vaultos sync` once at the end of the session.

## 3. 모델 배정 (가이드) / Model tiers (a guide)

- **개인 설정이 먼저다.** 개인 규칙이나 개인 에이전트가 모델을 정하면 그것을 따른다.
  **Your own setup comes first.** If your personal rules or agents choose a model, follow them.
- 등급: **high** 기획, 설계, 리뷰 · **bulk** 구현, 리서치 · **fast** 명세가 닫힌 작은 수정. 역할: `planner`·`reviewer` = high, `implementer`·`researcher` = bulk, `mechanic` = fast.
  Tiers: **high** planning, design, review · **bulk** implementation, research · **fast** small edits with a closed spec. Roles: `planner`·`reviewer` = high, `implementer`·`researcher` = bulk, `mechanic` = fast.
- 가장 좋은 모델을 늘 쓰지 않는다. 작업에 맞는 역할에 맡긴다.
  Do not always use the strongest model. Hand the work to the role that fits.

## 4. 안전 / Safety

- push, 릴리스, CR 승인, 볼트 구조 변경은 사람이 한다. / A person pushes, releases, approves CRs and changes the vault structure.
- 비밀값은 환경변수에만 둔다. 볼트, 저장소, remote URL에 쓰지 않는다. / Secrets live in environment variables only — never in the vault, the repository or a remote URL.
- 환경이 이상하면 `vaultos doctor`. / When the environment looks wrong, run `vaultos doctor`.
