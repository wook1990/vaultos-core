"""vaultos upgrade — bring the framework files in your VaultOS folder to this version.

A 3-way comparison. The base is system/.base/ (a copy of what the previous version shipped),
so no git history is needed.

    yours == new                 nothing to do
    yours == base                you did not edit it -> replace (previous copy backed up)
    yours != base                you edited it -> 3-way merge with `git merge-file`.
                                 Overlapping edits: your file stays, the new one is written
                                 next to it as <file>.vaultos-new
    listed in upgrade-keep.txt   yours — never changed
    missing, not in base         new file -> added
    missing, in base             you deleted it -> not recreated

Backups: archive/backups/upgrade-<time>/
"""

import os
import shutil
import subprocess
import tempfile
from datetime import datetime

from . import FRAMEWORK, version
from .home import BASE, read_version, shipped_files, write_version
from .i18n import t
from .paths import ARCHIVE, SYSTEM

KEEP_FILE = os.path.join(SYSTEM, "upgrade-keep.txt")


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def read_keep(home):
    p = os.path.join(home, KEEP_FILE)
    if not os.path.isfile(p):
        return set()
    out = set()
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            s = line.split("#")[0].strip()
            if s:
                out.add(s.replace("\\", "/"))
    return out


def merge3(cur, base, new):
    """Return (merged text, clean). Without git, nothing merges cleanly."""
    if shutil.which("git") is None:
        return cur, False
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, text in (("cur", cur), ("base", base), ("new", new)):
            p = os.path.join(tmp, name)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            paths.append(p)
        r = subprocess.run(["git", "merge-file", "-p", *paths], capture_output=True)
        return r.stdout.decode("utf-8", errors="replace"), r.returncode == 0


def plan(home):
    keep = read_keep(home)
    items = []
    for rel in shipped_files():
        new = _read(os.path.join(FRAMEWORK, rel))
        dst = os.path.join(home, rel)
        base_p = os.path.join(home, BASE, rel)
        base = _read(base_p) if os.path.isfile(base_p) else None
        if rel in keep:
            if os.path.isfile(dst) and _read(dst) != new:
                items.append(("keep", rel, None))
            continue
        if not os.path.exists(dst):
            items.append(("deleted" if base is not None else "add", rel, None if base is not None else new))
            continue
        cur = _read(dst)
        if cur == new:
            items.append(("same", rel, None))
        elif base is not None and cur == base:
            items.append(("replace", rel, new))
        elif base is None:
            items.append(("conflict", rel, new))
        else:
            merged, clean = merge3(cur, base, new)
            items.append(("merge", rel, merged) if clean else ("conflict", rel, new))
    return items


LABEL = {
    "add": ("추가", "add"), "replace": ("교체", "replace"), "merge": ("자동 병합", "merge"),
    "conflict": ("충돌 — 새 판을 .vaultos-new로", "conflict — new copy as .vaultos-new"),
    "keep": ("보존 (upgrade-keep)", "kept (upgrade-keep)"), "deleted": ("사용자가 지움 — 다시 만들지 않음", "deleted by you — not recreated"),
}


def run(home, dry_run=False):
    have = read_version(home).get("framework_version", "?")
    want = version()
    items = plan(home)
    counts = {}
    for kind, _rel, _c in items:
        counts[kind] = counts.get(kind, 0) + 1
    print(f"VaultOS {have} -> {want}")
    print("  " + " · ".join(f"{t(*LABEL[k]) if k in LABEL else k} {n}" for k, n in sorted(counts.items()) if k != "same"))
    for kind, rel, _c in items:
        if kind not in ("same",):
            print(f"    {t(*LABEL[kind]):12} {rel}")
    if dry_run:
        print(t("\n(dry-run — 아무것도 쓰지 않았다)", "\n(dry-run — nothing written)"))
        return 0

    backup = os.path.join(home, ARCHIVE, "backups", "upgrade-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    for kind, rel, content in items:
        dst = os.path.join(home, rel)
        if kind in ("replace", "merge"):
            b = os.path.join(backup, rel)
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copyfile(dst, b)
        if kind in ("add", "replace", "merge"):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(content)
        elif kind == "conflict":
            with open(dst + ".vaultos-new", "w", encoding="utf-8") as fh:
                fh.write(content)
    # the new base is what this version ships
    base_root = os.path.join(home, BASE)
    shipped = set(shipped_files())
    for rel in shipped:
        b = os.path.join(base_root, rel)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.copyfile(os.path.join(FRAMEWORK, rel), b)
    for dirpath, _d, files in os.walk(base_root):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), base_root).replace(os.sep, "/")
            if rel not in shipped:
                os.remove(os.path.join(dirpath, fn))
    write_version(home, read_version(home).get("lang", "en"))
    print(t(f"\n{want}로 맞췄다.", f"\nUpdated to {want}.")
          + (t(f" 이전 판: {os.path.relpath(backup, home)}", f" Previous copies: {os.path.relpath(backup, home)}")
             if os.path.isdir(backup) else ""))
    if counts.get("conflict"):
        print(t("  .vaultos-new 파일을 열어 직접 합친 뒤 지운다.", "  Open each .vaultos-new file, merge by hand, then delete it."))
    return 0
