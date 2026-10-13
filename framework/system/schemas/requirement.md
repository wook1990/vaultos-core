# Requirement schema / 요구사항 스키마

위치: `projects/<slug>/requirements/requirements.yaml`
Location: `projects/<slug>/requirements/requirements.yaml`

## 형식 / Format

```yaml
requirements:
  - id: REQ-APP-001
    statement: "Users sign in with Google"
    type: functional            # functional | non_functional
    source: "intake/grill.md"   # where it came from
    priority: MUST              # MUST | SHOULD | COULD
    acceptance:
      - "A new user reaches the home screen after one Google consent"
    verification:
      - "tests/test_login.py passes"
    status: draft               # draft | approved | deprecated
```

## 규칙 / Rules

- ID는 다시 쓰지 않는다. 폐기한 요구사항은 `status: deprecated`로 남긴다.
  IDs are never reused. A retired requirement stays with `status: deprecated`.
- `acceptance`는 판정 가능한 문장이다. "빠르게", "편하게"는 판정할 수 없다.
  `acceptance` is a checkable sentence. "fast" or "easy" cannot be checked.
- `verification`은 무엇으로 확인하는지 적는다: 테스트, 수동 확인, 지표.
  `verification` names how it is checked: a test, a manual check, a metric.
- `approved` 요구사항을 바꾸려면 CR을 먼저 쓴다 → `change-request.md`.
  Changing an `approved` requirement needs a CR first → `change-request.md`.
- 파일은 VaultOS YAML 형식(`governance/task-contract.md` §YAML)을 따른다. 콜론이 든 값은 따옴표로 감싼다.
  The file follows the VaultOS YAML subset (`governance/task-contract.md` §YAML). Quote any value that contains a colon.
