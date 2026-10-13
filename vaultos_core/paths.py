"""Where things live.

    <your vault>/                 any folder you already use (an Obsidian vault, a synced folder, ...)
      <folder>/                   VaultOS writes only here (default: VaultOS)
        system/                   VAULTOS.md, schemas, templates, upgrade base
        governance/               shared contracts
        projects/<slug>/          intent documents of one project
        archive/backups/          previous copies made by upgrade

    ~/.config/vaultos/config      this machine only: vault, folder, workspace_root, lang,
                                  repo.<slug> (local repo path), model.<tool>.<tier>
    <repo>/.vaultos/link          project slug only — no machine paths, safe to commit
"""

import os
import re

DEFAULT_FOLDER = "VaultOS"
SYSTEM, GOVERNANCE, PROJECTS, ARCHIVE = "system", "governance", "projects", "archive"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


# ---------------------------------------------------------------- machine config

def config_path():
    return os.path.join(os.path.expanduser("~"), ".config", "vaultos", "config")


def read_config():
    out = {}
    try:
        with open(config_path(), encoding="utf-8") as fh:
            for line in fh:
                if ":" in line and not line.lstrip().startswith("#"):
                    k, v = line.split(":", 1)
                    out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def set_config(**values):
    """Replace only the given keys. Other lines stay as they are. A value of None removes the key."""
    path = config_path()
    lines = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    for key, val in values.items():
        lines = [ln for ln in lines if not ln.startswith(f"{key}:")]
        if val is not None:
            lines.append(f"{key}: {val}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def expand(path):
    return os.path.abspath(os.path.expanduser(path)) if path else path


# ---------------------------------------------------------------- vault home

def is_home(path):
    return bool(path) and os.path.isfile(os.path.join(path, SYSTEM, "VAULTOS.md"))


def find_home(vault=None, folder=None):
    """Return (vault, home) or (None, None).

    Order: --vault argument, VAULTOS_VAULT, ~/.config/vaultos/config. No guessing, no disk search.
    The argument may point at the vault or straight at the VaultOS folder inside it.
    """
    cfg = read_config()
    seen = None
    for candidate in (vault, os.environ.get("VAULTOS_VAULT"), cfg.get("vault")):
        if not candidate:
            continue
        seen = seen or expand(candidate)
        v = expand(candidate)
        if is_home(v):
            return os.path.dirname(v), v
        home = os.path.join(v, folder or os.environ.get("VAULTOS_FOLDER") or cfg.get("folder") or DEFAULT_FOLDER)
        if is_home(home):
            return v, home
        if candidate is vault:  # an explicit argument that is wrong must not fall through silently
            return v, None
    return seen, None


def workspace_root():
    cfg = read_config()
    return expand(os.environ.get("VAULTOS_WORKSPACE") or cfg.get("workspace_root") or "~/workspace")


# ---------------------------------------------------------------- projects

def projects(home):
    base = os.path.join(home, PROJECTS)
    out = []
    if os.path.isdir(base):
        for slug in sorted(os.listdir(base)):
            d = os.path.join(base, slug)
            if os.path.isfile(os.path.join(d, "project.yaml")):
                out.append((slug, d))
    return out


def project_dir(home, slug):
    return os.path.join(home, PROJECTS, slug)


def repo_path(slug):
    """This machine's local repo for a project, from the machine config."""
    p = read_config().get(f"repo.{slug}")
    return expand(p) if p else None


def set_repo_path(slug, path):
    set_config(**{f"repo.{slug}": path})


# ---------------------------------------------------------------- repo link

def read_link(repo):
    p = os.path.join(repo, ".vaultos", "link")
    if not os.path.isfile(p):
        return None
    out = {}
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out if out.get("project") else None


def find_repo_root(start=None):
    """Walk up from start to the folder that holds .vaultos/link."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(d, ".vaultos", "link")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
