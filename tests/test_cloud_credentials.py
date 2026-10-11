"""Credential loading must never require committing a secret."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import cloud_credentials


class CloudCredentialTests(unittest.TestCase):
    def test_parses_export_style_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tableau.env"
            path.write_text(
                "# comment\n"
                "export TABLEAU_SERVER_URL=https://example.online.tableau.com\n"
                "export TABLEAU_SITE_ID='mysite'\n"
                'TABLEAU_TOKEN_NAME="mytoken"\n'
                "TABLEAU_TOKEN_SECRET=s3cret\n",
                encoding="utf-8",
            )
            values = cloud_credentials.parse_env_file(path)
            self.assertEqual(values["TABLEAU_SERVER_URL"], "https://example.online.tableau.com")
            self.assertEqual(values["TABLEAU_SITE_ID"], "mysite")
            self.assertEqual(values["TABLEAU_TOKEN_NAME"], "mytoken")
            self.assertEqual(values["TABLEAU_TOKEN_SECRET"], "s3cret")

    def test_process_environment_wins_over_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tableau.env"
            path.write_text(
                "TABLEAU_SERVER_URL=https://file\n"
                "TABLEAU_SITE_ID=file\n"
                "TABLEAU_TOKEN_NAME=file\n"
                "TABLEAU_TOKEN_SECRET=file\n",
                encoding="utf-8",
            )
            saved = {key: os.environ.get(key) for key in cloud_credentials.REQUIRED}
            try:
                for key in cloud_credentials.REQUIRED:
                    os.environ.pop(key, None)
                os.environ["TABLEAU_TOKEN_SECRET"] = "from-env"
                resolved = cloud_credentials.load_credentials(path)
                self.assertEqual(resolved["TABLEAU_TOKEN_SECRET"], "from-env")
                self.assertEqual(resolved["TABLEAU_SERVER_URL"], "https://file")
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_missing_credentials_raise_actionable_error(self):
        with TemporaryDirectory() as directory:
            saved = {key: os.environ.get(key) for key in cloud_credentials.REQUIRED}
            try:
                for key in cloud_credentials.REQUIRED:
                    os.environ.pop(key, None)
                with self.assertRaises(RuntimeError) as caught:
                    cloud_credentials.require_credentials(Path(directory) / "absent.env")
                message = str(caught.exception)
                self.assertIn("TABLEAU_TOKEN_SECRET", message)
                self.assertIn("cloud_credentials.py", message)
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_default_file_is_outside_the_repository(self):
        resolved = cloud_credentials.DEFAULT_ENV_FILE.resolve()
        repo_root = Path(__file__).resolve().parents[1]
        self.assertFalse(
            str(resolved).startswith(str(repo_root)),
            "The default credential file must live outside the repository",
        )


if __name__ == "__main__":
    unittest.main()
