from pathlib import Path

import pytest

from career_catalyst.config import normalize_path, resolve_jobs_path
from career_catalyst.jev import build_questions, normalize_score


def test_normalize_path_supports_windows_drive_mapping():
    result = normalize_path(r"M:\tool-outputs\career-catalyst")
    assert result == Path("/mnt/m/tool-outputs/career-catalyst")


def test_resolve_jobs_path_uses_environment_fallback():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("CAREER_CATALYST_JOBS_PATH", r"M:\tool-outputs\career-catalyst")
    result = resolve_jobs_path(None)
    assert result == Path("/mnt/m/tool-outputs/career-catalyst")
    monkeypatch.undo()


def test_build_questions_contains_affinity_dimensions():
    questions = build_questions()
    assert "overall_affinity" in questions
    assert "skills_match" in questions
    assert "experience_fit" in questions
    assert "role_fit" in questions


def test_normalize_score_handles_fractional_probability():
    assert normalize_score(0.0) == 0.0
    assert normalize_score(0.5) == 50.0
    assert normalize_score(1.0) == 100.0
    assert normalize_score(0.25) == 25.0
    assert normalize_score(1.49, maximum=4.0) == 37.25

    with pytest.raises(ValueError):
        normalize_score(-0.1)
    with pytest.raises(ValueError):
        normalize_score(1.1)
    with pytest.raises(ValueError):
        normalize_score(4.1, maximum=4.0)
