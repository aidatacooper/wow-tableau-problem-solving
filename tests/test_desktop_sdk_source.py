"""The SDK resolver must select the requested cwtwb checkout.

``cwtwb`` is installed editable, so ``import cwtwb`` silently resolves to one
fixed checkout. A build run from a Paseo worktree would then import the wrong
SDK and make an SDK change look ineffective. These tests pin the precedence
that makes the selection explicit and checkable.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.desktop import sdk_source


def make_sdk(root: Path) -> Path:
    """Create a minimal ``src/cwtwb`` package and return its src directory."""
    src = root / "src"
    package = src / "cwtwb"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("__version__ = '0.0.0'\n", encoding="utf-8")
    return src


class SdkSourceTests(unittest.TestCase):
    def test_env_var_selects_that_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = make_sdk(Path(tmp))
            with patch.dict(os.environ, {sdk_source.ENV_VAR: str(src)}, clear=False):
                self.assertEqual(sdk_source.resolve(), str(src.resolve()))

    def test_env_var_accepts_the_checkout_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = make_sdk(root)
            with patch.dict(os.environ, {sdk_source.ENV_VAR: str(root)}, clear=False):
                self.assertEqual(sdk_source.resolve(), str(src.resolve()))

    def test_pythonpath_is_the_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = make_sdk(Path(tmp))
            env = {k: v for k, v in os.environ.items() if k != sdk_source.ENV_VAR}
            env["PYTHONPATH"] = str(src)
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(sdk_source.resolve(), str(src.resolve()))

    def test_env_var_wins_over_pythonpath(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            wanted = make_sdk(Path(first))
            other = make_sdk(Path(second))
            env = {"PYTHONPATH": str(other), sdk_source.ENV_VAR: str(wanted)}
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(sdk_source.resolve(), str(wanted.resolve()))

    def test_no_override_means_ambient_install(self):
        env = {k: v for k, v in os.environ.items() if k != sdk_source.ENV_VAR}
        env.pop("PYTHONPATH", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertIsNone(sdk_source.resolve())

    def test_missing_package_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {sdk_source.ENV_VAR: tmp}, clear=False):
                with self.assertRaises(SystemExit):
                    sdk_source.resolve()

    def test_active_reports_selection_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = make_sdk(Path(tmp))
            with patch.dict(os.environ, {sdk_source.ENV_VAR: str(src)}, clear=False):
                info = sdk_source.active_cwtwb()
                self.assertEqual(info["selected_by"], sdk_source.ENV_VAR)
                self.assertEqual(Path(info["sdk_root"]).resolve(), src.resolve())


if __name__ == "__main__":
    unittest.main()
