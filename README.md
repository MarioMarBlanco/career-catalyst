# career-catalyst

A small Python project for scoring a CV against Markdown job applications using the Jev evaluation API via Vercel AI Gateway.

## Installation

```bash
python3 -m pip install -e '.[dev]'
```

## Configuration

The job directory is configurable. The priority order is:

1. `--jobs-path` CLI argument
2. `CAREER_CATALYST_JOBS_PATH` environment variable
3. The default path: `/mnt/m/tool-outputs/career-catalyst`

This default matches the Windows path `M:\tool-outputs\career-catalyst` when accessed from WSL.

Set the Gateway key before running the tool:

```bash
export AI_GATEWAY_API_KEY="your-key"
```

## CLI usage

```bash
python3 -m career_catalyst --cv cv/mario-martin-blanco.ai.md --jobs-path /mnt/m/tool-outputs/career-catalyst --json
```

You can also rely on the environment variable:

```bash
export CAREER_CATALYST_JOBS_PATH="M:\tool-outputs\career-catalyst"
python3 -m career_catalyst --cv cv/mario-martin-blanco.ai.md --json
```

## Behavior

- Reads a single CV markdown file and all `.md` job files in the configured directory.
- Sends one Jev evaluation request per job.
- Uses a scored `overall_affinity` question as the ranking signal.
- Surfaces supporting score dimensions for skill, experience, role fit, and mismatch detection.
- Produces a deterministic 0–100 affinity score for each job.

This is a decision-support tool, not an autonomous hiring system. Use human review for high-risk decisions.
