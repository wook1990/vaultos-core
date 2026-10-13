# Changelog / 변경 기록

[SemVer](https://semver.org)를 따른다. MAJOR는 볼트 구조나 필수 계약이 바뀔 때, MINOR는 선택 기능이 늘 때, PATCH는 고침과 문구다.
Follows [SemVer](https://semver.org). MAJOR when the vault layout or a required contract changes, MINOR for optional features, PATCH for fixes and wording.

## [3.0.0] - 2026-10-13

첫 공개 판. 1인 개발자용 코어만 담는다.
First public release. The core for solo developers only.

### 추가 / Added

- 사용자 볼트 안의 폴더 하나에만 설치 (`vaultos init <vault>`). 볼트 경로는 필수 입력이고, 볼트 루트와 `.obsidian`은 건드리지 않는다.
  Installs into one folder inside your existing vault (`vaultos init <vault>`). The vault path is required; the vault root and `.obsidian` are never touched.
- 엄격한 YAML 부분 집합 파서. 지원하지 않는 형식은 줄 번호와 함께 오류로 알린다.
  A strict YAML-subset parser. Unsupported syntax is an error with a line number.
- `vaultos validate --ci`: 볼트 없이 저장소만 검사. GitHub Actions 예시.
  `vaultos validate --ci`: repository-only checks without the vault. GitHub Actions example.
- 감사 기록: `owner: 역할@모델`, `started_at`, 등급 불일치 경고, 볼트에 없는 REQ를 가리키는 task 위반.
  Audit trail: `owner: role@model`, `started_at`, tier-mismatch warnings, a violation for tasks pointing at a REQ that is not in the vault.
- 모델 등급 가이드 `vaultos agents` (high, bulk, fast). 개인 설정이 먼저다.
  Model-tier guide `vaultos agents` (high, bulk, fast). Your own setup comes first.
- `upgrade`의 기준판을 볼트 안 `system/.base/`에 저장. git 히스토리가 없어도 3-way 병합.
  `upgrade` keeps its base in `system/.base/` inside the vault: 3-way merges without git history.
- 한국어/영어 CLI 출력, 모든 문서 한영 병기, 영문 파일 이름.
  Korean/English CLI output, every document bilingual, English file names.
- 단위 테스트, 클린 설치 E2E 테스트, CI (Python 3.9–3.13, Linux, macOS).
  Unit tests, a clean-install end-to-end test, CI (Python 3.9–3.13, Linux, macOS).

### 바뀜 / Changed

- 기기별 경로(볼트, 저장소)는 `~/.config/vaultos/config`에만 둔다. `.vaultos/link`에는 프로젝트 이름만 있어 커밋해도 된다.
  Machine paths (vault, repositories) live only in `~/.config/vaultos/config`. `.vaultos/link` holds just the project name and is safe to commit.
- `bind`는 `link`로 합쳤다. 개인/회사 구분과 프로필 4종은 `light`/`full` 2종으로 줄였다.
  `bind` is merged into `link`. The personal/company split and four profiles became two: `light` and `full`.

### 공개 판에 없는 것 / Not in the public core

지식 큐레이션, 아침 브리핑, 제품 헬스체크, 일정 등록.
Knowledge curation, morning briefing, product health checks, scheduling.
