"""Regression: fresh demo records must survive a separate installed CLI process."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class RetainedWorkflowTests(unittest.TestCase):
    def test_kept_demo_persists_recaptured_manifest_for_actual_cli(self):
        script = Path(__file__).resolve().parents[1] / "examples" / "workflow.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            demo = subprocess.run([sys.executable, str(script), "--keep", str(root)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            self.assertEqual(json.loads(demo.stdout)["after_execution_and_recapture_stale"], [])
            cli = [sys.executable, "-m", "lineagefrontier", "plan", str(root / "manifest.json"),
                   "--root", str(root), "--request", "release"]
            result = subprocess.run(cli, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["assessment"]["stale"], [])
            self.assertEqual(report["plan"]["cost"], 0)
            self.assertEqual(report["plan"]["execution_order"], [])
            revoked = subprocess.run(cli + ["--revoke", "raw=withdrawn"],
                                     capture_output=True, text=True, check=False)
            self.assertEqual(revoked.returncode, 0, revoked.stderr)
            replacement = json.loads(revoked.stdout)["plan"]
            self.assertEqual(replacement["cost"], 15)
            self.assertEqual(replacement["execution_order"], ["recover-clean", "fit-batch", "chart", "bundle"])
