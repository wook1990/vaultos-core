"""Grill Gate — question the project before building it.

1. Do not start from "build me this". Collect sources first and question from them.
2. If documents exist, do not start from a bare idea. Take answers from the documents
   and ask a person only for what is missing.

Success criteria are part of the requirements, not a later QA add-on.

Outputs (inside the project folder of the vault, plus the repo tracker):

    intake/sources.md               sources, candidate facts, assumptions, open questions
    intake/grill.md                 questions and answers, gate status
    governance/constitution.md      mission, non-goals, constraints
    requirements/requirements.yaml  REQ + acceptance + verification
    status/timeline.md              phases and a mermaid gantt
    <repo>/tracker/tasks.yaml       task slices (only when the tracker has no tasks yet)
"""

import os
import re
import unicodedata
from datetime import date, timedelta

from .i18n import t
from .yamlish import quote

# (key, Korean question, English question, required)
QUESTIONS = (
    ("outcome", "이 프로젝트가 끝나면 무엇이 달라져 있어야 합니까?", "When this project is done, what is different?", True),
    ("problem", "지금 무엇이 문제입니까? 누가 불편합니까?", "What is the problem now? Who has it?", True),
    ("users", "누가 씁니까?", "Who uses it?", False),
    ("non_goals", "이번에 하지 않기로 할 것은? (쉼표로 구분)", "What will you NOT do this time? (comma-separated)", True),
    ("features", "핵심 기능 1~3개는? (쉼표로 구분)", "The 1-3 core features? (comma-separated)", True),
    ("success", "무엇이 측정되면 성공입니까? (판정 가능한 문장)", "What measurement means success? (a checkable sentence)", True),
    ("verification", "그것을 어떻게 검증합니까? (테스트, 수동 확인, 지표)", "How do you verify it? (tests, manual check, metric)", True),
    ("surfaces", "영향받는 영역은? (예: API, 화면, 데이터 스키마)", "Which areas change? (e.g. API, screens, data schema)", False),
    ("constraints", "바꿀 수 없는 제약은? (기술, 일정, 비용, 규제)", "Constraints you cannot change? (tech, time, cost, regulation)", False),
    ("vocabulary", "이 프로젝트에서만 특별한 뜻을 갖는 용어는?", "Terms with a special meaning in this project?", False),
    ("approval", "사람 승인이 반드시 필요한 지점은?", "Where must a person approve?", False),
    ("stop", "언제 멈춥니까? (더 다듬고 싶어도 그만둘 조건)", "When do you stop? (the point where you stop polishing)", True),
)

PHASES = (
    ("intake", "소스 수집과 Grill", "Sources and Grill", 2),
    ("spec", "요구사항 확정", "Requirements", 3),
    ("build", "구현", "Build", 10),
    ("verify", "검증", "Verify", 3),
    ("release", "릴리스 판단", "Release decision", 1),
)

# A task slice per feature: (phase, Korean suffix, English suffix, role)
SLICES = (
    ("spec", "요구사항 확정", "requirements", "planner"),
    ("build", "구현", "build", "implementer"),
    ("verify", "검증", "verify", "reviewer"),
)

PLAN_NAMES = ("plan", "planning", "prd", "기획문서", "기획서")
REQ_NAMES = ("requirements", "requirement", "요구사항정의서", "요구사항")
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".venv", "venv", "templates", "tracker"}

SECTION_KEYS = (
    ("problem", r"문제|배경|problem|background"),
    ("outcome", r"목표|목적|goal|objective|vision|outcome"),
    ("users", r"사용자|대상|페르소나|users?|persona"),
    ("non_goals", r"제외|비목표|하지 않|non.?goals?|out of scope"),
    ("success", r"성공|지표|kpi|success|metric"),
    ("verification", r"검증|verification"),
    ("constraints", r"제약|constraints?"),
    ("surfaces", r"영향|영역|surfaces?"),
    ("vocabulary", r"용어|glossary|vocabulary"),
    ("approval", r"승인|approval"),
    ("stop", r"멈추|중단 조건|종료 조건|stop"),
)
PRIORITY = {"필수": "MUST", "must": "MUST", "권장": "SHOULD", "should": "SHOULD", "선택": "COULD", "could": "COULD"}


def _nfc(s):
    return unicodedata.normalize("NFC", s)


def domain(slug):
    return re.sub(r"[^A-Z0-9]", "", slug.upper())[:6] or "CORE"


def split_list(text):
    return [x.strip(" -*\t") for x in re.split(r"[,\n]", text or "") if x.strip(" -*\t")]


# ------------------------------------------------------------------ sources

def scan_docs(doc_dir):
    """Headings and goal-like sentences as *inferred* candidate facts."""
    facts, files = [], []
    for dirpath, dirnames, filenames in os.walk(doc_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            if not fn.lower().endswith((".md", ".txt")):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, doc_dir)
            with open(p, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            files.append((rel, len(text)))
            for line in text.splitlines():
                s = line.strip()
                if not s or len(s) > 200:
                    continue
                if re.match(r"^#{1,3}\s+\S", s):
                    facts.append((rel, "heading", s.lstrip("# ").strip()))
                elif re.search(r"(목적|목표|문제|사용자|요구사항|제약|성공|범위|goal|problem|users?|constraint|success|scope)\s*[:：]", s, re.I):
                    facts.append((rel, "statement", s))
    return files, facts


def find_plan_docs(repo):
    """Find a plan document and a requirements document by file name. Shallow paths win."""
    best = {"plan": None, "req": None}
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        depth = os.path.relpath(dirpath, repo).count(os.sep)
        for fn in filenames:
            name = _nfc(fn).lower()
            if not name.endswith(".md"):
                continue
            stem = name[:-3]
            for kind, names in (("plan", PLAN_NAMES), ("req", REQ_NAMES)):
                rank = next((i for i, n in enumerate(names) if stem == n or stem.startswith(n + "-")
                             or stem.startswith(n + "_") or (not n.isascii() and stem.startswith(n))), None)
                if rank is None:
                    continue
                key = (depth, rank, name)
                if best[kind] is None or key < best[kind][0]:
                    best[kind] = (key, os.path.join(dirpath, fn))
                break
    return tuple(best[k][1] if best[k] else None for k in ("plan", "req"))


def parse_sections(text):
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    out, cur, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            if cur:
                out.append((cur, "\n".join(buf).strip()))
            cur, buf = re.sub(r"^\d+[.)]\s*", "", m.group(1).strip()), []
        elif cur:
            buf.append(line)
    if cur:
        out.append((cur, "\n".join(buf).strip()))
    return out


def parse_table(body):
    rows = [r.strip() for r in body.splitlines() if r.strip().startswith("|")]
    if len(rows) < 2:
        return []

    def cells(r):
        return [c.strip() for c in r.strip("|").split("|")]
    head = cells(rows[0])
    return [dict(zip(head, cells(r))) for r in rows[2:] if not set(r) <= set("|-: ")]


def _col(row, *names):
    for k, v in row.items():
        if any(n in k.lower() for n in names):
            return v
    return ""


def extract_from_plan(repo):
    """Take Grill answers and requirements from existing plan documents.

    Returns (prefill, src, reqs, files).
    """
    plan, req = find_plan_docs(repo)
    prefill, src, reqs, files = {}, {}, [], []

    def take(key, value, where):
        value = value.strip()
        if value and key not in prefill:
            prefill[key], src[key] = value, where

    for path in (plan, req):
        if not path:
            continue
        rel = os.path.relpath(path, repo)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        files.append((rel, len(text)))
        for title, body in parse_sections(text):
            where = f"`{rel}` §{title}"
            low = title.lower()
            table = parse_table(body)
            if re.search(r"요건|requirement", low) and table and _col(table[0], "id"):
                kind = "non_functional" if re.search(r"비기능|non.?func", low) else "functional"
                for row in table:
                    stmt = _col(row, "요건", "requirement", "내용", "statement")
                    if not stmt:
                        continue
                    acc = _col(row, "인수", "accept")
                    reqs.append({
                        "id": _col(row, "id"), "statement": stmt, "kind": kind,
                        "acceptance": [a.strip() for a in re.split(r"(?<=[.다])\s+", acc) if a.strip()],
                        "priority": PRIORITY.get(_col(row, "우선", "priority").lower(), "MUST"),
                    })
                continue
            if re.search(r"범위|scope", low) and table:
                for row in table:
                    label = " ".join(list(row.values())[:1]).lower()
                    text_ = " ".join(list(row.values())[1:])
                    if re.search(r"제외|out", label):
                        take("non_goals", text_, where)
                    elif re.search(r"포함|in", label):
                        take("scope_in", text_, where)
                continue
            for key, pat in SECTION_KEYS:
                if re.search(pat, low):
                    take(key, body, where)
                    break

    func = [r for r in reqs if r["kind"] == "functional"]
    if func:
        prefill["features"] = "\n".join(f"- {r['id']} {r['statement']}" for r in func)
        src["features"] = f"`{files[-1][0]}` ({len(func)} functional)"
    elif "scope_in" in prefill:
        prefill["features"], src["features"] = prefill["scope_in"], src["scope_in"]
    prefill.pop("scope_in", None)
    src.pop("scope_in", None)
    nfr = [r for r in reqs if r["kind"] == "non_functional"]
    if nfr:
        extra = "\n".join(f"- {r['id']} {r['statement']}: {' '.join(r['acceptance'])}" for r in nfr)
        prefill["constraints"] = (prefill.get("constraints", "") + "\n" + extra).strip()
        src["constraints"] = (src.get("constraints", "") + f" + {len(nfr)} non-functional").strip(" +")
    return prefill, src, reqs, files


def write_sources(pdir, mode, where=None, files=None, facts=None):
    os.makedirs(os.path.join(pdir, "intake"), exist_ok=True)
    lines = ["# Intake Sources / 소스", "",
             t("> 이 프로젝트가 무엇을 근거로 시작됐는지 남긴다.", "> What this project started from."), "",
             f"- mode: `{mode}`", f"- date: {date.today().isoformat()}"]
    if where:
        lines.append(f"- location: `{where}`")
    lines += ["", t("## 소스 목록", "## Sources"), ""]
    if files:
        lines += ["| file | chars |", "|---|---|"] + [f"| `{rel}` | {n:,} |" for rel, n in files[:40]]
        if len(files) > 40:
            lines.append(f"| … +{len(files) - 40} | |")
    else:
        lines.append(t("_(문서 소스 없음 — 대화로 수집)_", "_(no documents — collected by questions)_"))
    lines += ["", t("## 추출된 사실 후보", "## Candidate facts"), ""]
    if facts:
        lines += [t("> 전부 추정(inferred)이다. 사람이 확인하기 전에는 사실이 아니다.",
                    "> All inferred. Not facts until a person confirms them."), "",
                  "| source | kind | text |", "|---|---|---|"]
        lines += [f"| `{rel}` | {kind} | {s.replace('|', chr(92) + '|')[:120]} |" for rel, kind, s in facts[:60]]
    else:
        lines.append("_(none)_")
    lines += ["", t("## 가정", "## Assumptions"), "", "- ",
              "", t("## 모순", "## Contradictions"), "", t("- 없음", "- none"),
              "", t("## 열린 질문", "## Open questions"), "", "- "]
    with open(os.path.join(pdir, "intake", "sources.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ questions

def run_grill(prefill=None, interactive=True, ask=input):
    prefill = prefill or {}
    out = {}
    if interactive:
        print(t("\nGrill — 프로젝트를 캐묻습니다. 비워 두면 건너뜁니다. 필수(*)가 비면 게이트는 pending입니다.\n",
                "\nGrill — questions about the project. Leave blank to skip. A blank required (*) item keeps the gate pending.\n"))
    for key, ko, en, required in QUESTIONS:
        hint = prefill.get(key, "")
        if not interactive or (hint and interactive == "fill"):
            out[key] = hint
            continue
        if hint:
            print("  " + t("문서에서", "from documents") + f": {hint[:80]}")
        try:
            answer = ask(f"{t(ko, en)}{' *' if required else ''}\n> ").strip()
        except EOFError:
            answer = ""
        out[key] = answer or hint
        print()
    return out


def gate_status(ans):
    missing = [k for k, _ko, _en, req in QUESTIONS if req and not (ans.get(k) or "").strip()]
    return ("complete" if not missing else "pending"), missing


def write_grill(pdir, ans, status, missing, mode, src=None):
    src = src or {}
    lines = ["# Grill Gate", "", f"- status: **{status}**", f"- mode: `{mode}`", f"- date: {date.today().isoformat()}", ""]
    if status != "complete":
        lines += [t("> 게이트가 열리지 않았다. 아래 필수 항목이 비어 있다. 구현을 시작하지 않는다.",
                    "> The gate is not open. The required items below are empty. Do not start implementation."), ""]
        lines += [f"- `{k}`" for k in missing] + [""]
    if src:
        lines += [t("> 기존 기획 문서에서 옮겨 적은 답이 있다. 원래 문서가 바뀌면 `vaultos grill`을 다시 실행한다.",
                    "> Some answers come from existing plan documents. Run `vaultos grill` again when they change."), ""]
    lines += [t("## 질문과 답", "## Questions and answers"), ""]
    for key, ko, en, required in QUESTIONS:
        lines += [f"### {t(ko, en)}{' *' if required else ''}", "", ans.get(key) or "_(no answer)_", ""]
        if src.get(key) and ans.get(key):
            lines += [f"> source: {src[key]}", ""]
    lines += [t("## 멈추는 조건", "## Stop condition"), "", ans.get("stop") or "_(not set)_", "",
              t("> success criteria가 충족되면 멈춘다. 다듬기로 계속하지 않고 후속 task로 남긴다.",
                "> Stop when the success criteria hold. Do not keep polishing; record follow-up tasks."), ""]
    with open(os.path.join(pdir, "intake", "grill.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ outputs

def write_constitution(pdir, name, ans):
    os.makedirs(os.path.join(pdir, "governance"), exist_ok=True)
    ngs, tcs = split_list(ans.get("non_goals")), split_list(ans.get("constraints"))
    lines = [f"# Constitution — {name}", "",
             t("> 프로젝트의 불변 원칙이다. AI는 이 문서를 고치지 않는다. 바꾸려면 사람이 직접 한다.",
               "> The fixed principles of the project. AI does not edit this file. Only a person changes it."), "",
             "## Mission", "", ans.get("outcome") or "_(not set)_", ""]
    if ans.get("problem"):
        lines += [t("해결하려는 문제:", "Problem:"), "", ans["problem"], ""]
    lines += ["## Core Principles", "",
              "- **P-001**: " + t("success criteria가 충족되면 멈춘다.", "Stop when the success criteria hold."),
              "- **P-002**: " + t("요구사항에 연결되지 않은 구현을 하지 않는다.", "No implementation without a linked requirement."), "",
              "## Non-Goals", ""]
    lines += [f"- **NG-{i:03d}**: {v}" for i, v in enumerate(ngs, 1)] or ["- _(not set)_"]
    lines += ["", "## Constraints", ""]
    lines += [f"- **TC-{i:03d}**: {v}" for i, v in enumerate(tcs, 1)] or ["- _(none)_"]
    if ans.get("vocabulary"):
        lines += ["", "## Vocabulary", "", ans["vocabulary"]]
    lines += ["", "## Governance", "",
              "- " + t("요구사항 변경은 CR(changes/)로 한다.", "Requirement changes go through a CR (changes/)."),
              "- " + t("구조 변경은 ADR(architecture/adr/)로 한다.", "Structure changes go through an ADR (architecture/adr/)."),
              "- " + t("evidence 없이 done으로 바꾸지 않는다.", "No done without evidence."), ""]
    if ans.get("approval"):
        lines += [t("사람 승인이 필요한 지점:", "Human approval points:"), "", ans["approval"], ""]
    with open(os.path.join(pdir, "governance", "constitution.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _req_block(rid, statement, kind, source, priority, acceptance, verification):
    out = [f"  - id: {rid}", f"    statement: {quote(statement)}", f"    type: {kind}",
           f"    source: {quote(source)}", f"    priority: {priority}", "    acceptance:"]
    out += [f"      - {quote(a)}" for a in acceptance] or [f"      - {quote(t('(판정 가능한 문장으로 채운다)', '(fill with a checkable sentence)'))}"]
    out += ["    verification:", f"      - {quote(verification or t('(어떻게 검증할지 채운다)', '(fill: how it is verified)'))}",
            "    status: draft", ""]
    return out


def write_requirements(pdir, slug, ans, doc_reqs=None, doc_rel=None):
    """One REQ per feature, or one per row of an existing requirements table."""
    os.makedirs(os.path.join(pdir, "requirements"), exist_ok=True)
    dom = domain(slug)
    out = ["# Generated by the Grill Gate. Success criteria are part of each requirement.",
           "# Grill Gate가 만들었다. 성공 기준은 요구사항의 일부다.", "", "requirements:"]
    ids = []
    if doc_reqs:
        for i, r in enumerate(doc_reqs, 1):
            rid = f"REQ-{dom}-{i:03d}"
            ids.append(rid)
            out += _req_block(rid, r["statement"], r["kind"], f"{doc_rel} {r['id']}".strip(), r["priority"],
                              r["acceptance"], ans.get("verification", ""))
    else:
        success = ans.get("success", "")
        for i, feat in enumerate(split_list(ans.get("features")), 1):
            rid = f"REQ-{dom}-{i:03d}"
            ids.append(rid)
            out += _req_block(rid, feat, "functional", "intake/grill.md", "MUST",
                              [success] if success else [], ans.get("verification", ""))
    if not ids:
        out[-1] = "requirements: []"
    with open(os.path.join(pdir, "requirements", "requirements.yaml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return ids


def write_timeline(pdir, name, ans, start=None):
    os.makedirs(os.path.join(pdir, "status"), exist_ok=True)
    d = start or date.today()
    rows, gantt = [], []
    for key, ko, en, days in PHASES:
        end = d + timedelta(days=days)
        rows.append(f"| {key} | {t(ko, en)} | {d.isoformat()} | {end.isoformat()} | {days}d |")
        gantt.append(f"    {t(ko, en)} :{key}, {d.isoformat()}, {days}d")
        d = end
    lines = ["# Timeline", "",
             t("> Grill Gate가 만든 초안이다. task가 쌓이면 조정한다.", "> A draft from the Grill Gate. Adjust it as tasks come in."), "",
             "| phase | | start | end | length |", "|---|---|---|---|---|", *rows, "",
             "```mermaid", "gantt", f"    title {name}", "    dateFormat YYYY-MM-DD", "    axisFormat %m/%d",
             "    section Phases", *gantt, "```", ""]
    with open(os.path.join(pdir, "status", "timeline.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_tasks(repo, ans, req_ids, dom):
    """Split each feature into spec / build / verify slices. Never touches a tracker that has tasks."""
    if not repo or not os.path.isdir(repo):
        return None
    tpath = os.path.join(repo, "tracker", "tasks.yaml")
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as fh:
            if re.search(r"^\s*-\s*id:", fh.read(), re.M):
                return None
    os.makedirs(os.path.dirname(tpath), exist_ok=True)
    feats = split_list(ans.get("features"))
    out = ["# Task slices from the Grill Gate. This file is the source of truth.",
           "# Grill Gate가 만든 task. 이 파일이 정본이다.", "", "tasks:"]
    n = 0
    for i, feat in enumerate(feats):
        req = req_ids[i] if i < len(req_ids) else None
        for phase, ko, en, role in SLICES:
            n += 1
            dod = ans.get("verification") if phase == "verify" else ""
            out += [f"  - id: T-{dom}-{n:03d}",
                    f"    title: {quote(feat + ' — ' + t(ko, en))}",
                    "    status: planned",
                    f"    phase: {phase}",
                    f"    owner: {role}",
                    f"    requirement_ids: [{req}]" if req else "    requirement_ids: []",
                    "    definition_of_done:",
                    f"      - {quote(dod or t('(완료 조건을 채운다)', '(fill: when is it done)'))}",
                    "    evidence: []", ""]
    if not feats:
        out[-1] = "tasks: []"
    with open(tpath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return tpath
