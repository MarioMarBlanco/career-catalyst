from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CV_PATH = REPO_ROOT / "cv" / "mario-martin-blanco.ai.md"
DEFAULT_JOB_PATH = Path("/mnt/m/tool-outputs/career-catalyst")


def normalize_path(value: str | os.PathLike[str] | None) -> Path:
    if value is None:
        return DEFAULT_JOB_PATH

    raw = str(value).strip()
    if not raw:
        return DEFAULT_JOB_PATH

    if raw.startswith("/"):
        return Path(raw).expanduser().resolve()

    if len(raw) >= 2 and raw[1] == ":":
        drive = raw[0].lower()
        remainder = raw[2:].replace("\\", "/")
        return Path(f"/mnt/{drive}{remainder}").expanduser().resolve()

    return Path(raw).expanduser().resolve()


def resolve_jobs_path(cli_value: str | os.PathLike[str] | None) -> Path:
    if cli_value is not None:
        return normalize_path(cli_value)

    env_value = os.getenv("CAREER_CATALYST_JOBS_PATH")
    if env_value:
        return normalize_path(env_value)

    return DEFAULT_JOB_PATH


def resolve_cv_path(cli_value: str | os.PathLike[str] | None) -> Path:
    if cli_value is not None:
        return normalize_path(cli_value)

    return DEFAULT_CV_PATH
