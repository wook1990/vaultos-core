#!/usr/bin/env python3
"""Install the VaultOS CLI and agent rules on this machine.

    python3 install.py            link ~/.local/bin/vaultos, install ~/.agents/rules/vaultos.md
    python3 install.py --check    show what would change, write nothing

It never touches your vault. Create the VaultOS folder inside your vault with `vaultos init`.
Existing agent rule files (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md) are never edited:
VaultOS creates one only when it is missing, otherwise it prints the line to add.
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)

from vaultos_core.i18n import set_lang, t  # noqa: E402

RULES_SRC = os.path.join(HERE, "framework", "harness", "rules", "vaultos.md")
RULES_REL = os.path.join("rules", "vaultos.md")
# (label, home dir, rule file, line that points at vaultos.md)
TOOLS = (
    ("Claude Code", ".claude", "CLAUDE.md", "@~/.agents/rules/vaultos.md"),
    ("Codex", ".codex", "AGENTS.md", "- VaultOS: read and follow ~/.agents/rules/vaultos.md first."),
)


def home():
    return os.path.expanduser("~")


def rules_dst():
    return os.path.join(home(), ".agents", RULES_REL)


def entry_files():
    """(label, rule file path, line) for each agent tool installed on this machine."""
    for label, d, fn, line in TOOLS:
        if os.path.isdir(os.path.join(home(), d)):
            yield label, os.path.join(home(), d, fn), line


def _same(a, b):
    try:
        with open(a, "rb") as x, open(b, "rb") as y:
            return x.read() == y.read()
    except OSError:
        return False


def install(check=False):
    done, hints = [], []
    bindir = os.path.join(home(), ".local", "bin")
    link = os.path.join(bindir, "vaultos")
    target = os.path.join(HERE, "vaultos")
    if os.name == "nt":
        hints.append(t("Windows: WSL에서 실행하거나 `python vaultos <명령>`으로 실행한다",
                       "Windows: use WSL, or run `python vaultos <command>`"))
    elif not (os.path.islink(link) and os.path.realpath(link) == os.path.realpath(target)):
        if os.path.exists(link) and not os.path.islink(link):
            hints.append(t(f"{link}가 이미 있어 링크하지 않았다", f"{link} exists and is not a link — left as is"))
        else:
            done.append(t(f"CLI 링크 {link}", f"CLI link {link}"))
            if not check:
                os.makedirs(bindir, exist_ok=True)
                if os.path.islink(link):
                    os.unlink(link)
                os.symlink(target, link)
        if bindir not in os.environ.get("PATH", "").split(os.pathsep):
            hints.append(t(f"PATH에 {bindir}를 넣는다", f"add {bindir} to PATH"))

    dst = rules_dst()
    if not _same(RULES_SRC, dst):
        if os.path.exists(dst):
            backup = os.path.join(home(), ".agents", "backups", "vaultos-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
            done.append(t(f"규칙 교체 ~/.agents/{RULES_REL} (이전 판 {backup})", f"rules updated ~/.agents/{RULES_REL} (previous copy {backup})"))
            if not check:
                os.makedirs(os.path.join(backup, "rules"), exist_ok=True)
                shutil.copyfile(dst, os.path.join(backup, RULES_REL))
        else:
            done.append(t(f"규칙 설치 ~/.agents/{RULES_REL}", f"rules installed ~/.agents/{RULES_REL}"))
        if not check:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(RULES_SRC, dst)

    for label, path, line in entry_files():
        if not os.path.lexists(path):
            done.append(t(f"{label}: {path} 생성 (vaultos.md를 가리키는 한 줄)", f"{label}: created {path} (one line pointing at vaultos.md)"))
            if not check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(line + "\n")
        else:
            with open(path, encoding="utf-8", errors="replace") as fh:
                if "vaultos.md" not in fh.read():
                    hints.append(t(f"{label}: {path}에 이 줄을 넣는다 → {line}", f"{label}: add this line to {path} → {line}"))

    print(t("VaultOS 설치", "VaultOS install") + (t(" (확인만)", " (check only)") if check else ""))
    for d in done or [t("바뀐 것 없음", "nothing to change")]:
        print(f"  {d}")
    for h in hints:
        print(f"  ! {h}")
    print(t("\n다음: vaultos init  (볼트 안에 VaultOS 폴더를 만든다)", "\nNext: vaultos init  (creates the VaultOS folder inside your vault)"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Install the VaultOS CLI and agent rules / VaultOS CLI와 에이전트 규칙 설치")
    ap.add_argument("--check", action="store_true", help="show changes only / 바뀔 것만 보여 준다")
    ap.add_argument("--lang", choices=("ko", "en"), help="output language / 출력 언어")
    args = ap.parse_args(argv)
    if args.lang:
        set_lang(args.lang)
    return install(check=args.check)


if __name__ == "__main__":
    sys.exit(main())
