#!/usr/bin/env python3
"""End-to-end test of a clean install. Everything runs in a temporary folder with a
temporary HOME, so your real vault, config and agent files are never touched.

    python3 tools/e2e.py            run against this checkout
    python3 tools/e2e.py --keep     keep the temporary folder for inspection

Exit code 0 means every check passed.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class Runner:
    def __init__(self, env):
        self.env, self.results = env, []

    def run(self, name, cmd, cwd=None, expect=0, stdin=None):
        p = subprocess.run(cmd, cwd=cwd, env=self.env, capture_output=True, text=True,
                           input=stdin, timeout=120)
        out = p.stdout + p.stderr
        ok = (expect is None or p.returncode == expect) and "Traceback" not in out
        self.check(name, ok, f"exit {p.returncode}" + ("" if expect is None else f" (want {expect})"))
        if not ok:
            for line in out.strip().splitlines()[-15:]:
                print(f"        | {line}")
        return p

    def check(self, name, ok, detail=""):
        self.results.append((name, bool(ok)))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
        return ok


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def tree(path):
    out = set()
    for d, _dirs, files in os.walk(path):
        for f in files:
            out.add(os.path.relpath(os.path.join(d, f), path))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    root = tempfile.mkdtemp(prefix="vaultos-e2e-")
    home = os.path.join(root, "home")
    os.makedirs(os.path.join(home, ".claude"))
    env = dict(os.environ, HOME=home, USERPROFILE=home, VAULTOS_LANG="en", PATH=os.environ.get("PATH", ""))
    for k in ("VAULTOS_VAULT", "VAULTOS_FOLDER", "VAULTOS_WORKSPACE"):
        env.pop(k, None)
    env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "e2e"
    env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "e2e@example.com"
    r = Runner(env)
    py = sys.executable
    vo = [py, os.path.join(REPO, "vaultos")]
    print(f"temp {root}\n")

    print("[1] files / 파일")
    shipped = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split()
    if not shipped:  # not a git checkout yet
        shipped = sorted(os.path.relpath(os.path.join(d, f), REPO) for d, _x, fs in os.walk(REPO)
                         for f in fs if ".git" not in d and "__pycache__" not in d)
    non_ascii = [f for f in shipped if not f.isascii()]
    r.check("every file name is ASCII / 파일 이름이 모두 영문", not non_ascii, ", ".join(non_ascii[:3]))
    docs = [f for f in shipped if f.endswith(".md") and not f.startswith(".github")]
    mono = [f for f in docs if not any("가" <= c <= "힣" for c in read(os.path.join(REPO, f)))]
    r.check("every document has Korean and English / 문서가 모두 한영 병기", not mono, ", ".join(mono[:3]))
    import re as _re
    named = [f for f in shipped if f.startswith("framework/") and
             _re.search(r"claude-(opus|sonnet|haiku|fable)|gpt-\d|\bsol-\d|\bluna\b", read(os.path.join(REPO, f)), _re.I)]
    r.check("no model names in the framework / 프레임워크에 모델 이름 없음", not named, ", ".join(named[:3]))
    sys.path.insert(0, REPO)
    from vaultos_core.cli import build_parser
    parser = build_parser()
    subs = next(a for a in parser._actions if a.dest == "cmd").choices
    wrong = []
    for f in docs + ["framework/harness/rules/vaultos.md"]:
        for n, line in enumerate(read(os.path.join(REPO, f)).splitlines(), 1):
            for cmd, rest in _re.findall(r"\bvaultos ([a-z]+)((?: [^`|#]*)?)", line):
                if cmd not in subs:
                    wrong.append(f"{f}:{n} vaultos {cmd}")
                    continue
                known = {o for a in subs[cmd]._actions for o in a.option_strings}
                wrong += [f"{f}:{n} vaultos {cmd} {o}" for o in _re.findall(r"(--[a-z][a-z-]*)", rest) if o not in known]
    r.check("documented commands and options exist / 문서의 명령·옵션이 실제로 있음", not wrong, ", ".join(wrong[:4]))

    print("\n[2] install / 설치")
    r.run("install.py", [py, os.path.join(REPO, "install.py")])
    r.check("~/.agents/rules/vaultos.md", os.path.isfile(os.path.join(home, ".agents", "rules", "vaultos.md")))
    cm = os.path.join(home, ".claude", "CLAUDE.md")
    r.check("CLAUDE.md created with one line", os.path.isfile(cm) and "vaultos.md" in read(cm))
    write(cm, "# mine\n- keep short\n")
    p = r.run("install.py again keeps a personal CLAUDE.md", [py, os.path.join(REPO, "install.py")])
    r.check("personal CLAUDE.md untouched, line printed", read(cm) == "# mine\n- keep short\n" and "vaultos.md" in p.stdout)
    r.check("no ~/.codex created", not os.path.exists(os.path.join(home, ".codex")))

    print("\n[3] init in an existing vault / 기존 볼트에 init")
    vault = os.path.join(root, "My Vault")
    write(os.path.join(vault, "Daily", "2026-10-13.md"), "my note\n")
    write(os.path.join(vault, ".obsidian", "hotkeys.json"), '{"mine": true}\n')
    before = {f: read(os.path.join(vault, f)) for f in tree(vault)}
    ws = os.path.join(root, "code")
    r.run("init without a vault path fails (no tty)", vo + ["init"], expect=2)
    r.run("init on a missing vault fails", vo + ["init", os.path.join(root, "nope"), "--workspace", ws], expect=2)
    r.run("init with the workspace inside the vault fails",
          vo + ["init", vault, "--workspace", os.path.join(vault, "code")], expect=2)
    r.run("init", vo + ["init", vault, "--workspace", ws, "--lang", "en"])
    h = os.path.join(vault, "VaultOS")
    after = {f: read(os.path.join(vault, f)) for f in tree(vault) if not f.startswith("VaultOS" + os.sep)}
    r.check("vault root and .obsidian unchanged / 볼트 루트와 .obsidian 그대로", after == before)
    r.check("VaultOS folder created", os.path.isfile(os.path.join(h, "system", "VAULTOS.md"))
            and os.path.isdir(os.path.join(h, "projects")))
    r.check("upgrade base stored", os.path.isfile(os.path.join(h, "system", ".base", "system", "VAULTOS.md")))
    r.run("init twice is refused", vo + ["init", vault, "--workspace", ws], expect=1)
    write(os.path.join(vault, "Taken", "x.md"), "x\n")
    r.run("init into a folder with other files is refused", vo + ["init", vault, "--folder", "Taken", "--workspace", ws], expect=1)
    cfg = read(os.path.join(home, ".config", "vaultos", "config"))
    r.check("config has vault, folder, workspace", f"vault: {vault}" in cfg and "folder: VaultOS" in cfg and f"workspace_root: {ws}" in cfg)

    print("\n[4] project, grill, validate / 프로젝트, Grill, 검사")
    r.run("new with a bad name fails", vo + ["new", "My App"], expect=2)
    r.run("new demo", vo + ["new", "demo", "--name", "Demo: app", "--mission", "Ship it # today"])
    repo = os.path.join(ws, "demo")
    r.check("repo created with contract files", all(os.path.exists(os.path.join(repo, x)) for x in
            (".vaultos/link", ".vaultos/contract.yaml", "tracker/tasks.yaml", "AGENTS.md", ".githooks/pre-commit")))
    r.check(".vaultos/link has no machine path", root not in read(os.path.join(repo, ".vaultos", "link")))
    pdir = os.path.join(h, "projects", "demo")
    sys.path.insert(0, REPO)
    from vaultos_core import yamlish
    m = yamlish.load(os.path.join(pdir, "project.yaml"))
    r.check("project.yaml round-trips special characters", m["project"]["name"] == "Demo: app" and m["mission"] == "Ship it # today")
    r.run("validate before Grill -> violation", vo + ["validate"], cwd=repo, expect=1)
    r.run("status", vo + ["status"])
    answers = "\n".join(["Faster sign-in", "Sign-up is slow", "", "Email login", "Google login: OAuth, Magic link",
                         "Sign-in under 10s", "tests/test_login.py", "", "", "", "", "When success holds"]) + "\n"
    r.run("grill (interactive)", vo + ["grill"], cwd=repo, stdin=answers)
    m = yamlish.load(os.path.join(pdir, "project.yaml"))
    r.check("grill complete", m.get("grill") == "complete")
    reqs = yamlish.load(os.path.join(pdir, "requirements", "requirements.yaml"))["requirements"]
    r.check("REQ with ': ' in the statement is valid YAML", len(reqs) == 2 and reqs[0]["statement"] == "Google login: OAuth")
    tasks = yamlish.load(os.path.join(repo, "tracker", "tasks.yaml"))["tasks"]
    r.check("6 task slices with roles", len(tasks) == 6 and [x["owner"] for x in tasks[:3]] == ["planner", "implementer", "reviewer"])
    r.run("validate after Grill", vo + ["validate"], cwd=repo, expect=0)
    r.run("validate --ci (no vault)", vo + ["validate", "--ci"], cwd=repo, expect=0,)

    tp = os.path.join(repo, "tracker", "tasks.yaml")
    good = read(tp)
    write(tp, good.replace("status: planned", "status: done", 1))
    p = r.run("done without evidence -> violation", vo + ["validate"], cwd=repo, expect=1)
    r.check("warns about owner and done_at", "without owner" in p.stdout and "without done_at" in p.stdout)
    write(tp, good + "  - id: T-X\n    title: x\n    status: ready\n    requirement_ids: [REQ-NOPE-001]\n")
    p = r.run("unknown REQ -> violation", vo + ["validate"], cwd=repo, expect=1)
    r.check("names the unknown REQ", "REQ-NOPE-001" in p.stdout)
    write(tp, good + "  - id: T-Y\n    title: broken: yaml\n")
    p = r.run("bad YAML -> violation with line number", vo + ["validate"], cwd=repo, expect=1)
    r.check("parse error has a line", "line " in p.stdout)
    write(tp, good.replace("status: planned", "status: done\n    done_at: 2026-10-13", 1)
          .replace("owner: planner", "owner: planner@bulk-model", 1).replace("evidence: []", "evidence: [x]", 1))
    r.run("agents set (tier map)", vo + ["agents", "set", "claude", "bulk", "bulk-model"])
    p = r.run("validate: tier mismatch warns only", vo + ["validate"], cwd=repo, expect=0)
    r.check("mismatch named", "planner@bulk-model" in p.stdout)
    r.run("sync", vo + ["sync"], cwd=repo)
    r.check("kanban.md written", "kanban-plugin: board" in read(os.path.join(pdir, "kanban.md")))
    m = yamlish.load(os.path.join(pdir, "project.yaml"))
    r.check("project.yaml still valid after sync", isinstance(m.get("next_actions"), list))

    print("\n[5] grill from plan documents / 기획 문서에서 Grill")
    other = os.path.join(root, "existing")
    os.makedirs(other)
    subprocess.run(["git", "init", "-q"], cwd=other, env=env)
    plan = read(os.path.join(REPO, "framework", "system", "templates", "plan.md"))
    plan = plan.replace("What is the problem now, and who has it?", "Users wait.").replace("When this is done, what is different?", "Instant login.")
    plan = plan.replace("| 포함 / In | |", "| 포함 / In | Login |").replace("| 제외 / Out | |", "| 제외 / Out | Billing |")
    plan = plan.replace("Write checkable sentences.", "p95 < 1s").replace("Tests, manual checks, metrics.", "load test")
    plan = plan.replace("The point where you stop polishing.", "When p95 < 1s")
    write(os.path.join(other, "docs", "plan.md"), plan)
    reqdoc = read(os.path.join(REPO, "framework", "system", "templates", "requirements.md"))
    reqdoc = reqdoc.replace("| FR-001 | | | MUST |", "| FR-001 | Login | Works | MUST |\n| FR-002 | Logout | Works | SHOULD |")
    write(os.path.join(other, "docs", "requirements.md"), reqdoc)
    r.run("new --path existing", vo + ["new", "existing", "--path", other])
    r.run("grill from plan (non-interactive)", vo + ["grill", "--non-interactive"], cwd=other)
    ep = os.path.join(h, "projects", "existing")
    reqs = yamlish.load(os.path.join(ep, "requirements", "requirements.yaml"))["requirements"]
    r.check("requirements taken from docs/requirements.md", [x["statement"] for x in reqs][:2] == ["Login", "Logout"])
    r.check("grill complete from plan", yamlish.load(os.path.join(ep, "project.yaml")).get("grill") == "complete")

    print("\n[6] upgrade / 갱신")
    gov = os.path.join(h, "governance", "agent-policy.md")
    write(gov, read(gov) + "\nMy own rule.\n")
    r.run("upgrade --dry-run", vo + ["upgrade", "--dry-run"])
    p = r.run("upgrade (same version)", vo + ["upgrade"])
    r.check("user edit kept", "My own rule." in read(gov))
    vfile = os.path.join(h, "system", "VAULTOS.md")
    write(os.path.join(h, "system", ".base", "system", "VAULTOS.md"), "old base\n")
    write(vfile, "old base\n")
    r.run("upgrade replaces an unedited file", vo + ["upgrade"])
    r.check("unedited file replaced + backup", read(vfile) == read(os.path.join(REPO, "framework", "system", "VAULTOS.md"))
            and glob.glob(os.path.join(h, "archive", "backups", "upgrade-*", "system", "VAULTOS.md")))
    os.remove(os.path.join(h, "governance", "approval-policy.md"))
    r.run("upgrade again", vo + ["upgrade"])
    r.check("a file you deleted is not recreated", not os.path.exists(os.path.join(h, "governance", "approval-policy.md")))

    print("\n[7] agents (guide) / 모델 배정")
    adir = os.path.join(home, ".claude", "agents")
    write(os.path.join(adir, "planner.md"), "---\nname: planner\n---\nmine\n")
    r.run("agents set claude high", vo + ["agents", "set", "claude", "high", "high-model", "--effort", "high"])
    r.run("agents set bad tier", vo + ["agents", "set", "claude", "best", "x"], expect=2)
    r.run("agents sync", vo + ["agents", "sync"])
    rev = os.path.join(adir, "reviewer.md")
    r.check("reviewer created with marker and owner", os.path.isfile(rev) and "vaultos:managed" in read(rev)
            and "owner: reviewer@high-model" in read(rev))
    r.check("personal planner.md untouched", read(os.path.join(adir, "planner.md")).endswith("mine\n"))
    p = r.run("agents sync again", vo + ["agents", "sync"])
    r.check("nothing changes on the second sync", "new" not in p.stdout and "update" not in p.stdout)

    print("\n[8] doctor")
    p = r.run("doctor", vo + ["doctor"])
    r.check("doctor FAIL 0", "FAIL 0" in p.stdout)
    r.check("model tiers never warn", "[WARN]" not in p.stdout.split("6.")[-1])
    p = r.run("doctor with a wrong vault", vo + ["--vault", os.path.join(root, "nope"), "doctor"], expect=1)

    print("\n[8-1] edge cases / 경계 상황")
    r.run("link with a path-like name is refused", vo + ["link", "../../etc"], expect=2)
    bare = os.path.join(root, "bare")
    os.makedirs(os.path.join(bare, ".vaultos"))
    write(os.path.join(bare, ".vaultos", "link"), "project: demo\nproject_path: projects/demo\n")
    p = r.run("sync without tracker/tasks.yaml fails cleanly", vo + ["sync"], cwd=bare, expect=1)
    r.check("names the missing file", "tasks.yaml" in p.stdout)
    os.rename(h, h + "-moved")
    p = r.run("configured vault without its folder", vo + ["status"], expect=2)
    r.check("says the folder is missing, not the vault", "No VaultOS folder inside this vault" in p.stdout)
    os.rename(h + "-moved", h)
    nogit = dict(env, PATH=os.path.dirname(sys.executable))
    p = subprocess.run(vo + ["new", "nogit"], env=nogit, capture_output=True, text=True)
    r.check("new without git does not crash", p.returncode == 0 and "Traceback" not in p.stderr, p.stdout[-120:])

    print("\n[9] Korean output / 한국어 출력")
    env_ko = dict(env, VAULTOS_LANG="ko")
    p = subprocess.run(vo + ["status"], env=env_ko, capture_output=True, text=True)
    r.check("status in Korean", "코드 폴더" in p.stdout and "Traceback" not in p.stderr)

    failed = [n for n, ok in r.results if not ok]
    print(f"\nResult  {len(r.results) - len(failed)}/{len(r.results)} passed")
    if args.keep or failed:
        print(f"kept: {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
