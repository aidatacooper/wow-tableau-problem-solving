"""Classify whether Tableau Desktop opens a workbook, from Tableau's own log.

A failed load always logs ``show-detailed-error-dialog``; a successful load
logs ``end-workspace.load-workbook`` and never the error dialog. The
classifier matches the process Tableau actually launched by finding the
workbook path in the ``argv[1]`` record, then reads only that process's
records.

Tableau rotates ``log.txt`` to ``log_bk.txt`` at startup, so a before/after
size scan misses the new file. Every log line with a timestamp at or after
launch is scanned instead.

Tableau forwards a second launch to the running instance, so ``kill()`` must
run and wait for exit between tests or the verdict belongs to the wrong
process.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import time

DEFAULT_EXE = r"C:\Program Files\Tableau\Tableau 2026.2\bin\tableau.exe"

# Tableau localises the repository directory. The Chinese name is the one
# this project's capture machine uses; the English name is the default for an
# English install.
_LOG_DIR_CANDIDATES = (
    r"%USERPROFILE%\Documents\我的 Tableau 存储库\日志",
    r"%USERPROFILE%\Documents\My Tableau Repository\Logs",
)

LOADED = "LOADED"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"


def tableau_exe() -> str:
    """Return the Tableau Desktop executable to launch.

    ``TABLEAU_EXE`` overrides the default so the harness still works when a
    different Desktop version is the licensed target.
    """
    return os.environ.get("TABLEAU_EXE", DEFAULT_EXE)


def log_dir() -> str:
    """Return the directory holding Tableau's JSON log files."""
    override = os.environ.get("TABLEAU_LOG_DIR")
    if override:
        return os.path.expandvars(override)
    for candidate in _LOG_DIR_CANDIDATES:
        path = os.path.expandvars(candidate)
        if os.path.isdir(path):
            return path
    return os.path.expandvars(_LOG_DIR_CANDIDATES[0])


def logs() -> list[str]:
    """Return every Tableau log file, current and rotated."""
    return glob.glob(os.path.join(log_dir(), "log*.txt"))


def kill() -> None:
    """Stop Tableau and wait until it has exited.

    A second launch is forwarded to the running instance, so the next test
    would otherwise read the previous process's log lines.
    """
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Stop-Process -Name tableau,tabprotosrv,tabdoc -Force "
            "-ErrorAction SilentlyContinue",
        ],
        capture_output=True,
    )
    for _ in range(40):
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq tableau.exe", "/NH"],
            capture_output=True,
            text=True,
        ).stdout.lower()
        if "tableau.exe" not in out:
            break
        time.sleep(1)
    time.sleep(4)


def _records(since: str):
    """Yield log records whose timestamp is at or after ``since``."""
    for path in logs():
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except OSError:
            continue
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line or '"ts":"' not in line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("ts", "") >= since:
                yield record


def test(path: str, timeout: int = 120) -> str:
    """Open ``path`` in Desktop and return ``LOADED``, ``FAIL`` or ``UNKNOWN``.

    ``UNKNOWN`` means no verdict was reached in ``timeout`` seconds; treat it
    as a failure until re-verified, never as a pass.
    """
    name = os.path.basename(path)
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    proc = subprocess.Popen([tableau_exe(), path])
    pid = None
    loaded = False
    error = False
    started = time.time()
    while time.time() - started < timeout:
        time.sleep(2)
        for record in _records(since):
            value = record.get("v")
            text = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            if pid is None and name in text and "argv[1]" in text:
                pid = record.get("pid")
            if pid is None or record.get("pid") != pid:
                continue
            if record.get("k") == "end-workspace.load-workbook":
                loaded = True
            if "show-detailed-error-dialog" in text:
                error = True
        if loaded or error:
            break
    try:
        proc.terminate()
    except Exception:
        pass
    if error:
        return FAIL
    if loaded:
        return LOADED
    return UNKNOWN


def test_with_retries(path: str, tries: int = 3) -> str:
    """Run ``test`` up to ``tries`` times, returning the first real verdict."""
    verdict = UNKNOWN
    for _ in range(max(1, tries)):
        kill()
        verdict = test(path)
        if verdict != UNKNOWN:
            return verdict
    return verdict
