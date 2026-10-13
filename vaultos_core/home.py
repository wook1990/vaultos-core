"""Create the VaultOS folder inside the user's vault.

Rules:
- The vault must already exist. VaultOS does not create or adopt a vault root.
- VaultOS writes only inside <vault>/<folder>/. The vault root, its other notes and
  .obsidian/ are never written.
- A copy of every shipped framework file goes to system/.base/ so that `upgrade`
  can do a 3-way merge without git history.
"""

import os
import shutil
from datetime import date

from . import FRAMEWORK, version
from .i18n import t
from .paths import ARCHIVE, GOVERNANCE, PROJECTS, SYSTEM, is_home

SHIPPED = (SYSTEM, GOVERNANCE)
BASE = os.path.join(SYSTEM, ".base")


def shipped_files():
    """Relative paths (with /) of framework files copied into a home."""
    out = []
    for top in SHIPPED:
        for dirpath, dirnames, files in os.walk(os.path.join(FRAMEWORK, top)):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for fn in sorted(files):
                rel = os.path.relpath(os.path.join(dirpath, fn), FRAMEWORK)
                out.append(rel.replace(os.sep, "/"))
    return out


def check_vault(vault):
    """Return an error message, or None if the path can hold a VaultOS folder."""
    if not vault:
        return t("볼트 경로를 입력해야 합니다", "A vault path is required")
    if not os.path.isdir(vault):
        return t(f"볼트 폴더가 없습니다: {vault}  (먼저 볼트를 만들거나 경로를 확인하세요)",
                 f"Vault folder not found: {vault}  (create the vault first or check the path)")
    if not os.access(vault, os.W_OK):
        return t(f"볼트에 쓸 수 없습니다: {vault}", f"Vault is not writable: {vault}")
    return None


def write_version(home, lang):
    with open(os.path.join(home, SYSTEM, "version.yaml"), "w", encoding="utf-8") as fh:
        fh.write("# Written by vaultos init / upgrade. Do not edit. / 직접 고치지 않는다.\n"
                 f"framework_version: {version()}\nlang: {lang}\n")


def read_version(home):
    p = os.path.join(home, SYSTEM, "version.yaml")
    out = {}
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    out[k.strip()] = v.strip()
    return out


def create(vault, folder, lang):
    """Create <vault>/<folder>. Returns (home, created relative paths). Raises ValueError."""
    err = check_vault(vault)
    if err:
        raise ValueError(err)
    if not folder or folder in (".", "..") or os.sep in folder or (os.altsep and os.altsep in folder):
        raise ValueError(t(f"폴더 이름이 올바르지 않습니다: {folder!r}", f"Invalid folder name: {folder!r}"))
    home = os.path.join(vault, folder)
    if is_home(home):
        raise ValueError(t(f"이미 VaultOS 폴더가 있습니다: {home}  (갱신은 vaultos upgrade)",
                           f"VaultOS is already here: {home}  (use vaultos upgrade to update)"))
    if os.path.exists(home) and (not os.path.isdir(home) or os.listdir(home)):
        raise ValueError(t(f"이 이름의 폴더에 이미 다른 파일이 있습니다: {home}  (다른 폴더 이름을 고르세요)",
                           f"A folder with other files already exists: {home}  (choose another folder name)"))

    created = []
    for rel in shipped_files():
        src = os.path.join(FRAMEWORK, rel)
        for dst in (os.path.join(home, rel), os.path.join(home, BASE, rel)):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        created.append(rel)
    for d in (PROJECTS, os.path.join(ARCHIVE, "backups")):
        os.makedirs(os.path.join(home, d), exist_ok=True)
    with open(os.path.join(home, SYSTEM, "upgrade-keep.txt"), "w", encoding="utf-8") as fh:
        fh.write("# Files listed here belong to you. `vaultos upgrade` never changes them.\n"
                 "# 여기 적은 파일은 사용자 것이다. vaultos upgrade가 바꾸지 않는다.\n"
                 "# One path per line, relative to this VaultOS folder. e.g. governance/agent-policy.md\n")
    write_version(home, lang)
    return home, created


def today():
    return date.today().isoformat()
