"""vaultos — connect your vault (intent) and your repositories (execution).

    vaultos init       create the VaultOS folder inside your vault
    vaultos config     show or change this machine's settings
    vaultos new        register a project (vault + repository)
    vaultos link       connect an existing repository to a project
    vaultos status     what is where, how far
    vaultos grill      the Grill Gate: question the project, write requirements
    vaultos validate   check a repository against the contract (--ci: repository only)
    vaultos sync       tracker -> project summary and board in the vault
    vaultos agents     model tiers and role agents (a guide)
    vaultos doctor     read-only check of this machine
    vaultos upgrade    update the framework files in your VaultOS folder
"""

import argparse
import os
import re
import subprocess
import sys

from . import agents, bind, doctor, grill, home, kanban, upgrade, validate, version, yamlish
from .i18n import lang, set_lang, t
from .paths import (SLUG, expand, find_home, find_repo_root, project_dir, projects, read_config, read_link,
                    repo_path, set_config, set_repo_path, workspace_root)


def _git(*a, cwd=None):
    try:
        r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _ask(prompt, default=None):
    if not sys.stdin.isatty():
        return default
    hint = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{hint}: ").strip()
    except EOFError:
        value = ""
    return value or default


def require_home(args):
    vault, h = find_home(getattr(args, "vault", None))
    if not h:
        if vault:
            print(t(f"이 볼트 안에 VaultOS 폴더가 없습니다: {vault}", f"No VaultOS folder inside this vault: {vault}"))
        else:
            print(t("볼트가 설정되지 않았습니다.", "No vault is configured."))
        print(t("  vaultos init 으로 만들거나, --vault <볼트 경로>를 붙입니다.",
                "  Run vaultos init, or pass --vault <vault path>."))
        sys.exit(2)
    return h


def _manifest(pdir):
    try:
        data = yamlish.load(os.path.join(pdir, "project.yaml"))
        return data if isinstance(data, dict) else {}
    except (OSError, yamlish.YamlError):
        return {}


def _replace_top(text, key, value_lines):
    """Replace a top-level `key:` block with new lines."""
    pat = re.compile(rf"^{re.escape(key)}:.*(?:\n(?:[ \t]+.*|[ \t]*-.*))*", re.M)
    block = "\n".join(value_lines)
    if pat.search(text):
        return pat.sub(lambda _m: block, text, count=1)
    return text.rstrip("\n") + "\n" + block + "\n"


# ---------------------------------------------------------------- init / config

def cmd_init(args):
    print(t("VaultOS 초기화 — 내 볼트 안에 VaultOS 폴더를 만듭니다.", "VaultOS init — creates a VaultOS folder inside your vault."))
    print(t("볼트 루트와 .obsidian은 건드리지 않습니다.\n", "The vault root and .obsidian are never touched.\n"))
    vault = args.path or _ask(t("내 볼트 경로 (Obsidian 볼트 등, 이미 있는 폴더)", "Your vault path (an Obsidian vault or any existing folder)"))
    vault = expand(vault)
    err = home.check_vault(vault)
    if err:
        print(err)
        return 2
    if os.path.isdir(os.path.join(vault, ".obsidian")):
        print(t("  Obsidian 볼트를 찾았습니다.", "  Obsidian vault detected."))
    folder = args.folder or _ask(t("볼트 안 VaultOS 폴더 이름", "Folder name inside the vault"), "VaultOS")
    chosen = args.lang or _ask(t("언어 (ko/en)", "Language (ko/en)"), lang())
    chosen = "ko" if (chosen or "").lower().startswith("ko") else "en"
    set_lang(chosen)
    ws = expand(args.workspace or _ask(t("코드 저장소를 둘 폴더 (볼트 밖)", "Folder for code repositories (outside the vault)"), "~/workspace"))
    if ws == vault or ws.startswith(vault.rstrip(os.sep) + os.sep):
        print(t("코드 저장소 폴더는 볼트 밖이어야 합니다. 동기화가 .git을 깨뜨릴 수 있습니다.",
                "The repository folder must be outside the vault. Syncing can break .git folders."))
        return 2
    try:
        h, created = home.create(vault, folder, chosen)
    except ValueError as e:
        print(e)
        return 1
    set_config(vault=vault, folder=folder, lang=chosen, workspace_root=ws)
    print(t(f"\n만들었습니다: {h}  (파일 {len(created)}개)", f"\nCreated: {h}  ({len(created)} files)"))
    print(t(f"설정: ~/.config/vaultos/config", "Settings: ~/.config/vaultos/config"))
    print(t("\n다음: vaultos new <프로젝트>  또는  vaultos link <프로젝트> (기존 저장소에서)",
            "\nNext: vaultos new <project>  or  vaultos link <project> (inside an existing repository)"))
    return 0


def cmd_config(args):
    changes = {}
    if args.set_vault:
        vault = expand(args.set_vault)
        _v, h = find_home(vault, args.folder)
        if not h:
            print(t(f"그 볼트 안에 VaultOS 폴더가 없습니다: {vault}", f"No VaultOS folder in that vault: {vault}"))
            return 1
        changes.update(vault=os.path.dirname(h), folder=os.path.basename(h))
    if args.workspace:
        changes["workspace_root"] = expand(args.workspace)
    if args.set_lang:
        changes["lang"] = args.set_lang
    if changes:
        set_config(**changes)
    cfg = read_config()
    for key in ("vault", "folder", "workspace_root", "lang"):
        print(f"  {key:15} {cfg.get(key, '-')}")
    for key in sorted(k for k in cfg if k.startswith(("repo.", "model."))):
        print(f"  {key:15} {cfg[key]}")
    return 0


# ---------------------------------------------------------------- projects

def _project_yaml(slug, name, mission, profile, url):
    return f"""# Project entry point. Agents read this file first.
# 프로젝트 진입점. 에이전트가 가장 먼저 읽는다.
project:
  id: {slug.upper()}
  name: {yamlish.quote(name)}
  slug: {slug}
mission: {yamlish.quote(mission)}
governance_profile: {profile}
# Grill Gate: pending / complete — `vaultos grill` writes it. pending이면 구현하지 않는다.
grill: pending
status:
  phase: idea
repo:
  url: {yamlish.quote(url) if url else 'null'}
# Written by `vaultos sync` / vaultos sync가 쓴다
next_actions: []
blocked: []
"""


def _link_repo(h, slug, repo, profile):
    made, skipped = bind.bind(repo, slug, profile)
    set_repo_path(slug, repo)
    url = _git("remote", "get-url", "origin", cwd=repo)
    mpath = os.path.join(project_dir(h, slug), "project.yaml")
    with open(mpath, encoding="utf-8") as fh:
        text = fh.read()
    if url and re.search(r"^\s+url:\s*null\s*$", text, re.M):
        text = re.sub(r"^(\s+)url:\s*null\s*$", lambda m: f"{m.group(1)}url: {yamlish.quote(url)}", text, count=1, flags=re.M)
        with open(mpath, "w", encoding="utf-8") as fh:
            fh.write(text)
    return made, skipped


def cmd_new(args):
    h = require_home(args)
    slug = args.slug
    if _bad_slug(slug):
        return 2
    pdir = project_dir(h, slug)
    if os.path.exists(os.path.join(pdir, "project.yaml")):
        print(t(f"이미 있습니다: {pdir}", f"Already exists: {pdir}"))
        return 1
    repo = None
    if args.path:
        repo = expand(args.path)
        if not os.path.isdir(repo):
            print(t(f"저장소 폴더가 없습니다: {repo}", f"Repository folder not found: {repo}"))
            return 1
    elif not args.no_repo:
        repo = os.path.join(workspace_root(), slug)
        if not os.path.isdir(repo):
            os.makedirs(repo)
            if _git("init", "-q", cwd=repo) is None:
                print(t("  git이 없어 git init을 건너뛰었습니다", "  git not found — skipped git init"))
            print(t(f"저장소를 만들었습니다: {repo}", f"Created repository: {repo}"))
    url = _git("remote", "get-url", "origin", cwd=repo) if repo else None
    for d in ("intake", "governance", "requirements", "changes", os.path.join("architecture", "adr"), "status"):
        os.makedirs(os.path.join(pdir, d), exist_ok=True)
    with open(os.path.join(pdir, "project.yaml"), "w", encoding="utf-8") as fh:
        fh.write(_project_yaml(slug, args.name or slug, args.mission or "", args.profile, url))
    rpath = os.path.join(pdir, "requirements", "requirements.yaml")
    if not os.path.exists(rpath):
        with open(rpath, "w", encoding="utf-8") as fh:
            fh.write("requirements: []\n")
    print(t(f"볼트에 등록했습니다: projects/{slug}/", f"Registered in the vault: projects/{slug}/"))
    if repo:
        made, _s = _link_repo(h, slug, repo, args.profile)
        print(t(f"저장소에 계약 파일을 놓았습니다: {repo}", f"Contract files placed in: {repo}") + f"  (+{len(made)})")
    print(t("\n다음: 저장소에서 vaultos grill", "\nNext: vaultos grill (inside the repository)"))
    return 0


def _bad_slug(slug):
    if slug and not SLUG.match(slug):
        print(t("프로젝트 이름은 영문 소문자, 숫자, -만 씁니다 (예: my-app)", "Project names use lowercase letters, digits and - (e.g. my-app)"))
        return True
    return False


def cmd_link(args):
    if _bad_slug(args.slug):
        return 2
    h = require_home(args)
    if not os.path.isfile(os.path.join(project_dir(h, args.slug), "project.yaml")):
        print(t(f"볼트에 그런 프로젝트가 없습니다: {args.slug}  (vaultos new로 먼저 등록)",
                f"No such project in the vault: {args.slug}  (register it with vaultos new)"))
        return 1
    repo = expand(args.path or os.getcwd())
    profile = _manifest(project_dir(h, args.slug)).get("governance_profile") or "full"
    made, skipped = _link_repo(h, args.slug, repo, profile)
    print(t(f"연결했습니다: {repo} -> projects/{args.slug}", f"Linked: {repo} -> projects/{args.slug}"))
    for f in made:
        print(f"  + {f}")
    for f in skipped:
        print(f"  . {f} ({t('이미 있음', 'kept')})")
    print(t("\n  git hook: git config core.hooksPath .githooks", "\n  git hook: git config core.hooksPath .githooks"))
    return 0


def cmd_status(args):
    h = require_home(args)
    print(f"VaultOS {version()}  {h}")
    print(f"  {t('코드 폴더', 'repositories')}  {workspace_root()}")
    ps = projects(h)
    if not ps:
        print(t("\n프로젝트 없음. vaultos new <프로젝트>로 시작합니다.", "\nNo projects. Start with vaultos new <project>."))
        return 0
    print()
    for slug, pdir in ps:
        m = _manifest(pdir)
        st = m.get("status") if isinstance(m.get("status"), dict) else {}
        gate = m.get("grill") or "?"
        flag = "" if gate == "complete" else t(f"   [Grill {gate} — 구현 전]", f"   [Grill {gate} — before implementation]")
        print(f"  {slug}   phase {st.get('phase', '-')}   profile {m.get('governance_profile', '-')}{flag}")
        repo = repo_path(slug)
        if repo and os.path.isdir(repo):
            branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo) or "-"
            dirty = _git("status", "--porcelain", cwd=repo)
            print(f"      {repo}  [{branch}{t(f', 미커밋 {len(dirty.splitlines())}건', f', {len(dirty.splitlines())} uncommitted') if dirty else ''}]")
        else:
            print("      " + t("이 기기에 연결된 저장소 없음 (vaultos link)", "no repository linked on this machine (vaultos link)"))
    return 0


# ---------------------------------------------------------------- contract

def _linked_repo(args):
    repo = find_repo_root(args.path)
    link = read_link(repo) if repo else None
    return repo, link


def cmd_grill(args):
    repo, link = _linked_repo(args)
    slug = args.slug or (link or {}).get("project")
    if _bad_slug(slug):
        return 2
    if not slug:
        print(t("어느 프로젝트인지 모릅니다. 연결된 저장소 안에서 실행하거나 프로젝트 이름을 붙입니다.",
                "Which project? Run inside a linked repository or pass the project name."))
        return 1
    h = require_home(args)
    pdir = project_dir(h, slug)
    if not os.path.isfile(os.path.join(pdir, "project.yaml")):
        print(t(f"볼트에 그런 프로젝트가 없습니다: {slug}", f"No such project in the vault: {slug}"))
        return 1
    if not repo:
        repo = repo_path(slug)
    name = (_manifest(pdir).get("project") or {}).get("name") or slug
    prefill, src, plan_reqs, plan_files = ({}, {}, [], [])
    mode = "grill-me"
    if repo and not args.docs:
        prefill, src, plan_reqs, plan_files = grill.extract_from_plan(repo)
        if plan_files:
            mode = "grill-from-plan"
            print(t("기존 기획 문서에서 답을 옮겨 적습니다:", "Taking answers from existing plan documents:"))
            for rel, _n in plan_files:
                print(f"  {rel}")
    if args.docs:
        doc_dir = expand(args.docs)
        if not os.path.isdir(doc_dir):
            print(t(f"폴더가 없습니다: {doc_dir}", f"Folder not found: {doc_dir}"))
            return 1
        files, facts = grill.scan_docs(doc_dir)
        mode = "grill-with-docs"
        print(t(f"문서 {len(files)}개에서 후보 {len(facts)}건", f"{len(facts)} candidate(s) from {len(files)} document(s)"))
        grill.write_sources(pdir, mode, doc_dir, files, facts)
    else:
        grill.write_sources(pdir, mode, repo if plan_files else None, plan_files or None)

    interactive = False if args.non_interactive else ("fill" if plan_files else True)
    ans = grill.run_grill(prefill, interactive=interactive)
    status, missing = grill.gate_status(ans)
    grill.write_grill(pdir, ans, status, missing, mode, src)
    grill.write_constitution(pdir, name, ans)
    doc_rel = next((rel for rel, _ in plan_files if any(n in grill._nfc(rel).lower() for n in grill.REQ_NAMES)), None)
    req_ids = grill.write_requirements(pdir, slug, ans, plan_reqs if doc_rel else None, doc_rel)
    grill.write_timeline(pdir, name, ans)
    tpath = None if plan_files else grill.write_tasks(repo, ans, req_ids, grill.domain(slug))

    mpath = os.path.join(pdir, "project.yaml")
    with open(mpath, encoding="utf-8") as fh:
        text = fh.read()
    text = _replace_top(text, "grill", [f"grill: {status}"])
    if status == "complete":
        text = re.sub(r"^(\s+)phase:\s*idea\s*$", r"\1phase: planning", text, count=1, flags=re.M)
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(text)
    if repo and os.path.isfile(os.path.join(repo, ".vaultos", "contract.yaml")):
        cpath = os.path.join(repo, ".vaultos", "contract.yaml")
        with open(cpath, encoding="utf-8") as fh:
            c = fh.read()
        with open(cpath, "w", encoding="utf-8") as fh:
            fh.write(_replace_top(c, "grill", [f"grill: {status}"]))

    print(f"\nGrill Gate: {status}")
    for rel in ("intake/sources.md", "intake/grill.md", "governance/constitution.md",
                f"requirements/requirements.yaml  ({len(req_ids)} REQ)", "status/timeline.md"):
        print(f"  {rel}")
    if tpath:
        print(f"  {tpath}")
    if status != "complete":
        print(t(f"\n  비어 있는 필수 항목: {', '.join(missing)} — 게이트가 pending인 동안 구현하지 않습니다.",
                f"\n  Missing required answers: {', '.join(missing)} — no implementation while the gate is pending."))
    return 0


def cmd_validate(args):
    repo, link = _linked_repo(args)
    if not link:
        if not args.quiet:
            print(t("VaultOS에 연결되지 않은 저장소입니다. vaultos link <프로젝트>로 연결합니다.",
                    "This repository is not linked. Link it with vaultos link <project>."))
        return 1
    h = None
    profile = "full"
    if not args.ci:
        h = require_home(args)
        profile = _manifest(project_dir(h, link["project"])).get("governance_profile") or "full"
    else:
        try:
            c = yamlish.load(os.path.join(repo, ".vaultos", "contract.yaml")) or {}
            profile = c.get("governance_profile") or "full"
        except (OSError, yamlish.YamlError):
            pass
    violations, warnings, facts = validate.check(repo, h, link, profile)
    if not args.quiet:
        bits = [f"{k} {facts[k]}" for k in ("grill", "requirements", "tasks") if k in facts]
        print(f"{link['project']}  ({profile}{', CI' if args.ci else ''})" + (f"  {' / '.join(bits)}" if bits else ""))
    for m in violations:
        print(f"  [{t('위반', 'violation')}] {m}")
    if not args.quiet:
        for m in warnings:
            print(f"  [{t('경고', 'warning')}] {m}")
        if not violations:
            print("  " + t("계약 위반 없음", "No contract violation") + (f" ({t('경고', 'warnings')} {len(warnings)})" if warnings else ""))
    return 1 if violations else 0


def cmd_sync(args):
    repo, link = _linked_repo(args)
    if not link:
        print(t("VaultOS에 연결되지 않은 저장소입니다.", "This repository is not linked."))
        return 1
    h = require_home(args)
    pdir = project_dir(h, link["project"])
    tasks, err = validate.load_tasks(os.path.join(repo, "tracker", "tasks.yaml"))
    if err:
        print(t(f"tracker/tasks.yaml을 읽을 수 없습니다 — {err}", f"Cannot read tracker/tasks.yaml — {err}"))
        return 1
    done = sum(1 for x in tasks if x.get("status") == "done")
    blocked = [str(x.get("id")) for x in tasks if x.get("status") == "blocked"]
    nxt = [str(x.get("id")) for x in tasks if x.get("status") in ("in_progress", "review", "ready", "planned")][:3]
    mpath = os.path.join(pdir, "project.yaml")
    with open(mpath, encoding="utf-8") as fh:
        text = fh.read()
    text = _replace_top(text, "next_actions", ["next_actions: " + yamlish.flow(nxt)])
    text = _replace_top(text, "blocked", ["blocked: " + yamlish.flow(blocked)])
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(os.path.join(pdir, "kanban.md"), "w", encoding="utf-8") as fh:
        fh.write(kanban.render(tasks))
    print(t(f"동기화했습니다  {link['project']}", f"Synced  {link['project']}"))
    print(f"  task {done}/{len(tasks)} done")
    print(f"  next {', '.join(nxt) or '-'}")
    if blocked:
        print(f"  blocked {', '.join(blocked)}")
    print(f"  board {link['project_path']}/kanban.md")
    return 0


# ---------------------------------------------------------------- environment

def cmd_agents(args):
    if args.action == "set":
        if len(args.rest) != 3:
            print("vaultos agents set <claude|codex> <high|bulk|fast> <model> [--effort level]")
            return 2
        return agents.set_model(*args.rest, effort=args.effort)
    if args.rest:
        print(t(f"인자가 너무 많습니다: {' '.join(args.rest)}", f"Unexpected arguments: {' '.join(args.rest)}"))
        return 2
    if args.action == "sync":
        return agents.sync(dry_run=args.dry_run)
    return agents.show()


def cmd_doctor(args):
    return doctor.run(getattr(args, "vault", None))


def cmd_upgrade(args):
    return upgrade.run(require_home(args), dry_run=args.dry_run)


def build_parser():
    ap = argparse.ArgumentParser(prog="vaultos", description="VaultOS — an audit trail for AI coding agents / AI 에이전트 작업 감사")
    ap.add_argument("--vault", help="your vault path (overrides the config) / 볼트 경로")
    ap.add_argument("--lang", choices=("ko", "en"), help="output language / 출력 언어")
    ap.add_argument("--version", action="version", version=f"vaultos {version()}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)  # --vault / --lang also after the command
    common.add_argument("--vault", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--lang", choices=("ko", "en"), default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    p = sub.add_parser("init", parents=[common], help="create the VaultOS folder inside your vault / 볼트 안에 VaultOS 폴더 생성")
    p.add_argument("path", nargs="?", help="your vault path / 볼트 경로")
    p.add_argument("--folder", help="folder name inside the vault (default VaultOS)")
    p.add_argument("--workspace", help="folder for code repositories, outside the vault")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("config", parents=[common], help="show or change settings / 설정 보기·바꾸기")
    p.add_argument("--set-vault", metavar="PATH")
    p.add_argument("--folder")
    p.add_argument("--workspace")
    p.add_argument("--set-lang", choices=("ko", "en"))
    p.set_defaults(fn=cmd_config)

    p = sub.add_parser("new", parents=[common], help="register a project / 프로젝트 등록")
    p.add_argument("slug")
    p.add_argument("--name")
    p.add_argument("--mission")
    p.add_argument("--path", help="existing repository / 기존 저장소")
    p.add_argument("--no-repo", action="store_true", help="vault only / 볼트에만")
    p.add_argument("--profile", choices=("full", "light"), default="full")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("link", parents=[common], help="connect a repository to a project / 저장소 연결")
    p.add_argument("slug")
    p.add_argument("--path")
    p.set_defaults(fn=cmd_link)

    p = sub.add_parser("status", parents=[common], help="projects and repositories / 현황")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("grill", parents=[common], help="the Grill Gate / Grill Gate")
    p.add_argument("slug", nargs="?")
    p.add_argument("--path")
    p.add_argument("--docs", help="folder of source documents / 소스 문서 폴더")
    p.add_argument("--non-interactive", action="store_true")
    p.set_defaults(fn=cmd_grill)

    p = sub.add_parser("validate", parents=[common], help="check the contract / 계약 검사")
    p.add_argument("--path")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--ci", action="store_true", help="repository only, no vault / 저장소만 (CI)")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("sync", parents=[common], help="tracker -> vault summary and board / tracker → 볼트 요약")
    p.add_argument("--path")
    p.set_defaults(fn=cmd_sync)

    p = sub.add_parser("agents", parents=[common], help="model tiers and role agents (guide) / 모델 등급")
    p.add_argument("action", nargs="?", choices=("show", "set", "sync"), default="show")
    p.add_argument("rest", nargs="*")
    p.add_argument("--effort")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_agents)

    p = sub.add_parser("doctor", parents=[common], help="read-only check / 점검")
    p.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("upgrade", parents=[common], help="update framework files in the vault / 볼트의 프레임워크 갱신")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_upgrade)
    return ap


def main(argv=None):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    if args.lang:
        set_lang(args.lang)
    return args.fn(args)
