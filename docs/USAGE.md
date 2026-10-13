# VaultOS 사용법 / Usage

## 0. 개념 / Concepts

VaultOS는 의도와 실행을 나눠 둔다. 의도(왜 만드는가)는 볼트 안의 VaultOS 폴더에, 실행(무엇을 만들었나)은 코드 저장소에 있다. 둘은 `.vaultos/link`의 프로젝트 이름으로 이어진다.

VaultOS keeps intent and execution apart. Intent (why we build it) lives in the VaultOS folder inside your vault; execution (what was built) lives in the code repository. They are joined by the project name in `.vaultos/link`.

```
<vault>/VaultOS/projects/my-app/      project.yaml, intake/grill.md, requirements/, changes/, architecture/adr/
~/workspace/my-app/                   code, tests, tracker/tasks.yaml, .vaultos/link, AGENTS.md
~/.config/vaultos/config              this machine: vault path, folder, repo paths, model tiers
```

## 1. 설치 / Install

```sh
git clone https://github.com/<owner>/vaultos.git ~/tools/vaultos
cd ~/tools/vaultos
python3 install.py
```

`install.py`는 `~/.local/bin/vaultos` 링크와 에이전트 규칙 `~/.agents/rules/vaultos.md`를 만든다. Claude Code나 Codex의 규칙 파일이 이미 있으면 고치지 않고 넣을 한 줄만 알려 준다. `--check`는 바뀔 것만 보여 준다.

`install.py` creates the `~/.local/bin/vaultos` link and the agent rules `~/.agents/rules/vaultos.md`. If Claude Code or Codex already has a rule file, it is not edited; the line to add is printed. `--check` only shows what would change.

`~/.local/bin`이 PATH에 없으면 셸 설정에 넣는다.
If `~/.local/bin` is not on your PATH, add it in your shell profile.

## 2. 볼트 안에 폴더 만들기 / Create the folder inside your vault

```sh
vaultos init                                  # asks: vault path, folder name, language, repository folder
vaultos init ~/Obsidian/MyVault --lang ko --workspace ~/workspace
```

- 볼트 경로는 반드시 입력한다. 이미 있는 폴더여야 한다 (Obsidian 볼트, 동기화 폴더, 아무 폴더).
  The vault path is required and must be an existing folder (an Obsidian vault, a synced folder, any folder).
- VaultOS는 `<vault>/VaultOS/`에만 쓴다. 볼트 루트, 다른 노트, `.obsidian`은 건드리지 않는다. 폴더 이름은 `--folder`로 바꾼다.
  VaultOS writes only to `<vault>/VaultOS/`. The vault root, your other notes and `.obsidian` are never touched. Change the folder name with `--folder`.
- 코드 저장소 폴더(`--workspace`)는 볼트 밖이어야 한다. 동기화 도구가 `.git`을 깨뜨릴 수 있다.
  The repository folder (`--workspace`) must be outside the vault. Sync tools can break `.git` folders.

## 3. 프로젝트 / Projects

### 새 프로젝트 / New project

```sh
vaultos new my-app --name "My App" --mission "Sign in within 10 seconds"
```

볼트에 `projects/my-app/`을 만들고, `~/workspace/my-app` 저장소를 만들어 계약 파일을 놓는다: `.vaultos/`, `tracker/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.githooks/pre-commit`. 이 파일들은 저장소에 커밋한다 (기기 경로가 들어 있지 않다).

Creates `projects/my-app/` in the vault and a `~/workspace/my-app` repository with the contract files: `.vaultos/`, `tracker/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.githooks/pre-commit`. Commit them; they contain no machine paths.

### 기존 저장소 / Existing repository

```sh
vaultos new my-app --path ~/code/my-app       # register and link in one step
cd ~/code/my-app && vaultos link my-app       # link to a project that already exists
```

이미 있는 `AGENTS.md`, tracker 파일은 덮어쓰지 않는다.
Existing `AGENTS.md` and tracker files are never overwritten.

## 4. Grill Gate

구현 전에 결과, 문제, 비목표, 기능, 성공 기준, 검증, 멈추는 조건을 정한다. 필수 답이 비면 게이트는 `pending`이고, `pending`이면 구현하지 않는다.
Before implementation, fix the outcome, problem, non-goals, features, success criteria, verification and stop condition. With a required answer empty the gate stays `pending`, and nothing is implemented while it is `pending`.

| 방식 / Mode | 실행 / Run |
|---|---|
| 질문에 답한다 / answer questions | `vaultos grill` |
| 기획서에서 옮긴다 / from plan documents | 저장소에 `docs/plan.md`, `docs/requirements.md`를 두고 `vaultos grill` / put `docs/plan.md` and `docs/requirements.md` in the repository, then `vaultos grill` |
| 메모 폴더에서 / from a folder of notes | `vaultos grill --docs ~/notes/my-app` |

기획서 양식은 VaultOS 폴더의 `system/templates/plan.md`, `requirements.md`. 결과는 `intake/grill.md`, `governance/constitution.md`, `requirements/requirements.yaml`, `status/timeline.md`, 그리고 비어 있는 tracker의 task들이다.
Templates: `system/templates/plan.md` and `requirements.md` in the VaultOS folder. The results are `intake/grill.md`, `governance/constitution.md`, `requirements/requirements.yaml`, `status/timeline.md`, and tasks in an empty tracker.

## 5. 작업 사이클 / Work cycle

에이전트(와 사람)는 이 순서를 따른다. 규칙은 `~/.agents/rules/vaultos.md`, 필드는 `governance/task-contract.md`.
Agents (and people) follow this order. Rules: `~/.agents/rules/vaultos.md`. Fields: `governance/task-contract.md`.

```yaml
tasks:
  - id: T-MYAPP-002
    title: "Google login — build"
    status: done
    requirement_ids: [REQ-MYAPP-001]
    owner: implementer@<model id>
    definition_of_done:
      - "tests/test_login.py passes"
    evidence: [tests/test_login.py, "commit 3f2a1c0"]
    started_at: 2026-10-12
    done_at: 2026-10-13
    note: "OAuth callback added; email login kept for existing users"
```

1. 시작: REQ에 연결된 task를 `in_progress`로. / Start: set a task linked to a REQ to `in_progress`.
2. 기록: `owner: 역할@모델`. / Record: `owner: role@model`.
3. 마무리: `evidence`, `done_at`, `note`를 채우고 `done`. / Finish: fill `evidence`, `done_at`, `note`, then `done`.
4. 검사: 커밋 전 `vaultos validate`. / Check: `vaultos validate` before committing.
5. 종료: `vaultos sync`. / End: `vaultos sync`.

요구사항을 바꾸려면 `changes/CR-NNN.md`, 구조를 바꾸려면 `architecture/adr/ADR-NNN-*.md`를 먼저 쓴다 (양식: `system/templates/`).
To change a requirement write `changes/CR-NNN.md` first; to change structure, `architecture/adr/ADR-NNN-*.md` (templates in `system/templates/`).

## 6. 검사 / Validation

```sh
vaultos validate          # repository + vault documents
vaultos validate --ci     # repository only — for CI, where the vault is not available
```

위반(종료 코드 1)과 경고를 나눠 보여 준다. 무엇을 검사하는지는 `system/schemas/task.md`.
Violations (exit code 1) and warnings are listed separately. What is checked: `system/schemas/task.md`.

### Git hook

```sh
git config core.hooksPath .githooks       # warns on commit; edit the hook to block
```

### GitHub Actions

```yaml
# .github/workflows/vaultos.yml in your project
name: vaultos
on: [pull_request]
jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with: { repository: <owner>/vaultos, path: .vaultos-cli }
      - run: python3 .vaultos-cli/vaultos validate --ci
```

## 7. 동기화 / Sync

`vaultos sync`는 tracker를 읽어 `project.yaml`의 `next_actions`, `blocked`와 `kanban.md`를 갱신한다. 보드는 Obsidian Kanban 플러그인으로 열 수 있고, 읽기 전용 생성물이다. 상태는 `tracker/tasks.yaml`에서 바꾼다.

`vaultos sync` reads the tracker and updates `next_actions` and `blocked` in `project.yaml`, plus `kanban.md`. The board opens in the Obsidian Kanban plugin and is a read-only, generated file. Change state in `tracker/tasks.yaml`.

## 8. 모델 배정 (가이드) / Model tiers (a guide)

| 등급 / Tier | 작업 / Work | 역할 / Roles |
|---|---|---|
| high | 기획, 설계, 리뷰 / planning, design, review | `planner`, `reviewer` |
| bulk | 구현, 리서치 / implementation, research | `implementer`, `researcher` |
| fast | 명세가 닫힌 작은 수정 / small edits with a closed spec | `mechanic` |

```sh
vaultos agents set claude high <model> --effort high
vaultos agents set claude bulk <model>
vaultos agents set codex  fast <model>
vaultos agents             # show
vaultos agents sync        # create ~/.claude/agents/<role>.md, ~/.codex/agents/<role>.toml
```

개인 설정이 먼저다. 이미 있는 같은 이름의 에이전트 파일(`vaultos:managed` 표식 없음)은 덮어쓰지 않는다. 매핑만 적어 두면 `validate`가 기획·리뷰 task를 high가 아닌 모델이 했을 때 경고한다. `doctor`는 이 부분에서 경고를 내지 않는다.

Your own setup comes first. An agent file with the same name and no `vaultos:managed` marker is never overwritten. With only the mapping set, `validate` warns when a planning or review task was done by a non-high model. `doctor` never warns about tiers.

## 9. 점검과 갱신 / Check and update

```sh
vaultos doctor            # 1 version/CLI  2 vault  3 rules  4 rule links  5 secrets  6 models
git pull && python3 install.py && vaultos upgrade --dry-run && vaultos upgrade
```

`upgrade`는 3-way 병합이다. 고치지 않은 파일은 교체하고(이전 판 `archive/backups/`), 고친 파일은 병합한다. 겹치면 새 판을 `<file>.vaultos-new`로 옆에 둔다. 내 것으로 지키려면 `system/upgrade-keep.txt`에 적는다. 지운 파일은 다시 만들지 않는다.

`upgrade` is a 3-way merge. Unedited files are replaced (previous copy in `archive/backups/`), edited files are merged; on overlap the new copy is written next to it as `<file>.vaultos-new`. To own a file, list it in `system/upgrade-keep.txt`. Files you deleted are not recreated.

## 10. 여러 기기 / Several machines

볼트가 동기화된다면 기기마다 `install.py`와 설정만 하면 된다. 기기마다 볼트 경로와 저장소 경로가 달라도 된다. 둘 다 그 기기의 `~/.config/vaultos/config`에만 있다.

If your vault syncs, each machine only needs `install.py` and its own settings. Vault and repository paths may differ per machine; both live only in that machine's `~/.config/vaultos/config`.

```sh
vaultos config --set-vault "/path/to/vault on this machine"
cd ~/code/my-app && vaultos link my-app
```

## 11. 문제 해결 / Troubleshooting

| 증상 / Symptom | 조치 / Fix |
|---|---|
| `No vault is configured` | `vaultos init` 또는 / or `vaultos config --set-vault <path>` |
| `cannot read tracker/tasks.yaml — line N` | 그 줄을 `governance/task-contract.md` §YAML 형식에 맞춘다. `: `가 든 값은 따옴표로. / Fix that line to the YAML subset; quote values containing `: `. |
| 볼트에 접근할 수 없다 / cannot open the vault | 드라이브나 동기화 폴더가 마운트돼 있는지 본다. / Check that the drive or sync folder is mounted. |
| `.vaultos-new` 파일 / files | 열어서 직접 합치고 지운다. / Merge by hand and delete them. |
| 출력 언어 / output language | `vaultos config --set-lang ko` 또는 / or `VAULTOS_LANG=en` |

## 12. 설정 / Settings

`~/.config/vaultos/config` (이 기기만 / this machine only)

| 키 / Key | 뜻 / Meaning |
|---|---|
| `vault`, `folder` | 볼트 경로와 그 안의 VaultOS 폴더 이름 / the vault path and the VaultOS folder name |
| `workspace_root` | `vaultos new`가 저장소를 만드는 곳 / where `vaultos new` creates repositories |
| `lang` | `ko` / `en` |
| `repo.<slug>` | 이 기기의 저장소 경로 (`vaultos link`가 쓴다) / this machine's repository path (written by `vaultos link`) |
| `model.<tool>.<tier>` | 모델 등급 매핑 / model tier mapping |

환경변수 / Environment: `VAULTOS_VAULT`, `VAULTOS_FOLDER`, `VAULTOS_WORKSPACE`, `VAULTOS_LANG`.
