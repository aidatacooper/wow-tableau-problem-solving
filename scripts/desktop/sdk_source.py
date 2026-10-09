"""Resolve which ``cwtwb`` checkout a build will import, and report it.

``cwtwb`` is installed editable, and the editable install points at one fixed
path (``<main-checkout>/cwtwb/src``). A build run from a Paseo worktree would
therefore silently import the main checkout's SDK, not the SDK worktree the
agent just edited. That failure is invisible: the build succeeds and the
change appears to have no effect.

``PYTHONPATH`` is honoured ahead of the editable path, so pointing it at an
SDK worktree's ``src`` directory selects that worktree reliably.

This module centralises the resolution so builders and wrappers agree on
which SDK is active.

Usage:
    python scripts/desktop/sdk_source.py            # report the active SDK
    python scripts/desktop/sdk_source.py --check     # also fail if unexpected
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

ENV_VAR = "CWTWB_SRC"


def resolve() -> str | None:
    """Return the ``src`` directory that should provide ``cwtwb``.

    Precedence:

    1. ``CWTWB_SRC`` environment variable, if it names an existing directory.
    2. ``PYTHONPATH`` entries that contain a ``cwtwb`` package.
    3. ``None``, meaning the ambient (editable) install is used.
    """
    override = os.environ.get(ENV_VAR)
    if override:
        path = Path(os.path.expandvars(override))
        if (path / "cwtwb" / "__init__.py").is_file():
            return str(path.resolve())
        if (path / "src" / "cwtwb" / "__init__.py").is_file():
            return str((path / "src").resolve())
        raise SystemExit(
            f"{ENV_VAR}={override!r} does not contain a cwtwb package "
            f"(looked for cwtwb/__init__.py and src/cwtwb/__init__.py)"
        )
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry)
        if (candidate / "cwtwb" / "__init__.py").is_file():
            return str(candidate.resolve())
    return None


def active_cwtwb() -> dict[str, str | None]:
    """Report where ``import cwtwb`` resolves, and how it was selected.

    A previously imported ``cwtwb`` is dropped when it does not come from the
    resolved directory, so changing the selection takes effect in a
    long-running process and not only in a fresh interpreter.
    """
    resolved = resolve()
    if resolved is not None:
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
        cached = sys.modules.get("cwtwb")
        cached_file = getattr(cached, "__file__", None) if cached else None
        if cached_file and Path(cached_file).resolve().parent.parent != Path(resolved):
            del sys.modules["cwtwb"]
    module = importlib.import_module("cwtwb")
    origin = getattr(module, "__file__", None)
    version = getattr(module, "__version__", None)
    root = None
    if origin:
        root = str(Path(origin).resolve().parents[1])
    return {
        "origin": origin,
        "version": version,
        "selected_by": ENV_VAR if os.environ.get(ENV_VAR) else (
            "PYTHONPATH" if resolved else "editable install"
        ),
        "sdk_root": root,
    }


def git_revision(sdk_root: str | None) -> str | None:
    """Return the short commit of the SDK checkout, when it is a git repo."""
    if not sdk_root:
        return None
    try:
        out = subprocess.check_output(
            ["git", "-C", sdk_root, "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    return out or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when an unexpected SDK is active",
    )
    parser.add_argument(
        "--expect",
        help="substring the resolved SDK path must contain",
    )
    args = parser.parse_args()

    info = active_cwtwb()
    info["git"] = git_revision(info["sdk_root"])
    for key in ("origin", "version", "git", "selected_by", "sdk_root"):
        print(f"{key:12s} {info.get(key)}")

    if args.expect and args.expect not in (info.get("sdk_root") or ""):
        print(
            f"ERROR: active SDK does not contain {args.expect!r}; "
            f"a build would use the wrong cwtwb",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
