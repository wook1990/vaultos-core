"""Put the VaultOS contract surface into a code repository.

    .vaultos/link            project slug and its path inside the VaultOS folder (no machine paths)
    .vaultos/contract.yaml   contract version, profile, cached Grill Gate state
    tracker/                 tasks.yaml, issues.yaml, decisions.yaml, releases.yaml, progress.md
    AGENTS.md CLAUDE.md GEMINI.md   entry points that send agents to the vault (never copies of it)
    .githooks/pre-commit     runs `vaultos validate` (warns only)

Existing files are kept unless force=True.
"""

import os
import stat

from .paths import PROJECTS

CONTRACT_VERSION = "1.3"

TRACKER_FILES = {
    "tasks.yaml": """# VaultOS tracker contract v1.3 — tasks / 태스크
# Every task links to at least one requirement (No Requirement, No Code).
# 모든 task는 requirement_ids로 REQ에 연결된다.
#
# Fields / 필드: id, title, status (planned|ready|in_progress|blocked|review|done|dropped),
#   requirement_ids, owner (role@model, e.g. implementer@<model id>), definition_of_done,
#   evidence (required for done / done이면 필수), started_at, due, done_at (YYYY-MM-DD)
# Format: see governance/task-contract.md in your VaultOS folder.
tasks: []
""",
    "issues.yaml": """# Every issue names its impact and the linked tasks.
# issue는 영향 범위와 연결 task를 반드시 남긴다.
issues: []
""",
    "decisions.yaml": """# A decision without context and consequence is incomplete.
# context와 consequence가 없는 decision은 미완성이다.
decisions: []
""",
    "releases.yaml": """# A release does not end with empty known_risks.
# release는 known_risks가 빈 채로 끝나지 않는다.
releases: []
""",
    "progress.md": """# Progress / 진행 기록

## YYYY-MM-DD

- Goal this week / 이번 주 목표:
- In progress / 진행 중:
- Blocked / 막힌 것:
- Needs a decision / 결정 필요:
- Next / 다음:
""",
}

AGENT_ENTRY = """# {title}

<!-- vaultos:entry — written by `vaultos bind`. / vaultos bind가 만든 파일 -->

## 이 저장소 / This repository

이 저장소는 실행의 정본이다: 코드, 테스트, `tracker/*.yaml`.
의도(왜 만드는가)는 VaultOS 폴더의 `{project_path}/`에 있다. 그 내용을 이 저장소로 복사하지 않는다.

This repository is the source of truth for execution: code, tests, `tracker/*.yaml`.
The intent (why we build it) lives in `{project_path}/` inside your VaultOS folder. Do not copy it here.

## 먼저 읽을 것 / Read first

```
<VaultOS folder>/{project_path}/
├── project.yaml                  entry point / 진입점
├── intake/grill.md               Grill Gate — what and why / 무엇을 왜
├── governance/constitution.md    principles, non-goals / 원칙, 비목표
├── requirements/requirements.yaml
├── changes/                      CR — requirement changes / 요구사항 변경
└── architecture/adr/             ADR — structure decisions / 구조 결정
```

공통 규칙: VaultOS 폴더의 `system/VAULTOS.md`, `governance/`.
Shared rules: `system/VAULTOS.md` and `governance/` in the VaultOS folder.
VaultOS 폴더 위치는 `vaultos status`가 알려 준다. / `vaultos status` prints where it is.

## 작업 사이클 / Work cycle

1. 시작: REQ에 연결된 task를 `in_progress`로 바꾼다. 연결할 REQ가 없으면 멈추고 묻는다.
   Start: move a task that links to a REQ to `in_progress`. No REQ to link? Stop and ask.
2. 기록: task의 `owner`에 `역할@모델`을 쓴다.
   Record: write `owner: role@model` on the task.
3. 마무리: `definition_of_done`을 확인하고 `evidence`, `done_at`을 채운 뒤 `done`으로 바꾼다.
   Finish: check `definition_of_done`, fill `evidence` and `done_at`, then set `done`.
4. 검사: 커밋 전에 `vaultos validate`. / Check: run `vaultos validate` before committing.
5. 종료: 세션 끝에 `vaultos sync`. / End: run `vaultos sync` when the session ends.

## 하지 않는 것 / Never

- Grill Gate가 `pending`이면 구현하지 않는다. / Do not implement while the Grill Gate is `pending`.
- REQ를 바꾸려면 CR, 구조를 바꾸려면 ADR을 먼저 쓴다. / Write a CR before changing a REQ, an ADR before changing structure.
- 의도 문서(기획서, 로드맵, 아키텍처)를 이 저장소에 만들지 않는다. / Do not create intent documents in this repository.
- evidence 없이 done으로 바꾸지 않는다. / Do not mark a task done without evidence.
"""

PRE_COMMIT = """#!/bin/sh
# VaultOS contract check. Install: git config core.hooksPath .githooks
# Warns only. Change the last line to `exit 1` to block commits.
# VaultOS 계약 검사. 경고만 한다. 막으려면 마지막 줄을 exit 1로 바꾼다.
if command -v vaultos >/dev/null 2>&1; then
  vaultos validate --quiet || echo "  vaultos validate: contract violations / 계약 위반 — run 'vaultos validate'"
fi
exit 0
"""


def bind(repo, slug, profile="full", force=False):
    made, skipped = [], []
    project_path = f"{PROJECTS}/{slug}"
    d = os.path.join(repo, ".vaultos")
    os.makedirs(d, exist_ok=True)

    def put(rel, body, always=False, executable=False):
        p = os.path.join(repo, rel)
        if os.path.exists(p) and not (force or always):
            skipped.append(rel)
            return
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        if executable:
            os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        made.append(rel)

    put(".vaultos/link", "# VaultOS project of this repository. No machine paths — safe to commit.\n"
                         "# 이 저장소의 VaultOS 프로젝트. 기기 경로가 없어 커밋해도 된다.\n"
                         f"project: {slug}\nproject_path: {project_path}\n", always=True)
    put(".vaultos/contract.yaml", f"""# The VaultOS contract this repository follows. Declares, does not copy.
# 이 저장소가 따르는 VaultOS 계약. 내용을 복사하지 않고 선언만 한다.
contract_version: "{CONTRACT_VERSION}"
governance_profile: {profile}
# Grill Gate cache. The source of truth is project.yaml in the vault. / 정본은 볼트의 project.yaml
grill: unknown
""")
    for name, body in TRACKER_FILES.items():
        put(f"tracker/{name}", body)
    for fn, title in (("AGENTS.md", "Agent Instructions"), ("CLAUDE.md", "Claude Instructions"),
                      ("GEMINI.md", "Gemini Instructions")):
        put(fn, AGENT_ENTRY.format(title=title, project_path=project_path))
    put(".githooks/pre-commit", PRE_COMMIT, executable=True)
    return made, skipped
