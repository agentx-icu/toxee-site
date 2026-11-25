"""Exercise the real workflow shell against a local Git remote and a fake API.

No network, GitHub token or third-party Python package is used. The API shim
injects failures at the boundaries where a successful push must remain retryable.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parent.parent


class ReleaseSyncRetryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-sync-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / "work"
        self.state = self.root / "state"
        self.state.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        remote = self.root / "origin.git"
        self.command(["git", "init", "--bare", str(remote)], cwd=self.root)
        self.command(["git", "init", "-b", "master", str(self.work)], cwd=self.root)
        for args in (("config", "user.name", "Release test"),
                     ("config", "user.email", "test@example.invalid"),
                     ("remote", "add", "origin", str(remote))):
            self.command(["git", *args])
        self.manifest = self.work / "release-manifest.json"
        self.manifest.write_text("{}\n")
        self.command(["git", "add", "."])
        self.command(["git", "commit", "-m", "baseline"])
        self.command(["git", "push", "-u", "origin", "master"])
        self.command(["git", "switch", "-c", "automation/release-v1.2.3"])
        shim = self.bin / "gh"
        shim.write_text('''#!/bin/sh
case "$1 $2" in
  "pr list") if [ -f "$SYNC_TEST_STATE/pr" ]; then echo 42; fi ;;
  "pr create")
    if [ -f "$SYNC_TEST_STATE/fail-pr" ]; then rm "$SYNC_TEST_STATE/fail-pr"; exit 1; fi
    touch "$SYNC_TEST_STATE/pr" ;;
  "run list")
    requested=""
    while [ "$#" -gt 0 ]; do
      if [ "$1" = --commit ]; then shift; requested="$1"; fi
      shift
    done
    if [ -f "$SYNC_TEST_STATE/check" ] && [ "$(cat "$SYNC_TEST_STATE/check")" = "$requested" ]; then echo 1; else echo 0; fi ;;
  "workflow run")
    if [ -f "$SYNC_TEST_STATE/fail-check" ]; then rm "$SYNC_TEST_STATE/fail-check"; exit 1; fi
    git rev-parse HEAD > "$SYNC_TEST_STATE/check"
    echo dispatch >> "$SYNC_TEST_STATE/dispatches" ;;
  *) exit 8 ;;
esac
''')
        shim.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(PATH=str(self.bin) + os.pathsep + self.env["PATH"],
                        RELEASE_BRANCH="automation/release-v1.2.3", RELEASE_TAG="v1.2.3",
                        DEFAULT_BRANCH="master", RUNNER_TEMP=str(self.root),
                        SYNC_TEST_STATE=str(self.state))
        workflow = (ROOT / ".github/workflows/release-sync.yml").read_text()
        step = workflow.split("      - name: Open or refresh the synchronization pull request\n", 1)[1]
        self.script = textwrap.dedent(step.split("        run: |\n", 1)[1])

    def command(self, args, cwd=None, expected=0, env=None):
        result = subprocess.run(args, cwd=cwd or self.work, env=env, text=True,
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout.strip()

    def invoke(self, expected=0):
        return self.command(["bash", "-c", self.script], expected=expected, env=self.env)

    def test_push_then_failed_pr_creation_retries_without_new_commit(self):
        self.manifest.write_text('{"version":"1.2.3"}\n')
        (self.state / "fail-pr").touch()
        self.invoke(expected=1)
        sha = self.command(["git", "rev-parse", "HEAD"])
        self.assertFalse((self.state / "pr").exists())
        self.assertEqual(self.command(["git", "status", "--porcelain"]), "")
        self.invoke()
        self.assertTrue((self.state / "pr").exists())
        self.assertEqual(self.command(["git", "rev-parse", "HEAD"]), sha)
        self.assertEqual((self.state / "check").read_text().strip(), sha)

    def test_created_pr_with_failed_check_dispatch_is_retryable(self):
        self.manifest.write_text('{"version":"1.2.3"}\n')
        (self.state / "fail-check").touch()
        self.invoke(expected=1)
        self.assertTrue((self.state / "pr").exists())
        self.assertFalse((self.state / "check").exists())
        self.invoke()
        self.assertTrue((self.state / "check").exists())
        self.invoke()
        self.assertEqual((self.state / "dispatches").read_text().splitlines(), ["dispatch"])

    def test_same_tag_correction_updates_existing_branch_without_force(self):
        self.manifest.write_text('{"version":"1.2.3"}\n')
        self.invoke()
        first = self.command(["git", "rev-parse", "HEAD"])
        self.manifest.write_text('{"version":"1.2.3","corrected":true}\n')
        self.invoke()
        final = self.command(["git", "rev-parse", "HEAD"])
        self.assertNotEqual(first, final)
        self.command(["git", "merge-base", "--is-ancestor", first, final])
        self.assertEqual((self.state / "check").read_text().strip(), final)


if __name__ == "__main__":
    unittest.main()
