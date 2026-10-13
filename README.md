# VaultOS

**AI 코딩 에이전트가 한 일을 감사할 수 있게 만드는 계약과 CLI.**
**A contract and CLI that make the work of AI coding agents auditable.**

에이전트에게 코드를 맡기면 네 가지가 궁금해진다. VaultOS는 그 답이 기록으로 남게 한다.
When an agent writes your code, four questions come up. VaultOS keeps the answers on record.

| 질문 / Question | 기록 / Record |
|---|---|
| 무엇을 했나 / What was done? | task, `owner: 역할@모델 / role@model`, evidence, `done_at` |
| 기획이 좋았나 / Was the plan good? | Grill Gate, requirements with acceptance and verification, CR, ADR |
| 태스크를 잘 나눴나 / Were tasks split well? | every task links to a REQ; `vaultos validate` flags orphans both ways |
| 잘 마무리했나 / Was it finished properly? | no done without evidence; definition of done |

```
your vault/VaultOS/   = why   intent, Grill, requirements, CR, ADR     (Obsidian-friendly Markdown)
your repository       = what  code, tests, tracker/*.yaml, evidence
```

## 특징 / Features

- 1인 개발자용. 서버, 계정, 데이터베이스가 없다. 표준 라이브러리만 쓰는 Python 3.9+.
  Built for solo developers. No server, no account, no database. Python 3.9+ standard library only.
- 이미 쓰는 볼트(Obsidian 등) 안의 폴더 하나에만 쓴다. 볼트 루트와 `.obsidian`은 건드리지 않는다.
  Writes only to one folder inside the vault you already use (Obsidian or any folder). Never touches the vault root or `.obsidian`.
- Claude Code, Codex, Gemini, Cursor 등 에이전트에 상관없이 같은 계약을 쓴다 (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
  Agent-neutral: Claude Code, Codex, Gemini, Cursor read the same contract (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
- 작업 등급(high, bulk, fast)에 맞는 모델을 쓰도록 안내한다. 가이드일 뿐이고 개인 설정이 먼저다.
  Guides agents to a model that fits the work tier (high, bulk, fast). A guide only — your own setup comes first.
- CLI 출력은 한국어와 영어. 문서는 모두 한영 병기.
  CLI output in Korean or English. Every document is bilingual.

## 시작하기 / Quick start

```sh
git clone https://github.com/wook1990/vaultos-core.git
cd vaultos-core
python3 install.py                       # CLI link + agent rules / CLI 링크와 에이전트 규칙
vaultos init ~/Obsidian/MyVault          # creates ~/Obsidian/MyVault/VaultOS / 볼트 안에 폴더 생성
vaultos new my-app                       # vault project + ~/workspace/my-app repository
cd ~/workspace/my-app
vaultos grill                            # answer the Grill Gate / Grill Gate에 답한다
vaultos validate                         # check the contract / 계약 검사
```

`vaultos init`은 볼트 경로를 반드시 입력받는다. 볼트는 이미 있어야 한다.
`vaultos init` always asks for your vault path. The vault must already exist.

자세한 사용법 / Full guide: [docs/USAGE.md](docs/USAGE.md)

## 명령 / Commands

| 명령 / Command | 하는 일 / What it does |
|---|---|
| `vaultos init` | 볼트 안에 VaultOS 폴더 생성 / create the VaultOS folder inside your vault |
| `vaultos new <slug>` | 프로젝트 등록과 저장소 연결 / register a project and its repository |
| `vaultos link <slug>` | 기존 저장소 연결 / link an existing repository |
| `vaultos grill` | Grill Gate — 기획서가 있으면 옮겨 적고, 없으면 묻는다 / takes answers from plan documents or asks |
| `vaultos validate` | 계약 검사, `--ci`는 저장소만 / contract check, `--ci` for the repository only |
| `vaultos sync` | tracker → 볼트 요약과 칸반 보드 / tracker → vault summary and Kanban board |
| `vaultos status` | 프로젝트와 저장소 현황 / projects and repositories |
| `vaultos agents` | 모델 등급과 역할 에이전트 (가이드) / model tiers and role agents (a guide) |
| `vaultos doctor` | 이 기기 점검 (읽기 전용) / read-only check of this machine |
| `vaultos upgrade` | 볼트의 프레임워크 파일 갱신 (3-way 병합) / update framework files in the vault (3-way merge) |
| `vaultos config` | 설정 보기, 바꾸기 / show or change settings |

## 지원 환경 / Supported

macOS, Linux, Windows의 WSL. Python 3.9–3.13. `git`이 있으면 `upgrade`가 3-way 병합을 한다.
macOS, Linux, and WSL on Windows. Python 3.9–3.13. With `git` installed, `upgrade` does a 3-way merge.

## 라이선스 / License

MIT. [LICENSE](LICENSE)
