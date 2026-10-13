# Contributing / 기여

## 원칙 / Principles

- 표준 라이브러리만 쓴다. 의존성을 늘리지 않는다. / Standard library only. No new dependencies.
- Python 3.9에서 동작한다. / It runs on Python 3.9.
- 사용자 볼트에서는 VaultOS 폴더 밖에 쓰지 않는다. / Never write outside the VaultOS folder in a user's vault.
- 사용자 출력은 `t("한국어", "English")`로 두 언어를 함께 넣는다. / User-facing output passes both languages through `t("한국어", "English")`.
- 문서는 절마다 한국어 다음 영어로 쓴다. 파일 이름은 영문이다. / Documents are written per section, Korean then English. File names are English.
- 프레임워크 파일에 모델 이름을 넣지 않는다. / No model names in framework files.

## 검사 / Checks

```sh
python3 -m unittest discover -s tests -v
python3 tools/e2e.py
```

둘 다 통과해야 한다. E2E는 임시 HOME에서 돌아서 실제 설정과 볼트를 건드리지 않는다.
Both must pass. The end-to-end test runs with a temporary HOME and never touches your real settings or vault.

## 버전 / Versions

`VERSION`과 `CHANGELOG.md`를 같이 고친다. 프레임워크 파일이 바뀌면 사용자는 `vaultos upgrade`로 받는다.
Update `VERSION` and `CHANGELOG.md` together. Users receive framework file changes through `vaultos upgrade`.
