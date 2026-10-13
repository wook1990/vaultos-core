"""vaultos doctor — read-only check of this machine.

    1 version and CLI   2 vault   3 agent rules   4 rule links   5 secrets   6 models (info only)
"""

import errno
import importlib.util
import os
import re
import subprocess

from . import ROOT, version
from .home import read_version
from .i18n import t
from .paths import config_path, find_home, projects, read_config, repo_path

TOKEN = re.compile(r"(ghp_|gho_|ghs_|github_pat_|glpat-|xox[bpa]-)[A-Za-z0-9_\-]{10,}")


class Report:
    def __init__(self):
        self.fail = self.warn = 0

    def section(self, title):
        print(f"\n{title}")

    def ok(self, msg):
        print(f"  [OK]   {msg}")

    def info(self, msg):
        print(f"  [INFO] {msg}")

    def bad(self, msg, fix=None):
        self.fail += 1
        print(f"  [FAIL] {msg}" + (f"\n         -> {fix}" if fix else ""))

    def note(self, msg, fix=None):
        self.warn += 1
        print(f"  [WARN] {msg}" + (f"\n         -> {fix}" if fix else ""))


def _installer():
    spec = importlib.util.spec_from_file_location("vaultos_install", os.path.join(ROOT, "install.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_version(r):
    r.section(t("1. 버전과 CLI", "1. Version and CLI"))
    r.ok(f"VaultOS {version()}  ({ROOT})")
    link = os.path.join(os.path.expanduser("~"), ".local", "bin", "vaultos")
    if os.path.islink(link) and os.path.realpath(link) == os.path.realpath(os.path.join(ROOT, "vaultos")):
        r.ok(f"~/.local/bin/vaultos -> {ROOT}")
    elif os.name != "nt":
        r.note(t("~/.local/bin/vaultos가 이 설치를 가리키지 않는다", "~/.local/bin/vaultos does not point at this install"),
               "python3 install.py")


def check_vault(r, vault_arg):
    r.section(t("2. 볼트", "2. Vault"))
    cfg = read_config()
    vault, home = find_home(vault_arg)
    if not vault:
        r.bad(t("볼트가 설정되지 않았다", "No vault is configured"), "vaultos init")
        return None
    try:
        os.listdir(vault)
    except OSError as e:
        hint = t("드라이브나 동기화 폴더가 마운트돼 있는지 확인한다", "check that the drive or sync folder is mounted") \
            if e.errno in (errno.ENODEV, errno.EIO, errno.ENOTCONN) else None
        r.bad(t(f"볼트에 접근할 수 없다: {vault} ({e.strerror})", f"Cannot open the vault: {vault} ({e.strerror})"), hint)
        return None
    if not home:
        r.bad(t(f"볼트 안에 VaultOS 폴더가 없다: {vault}", f"No VaultOS folder inside the vault: {vault}"), "vaultos init")
        return None
    r.ok(t(f"볼트 {vault}", f"vault {vault}"))
    r.ok(t(f"VaultOS 폴더 {home}", f"VaultOS folder {home}"))
    have = read_version(home).get("framework_version")
    if have != version():
        r.note(t(f"VaultOS 폴더 버전 {have} ≠ 설치 버전 {version()}", f"VaultOS folder is {have}, install is {version()}"),
               "vaultos upgrade")
    leftovers = []
    for dirpath, _d, files in os.walk(home):
        leftovers += [os.path.relpath(os.path.join(dirpath, f), home) for f in files if f.endswith(".vaultos-new")]
    if leftovers:
        r.note(t(f"합치지 않은 .vaultos-new 파일 {len(leftovers)}개", f"{len(leftovers)} unmerged .vaultos-new file(s)"),
               leftovers[0])
    if not cfg.get("workspace_root"):
        r.info(t("workspace_root 미설정 — 기본값 ~/workspace", "workspace_root not set — default ~/workspace"))
    return home


def check_rules(r):
    inst = _installer()
    r.section(t("3. 에이전트 규칙", "3. Agent rules"))
    dst = inst.rules_dst()
    if not os.path.isfile(dst):
        r.note(t("~/.agents/rules/vaultos.md가 없다", "~/.agents/rules/vaultos.md is missing"), "python3 install.py")
    elif not inst._same(inst.RULES_SRC, dst):
        r.note(t("~/.agents/rules/vaultos.md가 이 판과 다르다", "~/.agents/rules/vaultos.md differs from this version"),
               "python3 install.py")
    else:
        r.ok("~/.agents/rules/vaultos.md")
    r.section(t("4. 규칙 연결", "4. Rule links"))
    found = False
    for label, path, line in inst.entry_files():
        found = True
        if not os.path.isfile(path):
            r.note(t(f"{label}: {path}가 없다", f"{label}: {path} is missing"), "python3 install.py")
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            if "vaultos.md" in fh.read():
                r.ok(f"{label}: {path.replace(os.path.expanduser('~'), '~')} -> vaultos.md")
            else:
                r.note(t(f"{label}: 규칙 파일이 vaultos.md를 가리키지 않는다", f"{label}: rule file does not point at vaultos.md"),
                       t(f"한 줄 추가: {line}", f"add one line: {line}"))
    if not found:
        r.info(t("에이전트 도구가 없다 (~/.claude, ~/.codex)", "No agent tool found (~/.claude, ~/.codex)"))


def check_secrets(r, home):
    r.section(t("5. 비밀값", "5. Secrets"))
    leaks = []
    for slug, _d in projects(home) if home else []:
        repo = repo_path(slug)
        if not repo or not os.path.isdir(repo):
            continue
        try:
            out = subprocess.run(["git", "remote", "-v"], cwd=repo, capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        if TOKEN.search(out):
            leaks.append(repo)
    if os.path.isfile(config_path()):
        with open(config_path(), encoding="utf-8", errors="replace") as fh:
            if TOKEN.search(fh.read()):
                leaks.append(config_path())
    for p in leaks:
        r.bad(t(f"토큰이 들어 있다: {p}", f"Token found: {p}"),
              t("토큰을 폐기하고 remote URL에서 뺀다", "revoke the token and remove it from the remote URL"))
    if not leaks:
        r.ok(t("연결된 저장소의 remote URL과 설정에 토큰 없음", "No token in linked repo remotes or the config"))


def check_models(r):
    from . import agents
    r.section(t("6. 모델 배정 (가이드 — WARN을 내지 않는다)", "6. Model tiers (a guide — never a warning)"))
    models = agents.read_models()
    tools = list(agents.installed_tools())
    if not tools:
        r.info(t("에이전트 도구가 없다", "No agent tool found"))
        return
    for tool, label in tools:
        missing = [x for x in agents.TIERS if (tool, x) not in models]
        if missing:
            r.info(t(f"{label}: 매핑 없는 등급 {', '.join(missing)}", f"{label}: no model for {', '.join(missing)}"))
        else:
            r.ok(f"{label}: " + " · ".join(f"{x}={models[(tool, x)][0]}" for x in agents.TIERS))


def run(vault_arg=None):
    r = Report()
    print("VaultOS doctor")
    check_version(r)
    home = check_vault(r, vault_arg)
    check_rules(r)
    check_secrets(r, home)
    check_models(r)
    print(f"\n{t('결과', 'Result')}  FAIL {r.fail} / WARN {r.warn}")
    return 1 if r.fail else 0
