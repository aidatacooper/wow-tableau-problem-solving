"""Load Tableau Cloud credentials from the operator's private env file.

Credentials are never committed. They live outside the repository at
``~/.config/wow-cloud/tableau.env`` (owner-only permissions) and are read only
from the process environment, matching the rule in ``docs/ten-case-cloud-review.md``:
"Do not store the secret in the repository."

Resolution order for each variable:

1. an already-exported process environment variable (CI, or an operator who
   sourced the file themselves);
2. the ``WOW_CLOUD_ENV`` file if that variable names one;
3. the default file at ``~/.config/wow-cloud/tableau.env``.

Usage::

    from scripts.cloud_credentials import load_credentials
    load_credentials()  # populates os.environ, returns the four values

    from scripts.cloud_credentials import require_credentials
    credentials = require_credentials()  # raises with an actionable message
"""

from __future__ import annotations

import os
import re
from pathlib import Path

#: Variables that together identify a Tableau Cloud personal access token.
REQUIRED = (
    "TABLEAU_SERVER_URL",
    "TABLEAU_SITE_ID",
    "TABLEAU_TOKEN_NAME",
    "TABLEAU_TOKEN_SECRET",
)

DEFAULT_ENV_FILE = Path("~/.config/wow-cloud/tableau.env").expanduser()
_ENV_VAR = "WOW_CLOUD_ENV"
_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def env_file() -> Path:
    """Return the credential file this process should read."""
    override = os.environ.get(_ENV_VAR)
    return Path(override).expanduser() if override else DEFAULT_ENV_FILE


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a shell-style ``export KEY=VALUE`` file without executing it."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def load_credentials(path: Path | None = None) -> dict[str, str]:
    """Populate ``os.environ`` from the credential file and return all values.

    Existing process environment variables win, so a CI secret or an operator
    who already exported the values is never overridden by the file.
    """
    source = Path(path).expanduser() if path else env_file()
    file_values: dict[str, str] = {}
    if source.is_file():
        file_values = parse_env_file(source)
    resolved: dict[str, str] = {}
    for key in REQUIRED:
        value = os.environ.get(key) or file_values.get(key)
        if value:
            os.environ[key] = value
            resolved[key] = value
    return resolved


def require_credentials(path: Path | None = None) -> dict[str, str]:
    """Like :func:`load_credentials`, but fail loudly on a partial file."""
    resolved = load_credentials(path)
    missing = [key for key in REQUIRED if not resolved.get(key)]
    if missing:
        source = Path(path).expanduser() if path else env_file()
        raise RuntimeError(
            f"Missing Tableau Cloud credentials: {', '.join(missing)}. "
            f"Export them, or write {source} with one `export KEY=VALUE` per line "
            f"(keep it owner-only). See scripts/cloud_credentials.py."
        )
    return resolved
