from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

GATEWAY_URL = "https://ai-gateway.vercel.sh/v1/evaluate"
MODEL_ID = "typesafe-ai/jev"


def build_questions() -> dict[str, Any]:
    return {
        "overall_affinity": {
            "type": "score",
            "instructions": "Score how well the candidate CV matches this job description overall. Focus on relevant skills, domain experience, seniority, and role scope.",
            "criteria": [
                "Very poor fit: the CV misses the role's core requirements or signals a major mismatch.",
                "Weak fit: some transferable experience exists, but the main requirements are not well covered.",
                "Partial fit: the CV covers some key skills and experience, but important gaps remain.",
                "Strong fit: the CV covers most critical requirements and relevant domain experience.",
                "Exceptional fit: the CV directly matches the role's technical scope, responsibilities, and seniority."
            ],
        },
        "skills_match": {
            "type": "score",
            "instructions": "How well do the candidate's listed skills match the job's required technical and domain skills?",
            "criteria": [
                "No meaningful skill overlap",
                "Limited overlap",
                "Moderate overlap",
                "Strong overlap",
                "Excellent direct match"
            ],
        },
        "experience_fit": {
            "type": "score",
            "instructions": "How well does the candidate's career experience align with the job's relevant responsibilities and level of complexity?",
            "criteria": [
                "Poorly aligned experience",
                "Some relevant experience",
                "Relevant experience with gaps",
                "Mostly relevant experience",
                "Directly relevant experience"
            ],
        },
        "role_fit": {
            "type": "score",
            "instructions": "How appropriate is the candidate's seniority, education, and professional profile for the described role?",
            "criteria": [
                "Major mismatch",
                "Somewhat mismatched",
                "Reasonable fit",
                "Good fit",
                "Excellent fit"
            ],
        },
        "major_mismatch": {
            "type": "boolean",
            "instructions": "Is there a major blocker such as a clear mismatch in core domain, required seniority, or key hard skills?",
            "criteria": {
                "true": "There is a substantial blocker or mismatch.",
                "false": "No major blocker is evident."
            },
        },
    }


def normalize_score(raw_score: float, maximum: float = 1.0) -> float:
    score = float(raw_score)
    if maximum <= 0.0:
        raise ValueError(f"Score maximum must be greater than 0, got {maximum!r}")
    if not 0.0 <= score <= maximum:
        raise ValueError(
            f"Score must be between 0 and {maximum} inclusive, got {score!r}"
        )
    return round(score / maximum * 100.0, 2)


def _extract_score(answers: dict[str, Any], key: str) -> float:
    value = answers.get(key)
    if value is None:
        raise ValueError(f"Missing answer for question '{key}'")
    score = value.get("score")
    if score is None:
        raise ValueError(f"Question '{key}' did not return a numeric score field")
    return float(score)


def evaluate_cv_job_affinity(cv_text: str, job_text: str, api_key: str) -> dict[str, Any]:
    if not api_key:
        raise ValueError("AI_GATEWAY_API_KEY is required")

    payload = {
        "model": MODEL_ID,
        "state": {
            "cv": cv_text,
            "job_description": job_text,
        },
        "questions": build_questions(),
    }

    response = requests.post(
        GATEWAY_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=60,
    )

    if response.status_code >= 400:
        detail = response.text[:400]
        raise RuntimeError(f"Jev request failed with status {response.status_code}: {detail}")

    result = response.json()
    answers = result.get("answers")
    if not isinstance(answers, dict):
        raise RuntimeError("Jev response is missing the 'answers' payload")

    overall = _extract_score(answers, "overall_affinity")
    raw = {
        "overall_affinity": overall,
        "skills_match": _extract_score(answers, "skills_match"),
        "experience_fit": _extract_score(answers, "experience_fit"),
        "role_fit": _extract_score(answers, "role_fit"),
    }
    score_maximum = len(build_questions()["overall_affinity"]["criteria"]) - 1

    major_mismatch = answers.get("major_mismatch")
    mismatch_flag = False
    if isinstance(major_mismatch, dict):
        mismatch_flag = bool(major_mismatch.get("choice") == "true")

    return {
        "model": result.get("model"),
        "affinity_0_100": normalize_score(overall, score_maximum),
        "raw_scores": {key: round(value, 4) for key, value in raw.items()},
        "normalized_scores": {
            key: normalize_score(value, score_maximum) for key, value in raw.items()
        },
        "major_mismatch": mismatch_flag,
        "provider_metadata": result.get("providerMetadata"),
        "usage": result.get("usage"),
        "answers": answers,
    }


def discover_job_files(job_directory: str | os.PathLike[str]) -> list[Path]:
    directory = Path(job_directory).expanduser().resolve()
    if not directory.exists():
        raise FileNotFoundError(f"Job directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Job path is not a directory: {directory}")
    return sorted(path for path in directory.rglob("*.md") if path.is_file())


def rank_jobs_for_cv(cv_path: str | os.PathLike[str], jobs_path: str | os.PathLike[str], api_key: str) -> list[dict[str, Any]]:
    cv_file = Path(cv_path).expanduser().resolve()
    if not cv_file.exists():
        raise FileNotFoundError(f"CV file does not exist: {cv_file}")

    cv_text = cv_file.read_text(encoding="utf-8")
    ranked: list[dict[str, Any]] = []

    for job_file in discover_job_files(jobs_path):
        job_text = job_file.read_text(encoding="utf-8")
        result = evaluate_cv_job_affinity(cv_text, job_text, api_key)
        ranked.append(
            {
                "job_id": job_file.stem,
                "job_path": str(job_file),
                "affinity_0_100": result["affinity_0_100"],
                "raw_scores": result["raw_scores"],
                "normalized_scores": result["normalized_scores"],
                "major_mismatch": result["major_mismatch"],
                "model": result["model"],
            }
        )

    ranked.sort(key=lambda item: item["affinity_0_100"], reverse=True)
    return ranked
