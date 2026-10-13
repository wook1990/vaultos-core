"""Does a repository keep the VaultOS contract?

The goal is to make the state visible, not to block work. A person reads it and stops.

    check(repo, home, link, profile)   repository + vault documents
    check(repo, None, link, profile)   repository only (CI: the vault is not there)

Returns (violations, warnings, facts). A violation makes `vaultos validate` exit 1.
"""

import os
import re

from . import yamlish
from .i18n import t

TRACKER_REQUIRED = ("tasks.yaml", "issues.yaml", "decisions.yaml", "releases.yaml", "progress.md")
TRACKER_OPTIONAL = ("experiments.yaml",)
ENTRYPOINTS = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")
FORBIDDEN_DOCS = ("docs/product-brief.md", "docs/roadmap.md", "docs/architecture.md",
                  "docs/initiative-brief.md", "docs/release-checklist.md")
STATUSES = ("planned", "ready", "in_progress", "blocked", "review", "done", "dropped")
DONE = ("done",)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VAULT_REQUIRED = {
    "light": ("project.yaml",),
    "full": ("project.yaml", "intake/grill.md", "governance/constitution.md", "requirements/requirements.yaml"),
}


def _short(items, n=5):
    return ", ".join(items[:n]) + (" …" if len(items) > n else "")


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def load_tasks(path):
    """Return (tasks, error). tasks is a list of dicts."""
    if not os.path.isfile(path):
        return [], t("tracker/tasks.yaml이 없다 — vaultos link로 만든다", "tracker/tasks.yaml is missing — vaultos link creates it")
    try:
        data = yamlish.load(path)
    except yamlish.YamlError as e:
        return [], str(e)
    tasks = (data or {}).get("tasks") if isinstance(data, dict) else None
    if tasks is None:
        return [], None
    if not isinstance(tasks, list) or not all(isinstance(x, dict) for x in tasks):
        return [], t("tasks는 항목(id, title, …)의 목록이어야 한다", "tasks must be a list of items (id, title, …)")
    return tasks, None


def load_requirement_ids(path):
    """Return (ids, error)."""
    try:
        data = yamlish.load(path)
    except yamlish.YamlError as e:
        return [], str(e)
    reqs = (data or {}).get("requirements") if isinstance(data, dict) else None
    if not isinstance(reqs, list):
        return [], None
    return [str(r.get("id")) for r in reqs if isinstance(r, dict) and r.get("id")], None


def _task_checks(tasks, v, w, facts):
    ids = [str(x.get("id") or "") for x in tasks]
    facts["tasks"] = len(tasks)
    missing_id = sum(1 for i in ids if not i)
    if missing_id:
        v.append(t(f"id가 없는 task {missing_id}개", f"{missing_id} task(s) without an id"))
    dup = sorted({i for i in ids if i and ids.count(i) > 1})
    if dup:
        v.append(t(f"id가 겹치는 task: {_short(dup)}", f"duplicate task ids: {_short(dup)}"))

    unlinked, no_ev, bad_date, no_done_at, bad_status, no_owner, mismatch = [], [], [], [], [], [], []
    try:
        from . import agents
        models = agents.read_models()
        role_tier = {r["name"]: r["tier"] for r in agents.roles()}
    except Exception:  # model audit is a guide; never let it break validation
        models, role_tier = {}, {}
    for task in tasks:
        tid = str(task.get("id") or "?")
        status = str(task.get("status") or "")
        if status not in STATUSES:
            bad_status.append(f"{tid}={status or '∅'}")
        if not [r for r in _as_list(task.get("requirement_ids")) if r]:
            unlinked.append(tid)
        for field in ("started_at", "due", "done_at"):
            val = task.get(field)
            if val is not None and not DATE.match(str(val)):
                bad_date.append(f"{tid}.{field}={val}")
        owner = str(task.get("owner") or "")
        if status in DONE:
            if not [e for e in _as_list(task.get("evidence")) if e]:
                no_ev.append(tid)
            if task.get("done_at") is None:
                no_done_at.append(tid)
            if "@" not in owner:
                no_owner.append(tid)
        role, _, model = owner.partition("@")
        want = role_tier.get(role)
        if want and model and models:
            have = agents.tiers_of(model, models)
            if have and want not in have:
                mismatch.append(f"{tid}({role}@{model}: {want} / {'/'.join(sorted(have))})")

    facts["unlinked"] = len(unlinked)
    if unlinked:
        v.append(t(f"REQ에 연결되지 않은 task {len(unlinked)}개: {_short(unlinked)}",
                   f"{len(unlinked)} task(s) not linked to a requirement: {_short(unlinked)}"))
    if no_ev:
        v.append(t(f"evidence 없이 done인 task {len(no_ev)}개: {_short(no_ev)}",
                   f"{len(no_ev)} done task(s) without evidence: {_short(no_ev)}"))
    if bad_date:
        v.append(t(f"날짜가 YYYY-MM-DD가 아닌 필드 {len(bad_date)}개: {_short(bad_date)}",
                   f"{len(bad_date)} date field(s) not in YYYY-MM-DD: {_short(bad_date)}"))
    if bad_status:
        w.append(t(f"계약에 없는 status {len(bad_status)}개: {_short(bad_status)}",
                   f"{len(bad_status)} unknown status value(s): {_short(bad_status)}"))
    if no_done_at:
        w.append(t(f"done_at 없이 done인 task {len(no_done_at)}개: {_short(no_done_at)}",
                   f"{len(no_done_at)} done task(s) without done_at: {_short(no_done_at)}"))
    if no_owner:
        w.append(t(f"owner(역할@모델) 없이 done인 task {len(no_owner)}개 — 누가 했는지 남지 않는다: {_short(no_owner)}",
                   f"{len(no_owner)} done task(s) without owner (role@model) — who did it is not recorded: {_short(no_owner)}"))
    if mismatch:
        w.append(t(f"등급에 맞지 않는 모델이 한 task {len(mismatch)}개: {_short(mismatch, 3)}",
                   f"{len(mismatch)} task(s) done by a model outside the role's tier: {_short(mismatch, 3)}"))
    return {r for task in tasks for r in _as_list(task.get("requirement_ids")) if r}


def check(repo, home, link, profile="full"):
    v, w, facts = [], [], {}

    # 1) contract surface / 계약 표면
    for name in TRACKER_REQUIRED:
        if not os.path.isfile(os.path.join(repo, "tracker", name)):
            v.append(t(f"tracker 파일 없음: tracker/{name}", f"missing tracker file: tracker/{name}"))
    for name in ENTRYPOINTS:
        if not os.path.isfile(os.path.join(repo, name)):
            w.append(t(f"에이전트 진입점 없음: {name}", f"missing agent entry point: {name}"))
    tdir = os.path.join(repo, "tracker")
    if os.path.isdir(tdir):
        for f in sorted(os.listdir(tdir)):
            if f not in TRACKER_REQUIRED + TRACKER_OPTIONAL and not f.startswith("."):
                w.append(t(f"계약에 없는 tracker 파일: tracker/{f}", f"tracker file outside the contract: tracker/{f}"))
    for rel in FORBIDDEN_DOCS:
        if os.path.isfile(os.path.join(repo, rel)):
            v.append(t(f"의도 문서가 저장소에 있음: {rel} — 볼트에 둔다",
                       f"intent document in the repository: {rel} — it belongs in the vault"))

    # 2) tasks / 태스크
    tpath = os.path.join(repo, "tracker", "tasks.yaml")
    linked = set()
    if os.path.isfile(tpath):
        tasks, err = load_tasks(tpath)
        if err:
            v.append(t(f"tracker/tasks.yaml을 읽을 수 없음 — {err}", f"cannot read tracker/tasks.yaml — {err}"))
        else:
            linked = _task_checks(tasks, v, w, facts)

    if home is None:  # repository only (CI)
        return v, w, facts

    # 3) vault documents / 볼트 문서
    pdir = os.path.join(home, link["project_path"])
    facts["project_dir"] = pdir
    if not os.path.isfile(os.path.join(pdir, "project.yaml")):
        v.append(t(f"볼트에 프로젝트가 없음: {link['project_path']}", f"project not found in the vault: {link['project_path']}"))
        return v, w, facts
    for rel in VAULT_REQUIRED.get(profile, VAULT_REQUIRED["full"]):
        if not os.path.isfile(os.path.join(pdir, rel)):
            v.append(t(f"볼트 계약 문서 없음: {rel}  (profile={profile})", f"missing vault document: {rel}  (profile={profile})"))

    # 4) Grill Gate
    try:
        manifest = yamlish.load(os.path.join(pdir, "project.yaml")) or {}
    except yamlish.YamlError as e:
        v.append(t(f"project.yaml을 읽을 수 없음 — {e}", f"cannot read project.yaml — {e}"))
        manifest = {}
    grill = manifest.get("grill") if isinstance(manifest, dict) else None
    facts["grill"] = grill or "unknown"
    if grill == "pending":
        v.append(t("Grill Gate가 pending이다 — 구현을 시작하지 않는다", "the Grill Gate is pending — do not start implementation"))
    elif grill != "complete":
        w.append(t("Grill Gate를 통과한 적이 없다 — vaultos grill을 먼저 실행한다",
                   "the Grill Gate has never run — run vaultos grill first"))

    # 5) requirements ↔ tasks / 요구사항 ↔ 태스크
    rpath = os.path.join(pdir, "requirements", "requirements.yaml")
    if os.path.isfile(rpath):
        req_ids, err = load_requirement_ids(rpath)
        if err:
            v.append(t(f"requirements.yaml을 읽을 수 없음 — {err}", f"cannot read requirements.yaml — {err}"))
        else:
            facts["requirements"] = len(req_ids)
            unknown = sorted(r for r in linked if r not in req_ids)
            if unknown:
                v.append(t(f"볼트에 없는 REQ를 가리키는 task 연결 {len(unknown)}개: {_short(unknown)}",
                           f"{len(unknown)} task link(s) to a REQ that is not in the vault: {_short(unknown)}"))
            orphan = [r for r in req_ids if r not in linked]
            if orphan:
                w.append(t(f"task로 이어지지 않은 REQ {len(orphan)}개: {_short(orphan)}",
                           f"{len(orphan)} requirement(s) without a task: {_short(orphan)}"))
    return v, w, facts
