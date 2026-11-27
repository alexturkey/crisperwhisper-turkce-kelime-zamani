"""scripts/tani.sh SAPMA section (kit KL-23): variable names only, never values; no network.
Needs bash on PATH (Linux, WSL, Git Bash); skipped otherwise. Run: python -B -m unittest discover -s tests"""
import os
import pathlib
import shutil
import subprocess
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash not found")
class Sapma(unittest.TestCase):
    def test_ad_gorunur_deger_gizli(self):
        deger = "gizli" + "Deger" + "12345"
        env = dict(os.environ, STT_TEST_EZME=deger)
        p = subprocess.run([BASH, str(REPO / "scripts" / "tani.sh")], capture_output=True, env=env, timeout=120)
        out = p.stdout.decode("utf-8", "replace")
        self.assertEqual(p.returncode, 0, out[-300:])
        self.assertIn("SAPMA / DEVIATIONS", out)
        self.assertIn("STT_TEST_EZME", out)
        self.assertNotIn(deger, out)


if __name__ == "__main__":
    unittest.main()
