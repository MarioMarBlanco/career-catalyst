from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .config import resolve_cv_path, resolve_jobs_path
from .jev import rank_jobs_for_cv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score a CV against job application Markdown files using the Jev API.")
    parser.add_argument("--cv", type=str, help="Path to the CV Markdown file.")
    parser.add_argument("--jobs-path", type=str, help="Directory containing the job application Markdown files.")
    parser.add_argument("--api-key", type=str, help="Vercel AI Gateway API key. Defaults to AI_GATEWAY_API_KEY.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output instead of a human-readable summary.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    cv_path = resolve_cv_path(args.cv)
    jobs_path = resolve_jobs_path(args.jobs_path)
    api_key = args.api_key or os.getenv("AI_GATEWAY_API_KEY") or os.getenv("COPILOT_PROVIDER_API_KEY")

    if not api_key:
        raise SystemExit("Missing API key. Set AI_GATEWAY_API_KEY or pass --api-key.")

    results = rank_jobs_for_cv(cv_path, jobs_path, api_key)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    print(f"CV: {cv_path}")
    print(f"Jobs directory: {jobs_path}")
    print()
    for index, result in enumerate(results, start=1):
        print(f"{index}. {Path(result['job_path']).name} - {result['affinity_0_100']:.2f}/100")
        print(f"   raw: {result['raw_scores']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
