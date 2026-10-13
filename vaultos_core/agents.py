"""Model tiers for agent work — a guide, not a rule.

The framework ships tiers and role templates only, never model names. Which model
serves which tier is a per-machine setting. Your own agent setup always comes first:
a role file without the vaultos:managed marker is yours and is never overwritten.

    vaultos agents                                   tiers, mapping, role agents
    vaultos agents set <tool> <tier> <model> [--effort E]
    vaultos agents sync [--dry-run]                  create Claude Code / Codex role agents

Config line: model.<tool>.<tier>: <model> [effort]
"""

import os
import re
import shutil
from datetime import datetime

from . import FRAMEWORK
from .i18n import t
from .paths import config_path, set_config

ROLES_DIR = os.path.join(FRAMEWORK, "harness", "roles")
MARK = "vaultos:managed"
TIERS = ("high", "bulk", "fast")
TIER_USE = {
    "high": ("기획, PRD, 설계, 리뷰 — 판단이 결과를 정하는 일", "planning, PRD, design, review — judgment decides the result"),
    "bulk": ("구현, 리서치, 대량 처리 — 양이 많은 일", "implementation, research, bulk work — volume"),
    "fast": ("명세가 닫힌 작은 수정", "small edits with a closed spec"),
}
# tool: (label, home dir, agents dir, extension)
TOOLS = {
    "claude": ("Claude Code", ".claude", "agents", ".md"),
    "codex": ("Codex", ".codex", "agents", ".toml"),
}


def _home():
    return os.path.expanduser("~")


def roles(roles_dir=ROLES_DIR):
    """Role templates: frontmatter (name, tier, description, tools, readonly) + body."""
    out = []
    for fn in sorted(os.listdir(roles_dir)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(roles_dir, fn), encoding="utf-8") as fh:
            text = fh.read()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not m:
            continue
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        meta["body"] = m.group(2).strip()
        meta["readonly"] = meta.get("readonly") == "true"
        out.append(meta)
    return out


def read_models(path=None):
    """{(tool, tier): (model, effort or "")}"""
    models = {}
    try:
        with open(path or config_path(), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^model\.([a-z]+)\.([a-z]+):\s*(\S+)(?:\s+(\S+))?\s*$", line)
                if m:
                    models[(m.group(1), m.group(2))] = (m.group(3), m.group(4) or "")
    except OSError:
        pass
    return models


def tiers_of(model, models):
    return {tier for (_tool, tier), (mod, _e) in models.items() if mod == model}


def installed_tools():
    for key, (label, home_dir, _sub, _ext) in TOOLS.items():
        if os.path.isdir(os.path.join(_home(), home_dir)):
            yield key, label


def agent_path(tool, name):
    _label, home_dir, sub, ext = TOOLS[tool]
    return os.path.join(_home(), home_dir, sub, name + ext)


def is_managed(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return MARK in fh.read()
    except OSError:
        return False


def _footer(owner):
    return ("VaultOS-bound repo: follow the work cycle in `~/.agents/rules/vaultos.md`.\n"
            f"Write `owner: {owner}` on the task you work on.\n"
            "VaultOS 연결 저장소에서는 `~/.agents/rules/vaultos.md`의 작업 사이클을 따른다.\n"
            f"작업하는 task에 `owner: {owner}`를 쓴다.")


def render(tool, role, model, effort):
    owner = f"{role['name']}@{model}"
    body = role["body"] + "\n\n" + _footer(owner)
    note = f"{MARK} — created by `vaultos agents sync`. Edit the role template or the model mapping instead."
    if tool == "claude":
        lines = ["---", f"name: {role['name']}", f"description: {role['description']}", f"model: {model}"]
        if effort:
            lines.append(f"effort: {effort}")
        if role.get("tools"):
            lines.append(f"tools: {role['tools']}")
        return "\n".join(lines + ["---", "", f"<!-- {note} -->", "", body, ""])
    esc = body.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    desc = role["description"].replace("\\", "\\\\").replace('"', '\\"')
    lines = [f"# {note}", f'name = "{role["name"]}"', f'description = "{desc}"', f'model = "{model}"']
    if effort:
        lines.append(f'model_reasoning_effort = "{effort}"')
    if role["readonly"]:
        lines.append('sandbox_mode = "read-only"')
    return "\n".join(lines + [f'developer_instructions = """\n{esc}\n"""', ""])


def plan(models=None, roles_dir=ROLES_DIR):
    """[(tool, role, path, state, content)] — state: new / update / same / user / unmapped"""
    models = read_models() if models is None else models
    out = []
    for tool, _label in installed_tools():
        for role in roles(roles_dir):
            path = agent_path(tool, role["name"])
            mapped = models.get((tool, role["tier"]))
            if os.path.lexists(path) and not is_managed(path):
                out.append((tool, role, path, "user", None))
                continue
            if not mapped:
                out.append((tool, role, path, "unmapped", None))
                continue
            content = render(tool, role, *mapped)
            if not os.path.lexists(path):
                state = "new"
            else:
                with open(path, encoding="utf-8") as fh:
                    state = "same" if fh.read() == content else "update"
            out.append((tool, role, path, state, content))
    return out


def _short(path):
    return path.replace(_home(), "~")


LABELS = {
    "new": ("만들 것", "to create"),
    "update": ("갱신할 것", "to update"),
    "same": ("최신", "up to date"),
    "user": ("개인 설정 — VaultOS가 관리하지 않음", "your own file — not managed by VaultOS"),
    "unmapped": ("등급 매핑 없음 — 만들지 않음", "no model for this tier — not created"),
}


def show(models=None):
    models = read_models() if models is None else models
    tools = list(installed_tools())
    print(t("등급 (가이드 — 개인 설정이 먼저다)", "Tiers (a guide — your own setup comes first)"))
    for tier in TIERS:
        print(f"  {tier:5} {t(*TIER_USE[tier])}")
    if not tools:
        print("\n" + t("에이전트 도구가 없다 (~/.claude, ~/.codex)", "No agent tool found (~/.claude, ~/.codex)"))
        return 0
    print("\n" + t("이 기기의 모델 매핑", "Model mapping on this machine") + f"  ({_short(config_path())})")
    for tool, label in tools:
        cells = []
        for tier in TIERS:
            m = models.get((tool, tier))
            cells.append(f"{tier}={m[0]}{' ' + m[1] if m and m[1] else ''}" if m else f"{tier}=-")
        print(f"  {label:12} " + " · ".join(cells))
    print("\n" + t("역할 에이전트", "Role agents"))
    for tool, role, _path, state, _c in plan(models):
        m = models.get((tool, role["tier"]))
        who = f"{role['name']}@{m[0]}" if m and state != "user" else role["name"]
        print(f"  {TOOLS[tool][0]:12} {who:34} [{role['tier']}]  {t(*LABELS[state])}")
    missing = [(tl, tier) for tl, _l in tools for tier in TIERS if (tl, tier) not in models]
    if missing:
        tl, tier = missing[0]
        print("\n" + t("매핑 넣기", "Set a model") + f":  vaultos agents set {tl} {tier} <model> [--effort <level>]")
    print(t("만들기", "Create") + ":     vaultos agents sync")
    return 0


def set_model(tool, tier, model, effort=None):
    if tool not in TOOLS:
        print(t(f"도구는 {', '.join(TOOLS)} 중 하나다: {tool}", f"tool must be one of {', '.join(TOOLS)}: {tool}"))
        return 2
    if tier not in TIERS:
        print(t(f"등급은 {', '.join(TIERS)} 중 하나다: {tier}", f"tier must be one of {', '.join(TIERS)}: {tier}"))
        return 2
    if not re.match(r"^[A-Za-z0-9._:/-]+$", model) or (effort and not re.match(r"^[a-z]+$", effort)):
        print(t("모델 이름과 effort에는 공백이나 특수문자를 넣지 않는다", "model and effort must not contain spaces or symbols"))
        return 2
    set_config(**{f"model.{tool}.{tier}": model + (f" {effort}" if effort else "")})
    print(f"{TOOLS[tool][0]} {tier} = {model}{' ' + effort if effort else ''}")
    print(t("에이전트에 반영: vaultos agents sync", "Apply to agents: vaultos agents sync"))
    return 0


def sync(dry_run=False):
    items = plan()
    if not items:
        print(t("에이전트 도구가 없다 (~/.claude, ~/.codex). 만들 것이 없다.", "No agent tool found (~/.claude, ~/.codex). Nothing to do."))
        return 0
    backup = os.path.join(_home(), ".agents", "backups", "vaultos-agents-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    counts = {}
    for tool, role, path, state, content in items:
        counts[state] = counts.get(state, 0) + 1
        if state == "user":
            print(f"  {t('그대로 둠', 'kept'):8} {_short(path)} ({t('개인 설정', 'your own file')})")
        elif state == "unmapped":
            print(f"  {t('건너뜀', 'skipped'):8} {TOOLS[tool][0]} {role['name']} ({t('등급 매핑 없음', 'no model for tier')} {role['tier']})")
        elif state in ("new", "update"):
            print(f"  {t('만듦', 'created') if state == 'new' else t('갱신', 'updated'):8} {_short(path)}")
            if dry_run:
                continue
            if state == "update":
                b = os.path.join(backup, os.path.relpath(path, _home()))
                os.makedirs(os.path.dirname(b), exist_ok=True)
                shutil.copyfile(path, b)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
    print("\n" + " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          + (t("  (dry-run — 아무것도 쓰지 않았다)", "  (dry-run — nothing written)") if dry_run else ""))
    return 0
