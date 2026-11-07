import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "env.sh"


class LabEnvironmentTests(unittest.TestCase):
    def test_default_region_and_reused_credentials(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env.pop("LOCATION", None)
            env.pop("LAB_ENV_FILE", None)
            env["HOME"] = home
            command = ['bash', '-c', 'source "$1"; echo "$LOCATION"', 'bash', str(SCRIPT)]
            first = subprocess.check_output(command, env=env, text=True)
            saved = (Path(home) / ".aca-lab.env").read_text()
            second = subprocess.check_output(command, env=env, text=True)
            self.assertEqual(first, second)
            self.assertEqual(first.splitlines()[-1], "koreacentral")
            self.assertEqual((Path(home) / ".aca-lab.env").read_text(), saved)
            self.assertEqual((Path(home) / ".aca-lab.env").stat().st_mode & 0o777, 0o600)

    def test_custom_region_and_isolated_environment_file(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env.update(HOME=home, LOCATION="japaneast", LAB_ENV_FILE=str(Path(home) / "isolated.env"))
            output = subprocess.check_output(
                ['bash', '-c', 'source "$1"; echo "$LOCATION"', 'bash', str(SCRIPT)],
                env=env,
                text=True,
            )
            self.assertEqual(output.splitlines()[-1], "japaneast")
            self.assertTrue(Path(env["LAB_ENV_FILE"]).is_file())
            self.assertFalse((Path(home) / ".aca-lab.env").exists())


if __name__ == "__main__":
    unittest.main()
