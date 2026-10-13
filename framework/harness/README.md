# Harness / 하네스

에이전트가 VaultOS 계약을 따르게 하는 파일이다.
Files that make agents follow the VaultOS contract.

```
rules/vaultos.md   agent rules → ~/.agents/rules/vaultos.md (python3 install.py)
roles/*.md         role templates with a tier, no model names / 등급만 있는 역할 템플릿
```

## 설치 / Install

`python3 install.py`가 `~/.agents/rules/vaultos.md`를 설치한다. Claude Code(`~/.claude/CLAUDE.md`)나 Codex(`~/.codex/AGENTS.md`)의 규칙 파일이 없으면 이 파일을 가리키는 한 줄로 만든다. 있으면 고치지 않고 넣을 줄만 알려 준다.

`python3 install.py` installs `~/.agents/rules/vaultos.md`. If Claude Code (`~/.claude/CLAUDE.md`) or Codex (`~/.codex/AGENTS.md`) has no rule file, it creates one with a single line pointing here. An existing file is never edited; the line to add is printed instead.

## 역할 에이전트 / Role agents

| 역할 / Role | 등급 / Tier | 일 / Work |
|---|---|---|
| `planner` | high | 기획, 요구사항, 첫 구조 (읽기 전용) / planning, requirements, first structure (read-only) |
| `reviewer` | high | 리뷰, done 전 검토 (읽기 전용) / review, the check before done (read-only) |
| `implementer` | bulk | 구현 / implementation |
| `researcher` | bulk | 리서치 (읽기 전용) / research (read-only) |
| `mechanic` | fast | 작은 수정 / small edits |

```sh
vaultos agents set claude high <model> --effort <level>   # per machine / 기기마다
vaultos agents sync                                     # ~/.claude/agents/*.md, ~/.codex/agents/*.toml
```

모델 배정은 가이드다. 개인 설정이 먼저다. `vaultos:managed` 표식이 없는 같은 이름의 파일은 개인 것이라 덮어쓰지 않는다.
Model tiers are a guide; your own setup comes first. A file with the same name but without the `vaultos:managed` marker is yours and is never overwritten.
