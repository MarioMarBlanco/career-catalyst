"""Career Catalyst package."""

from .config import DEFAULT_CV_PATH, DEFAULT_JOB_PATH, normalize_path, resolve_cv_path, resolve_jobs_path
from .jev import build_questions, discover_job_files, evaluate_cv_job_affinity, normalize_score, rank_jobs_for_cv

__all__ = [
    "DEFAULT_CV_PATH",
    "DEFAULT_JOB_PATH",
    "build_questions",
    "discover_job_files",
    "evaluate_cv_job_affinity",
    "normalize_path",
    "normalize_score",
    "rank_jobs_for_cv",
    "resolve_cv_path",
    "resolve_jobs_path",
]
