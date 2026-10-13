import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from vaultos_core import bind, grill, home, upgrade, validate  # noqa: E402
from vaultos_core.i18n import set_lang  # noqa: E402
from vaultos_core.yamlish import load  # noqa: E402


class TempHome(unittest.TestCase):
    """Each test gets its own HOME so the real ~/.config/vaultos is never read."""

    def setUp(self):
        set_lang("en")
        self.tmp = tempfile.mkdtemp(prefix="vaultos-test-")
        self._home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp, "home")
        os.makedirs(os.environ["HOME"])

    def tearDown(self):
        if self._home is not None:
            os.environ["HOME"] = self._home
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p


class Validate(TempHome):
    def repo_with(self, tasks):
        repo = os.path.join(self.tmp, "repo")
        bind.bind(repo, "demo")
        self.write("repo/tracker/tasks.yaml", "tasks:\n" + tasks)
        return repo

    def run_check(self, tasks):
        repo = self.repo_with(tasks)
        return validate.check(repo, None, {"project": "demo", "project_path": "projects/demo"})

    def test_clean(self):
        v, w, f = self.run_check("  - id: T-1\n    title: a\n    status: ready\n    requirement_ids: [R-1]\n")
        self.assertEqual((v, w), ([], []))
        self.assertEqual(f["tasks"], 1)

    def test_done_rules(self):
        v, w, _ = self.run_check("  - id: T-1\n    title: a\n    status: done\n    requirement_ids: [R-1]\n")
        self.assertTrue(any("without evidence" in x for x in v))
        self.assertTrue(any("without done_at" in x for x in w))
        self.assertTrue(any("without owner" in x for x in w))

    def test_unlinked_dup_date(self):
        v, _w, _ = self.run_check("  - id: T-1\n    title: a\n    status: ready\n    requirement_ids: []\n"
                                  "  - id: T-1\n    title: b\n    status: ready\n    requirement_ids: [R]\n    due: 10/30\n")
        text = " ".join(v)
        self.assertIn("not linked", text)
        self.assertIn("duplicate task ids: T-1", text)
        self.assertIn("T-1.due=10/30", text)

    def test_bad_yaml_is_a_violation(self):
        v, _w, _ = self.run_check("  - id: T-1\n    title: a: b\n")
        self.assertTrue(any("line 3" in x for x in v))

    def test_vault_side(self):
        vault = os.path.join(self.tmp, "vault")
        os.makedirs(vault)
        h, _ = home.create(vault, "VaultOS", "en")
        pdir = os.path.join(h, "projects", "demo")
        self.write("vault/VaultOS/projects/demo/project.yaml", "grill: pending\n")
        self.write("vault/VaultOS/projects/demo/requirements/requirements.yaml",
                   "requirements:\n  - id: R-1\n  - id: R-2\n")
        repo = self.repo_with("  - id: T-1\n    title: a\n    status: ready\n    requirement_ids: [R-1, R-9]\n")
        v, w, f = validate.check(repo, h, {"project": "demo", "project_path": "projects/demo"}, "light")
        self.assertTrue(any("pending" in x for x in v))
        self.assertTrue(any("R-9" in x for x in v))
        self.assertTrue(any("R-2" in x for x in w))
        self.assertEqual(f["requirements"], 2)
        self.assertTrue(os.path.isdir(pdir))


class Grill(TempHome):
    def test_find_plan_docs_english_and_korean(self):
        repo = os.path.join(self.tmp, "r")
        self.write("r/docs/plan.md", "# x")
        self.write("r/docs/requirements.md", "# x")
        self.write("r/notes/planet.md", "# not a plan")
        plan, req = grill.find_plan_docs(repo)
        self.assertTrue(plan.endswith(os.path.join("docs", "plan.md")))
        self.assertTrue(req.endswith(os.path.join("docs", "requirements.md")))
        repo2 = os.path.join(self.tmp, "k")
        self.write("k/기획문서.md", "# x")
        self.assertTrue(grill.find_plan_docs(repo2)[0].endswith("기획문서.md"))

    def test_requirements_are_valid_yaml(self):
        pdir = os.path.join(self.tmp, "p")
        ans = {"features": 'Login: Google, Say "hi" # now', "success": "a: b", "verification": "x"}
        ids = grill.write_requirements(pdir, "my-app", ans)
        data = load(os.path.join(pdir, "requirements", "requirements.yaml"))
        self.assertEqual(ids, ["REQ-MYAPP-001", "REQ-MYAPP-002"])
        self.assertEqual(data["requirements"][1]["statement"], 'Say "hi" # now')
        self.assertEqual(data["requirements"][0]["acceptance"], ["a: b"])

    def test_tasks_and_gate(self):
        repo = os.path.join(self.tmp, "repo")
        os.makedirs(repo)
        ans = {"features": "A, B", "verification": "tests"}
        path = grill.write_tasks(repo, ans, ["R-1", "R-2"], "APP")
        tasks = load(path)["tasks"]
        self.assertEqual(len(tasks), 6)
        self.assertEqual(tasks[3]["requirement_ids"], ["R-2"])
        self.assertIsNone(grill.write_tasks(repo, ans, ["R-1"], "APP"))  # never overwrites real tasks
        self.assertEqual(grill.gate_status({})[0], "pending")


class Upgrade(TempHome):
    def setUp(self):
        super().setUp()
        self.vault = os.path.join(self.tmp, "vault")
        os.makedirs(self.vault)
        self.h, _ = home.create(self.vault, "VaultOS", "en")

    def kinds(self):
        return {rel: kind for kind, rel, _c in upgrade.plan(self.h)}

    def test_fresh_is_same(self):
        self.assertEqual(set(self.kinds().values()), {"same"})

    def test_states(self):
        h = self.h
        with open(os.path.join(h, "governance", "README.md"), "a", encoding="utf-8") as fh:
            fh.write("\nmine\n")
        os.remove(os.path.join(h, "governance", "agent-policy.md"))
        with open(os.path.join(h, home.BASE, "system", "VAULTOS.md"), "w", encoding="utf-8") as fh:
            fh.write("old\n")
        with open(os.path.join(h, "system", "VAULTOS.md"), "w", encoding="utf-8") as fh:
            fh.write("old\n")
        with open(os.path.join(h, "system", "upgrade-keep.txt"), "a", encoding="utf-8") as fh:
            fh.write("governance/README.md\n")
        k = self.kinds()
        self.assertEqual(k["governance/README.md"], "keep")
        self.assertEqual(k["governance/agent-policy.md"], "deleted")
        self.assertEqual(k["system/VAULTOS.md"], "replace")

    def test_create_refuses(self):
        with self.assertRaises(ValueError):
            home.create(self.vault, "VaultOS", "en")
        with self.assertRaises(ValueError):
            home.create(os.path.join(self.tmp, "missing"), "VaultOS", "en")
        with self.assertRaises(ValueError):
            home.create(self.vault, "../x", "en")


if __name__ == "__main__":
    unittest.main()
