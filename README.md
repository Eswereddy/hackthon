---
title: Real-World OpenEnv Benchmark
emoji: "🤖"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
---

# Real-World OpenEnv Benchmark

This repository provides a realistic, non-toy OpenEnv environment built for hackathon evaluation. It simulates practical customer support workflows that humans perform in real organizations:
- Email triage
- Ticket routing
- Content moderation

## Motivation

Most benchmark environments are either narrow or game-like. This environment emphasizes routine but high-impact support operations tasks requiring judgment, policy adherence, and safe behavior under constraints.

## OpenEnv Compliance

The environment implements the required OpenEnv-style interface:
- Typed models for observation, action, and reward via Pydantic
- `reset()` returns the initial observation
- `step(action)` returns `(observation, reward, done, info)`
- `state()` returns the current environment state
- Metadata provided in `openenv.yaml`

Primary implementation:
- Environment: `src/openenv_hackathon/environment.py`
- Models: `src/openenv_hackathon/models.py`
- Tasks and graders: `src/openenv_hackathon/tasks.py`

## Action Space

`Action` model fields:
- `action_type` (enum)
- `payload` (object)

Supported actions:
- `triage_email`: `{ "message_id": int, "category": "urgent|normal|spam" }`
- `route_ticket`: `{ "ticket_id": int, "queue": "technical|billing|general", "priority": "p1|p2|p3" }`
- `moderate_content`: `{ "post_id": int, "decision": "allow|warn|remove" }`
- `noop`: `{}`
- `delete_all`: `{}` (intentionally destructive and penalized)

## Observation Space

`Observation` model fields:
- `task_id`
- `difficulty` (`easy`, `medium`, `hard`)
- `objective`
- `context` (task-local state with target answers hidden)
- `progress` (grader score in `[0.0, 1.0]`)
- `remaining_steps`
- `recent_feedback`

## Tasks and Difficulty Levels

1. `email_triage` (easy)
Objective: label customer/support inbox items as urgent, normal, or spam.
Grader: exact-match label accuracy across all messages.

2. `ticket_routing` (medium)
Objective: assign each incoming support ticket to the right queue and priority.
Grader: exact match on queue+priority per ticket.

3. `content_moderation` (hard)
Objective: moderate support community content with allow/warn/remove policy actions.
Grader: per-post policy decision accuracy with penalty for over-action.

All graders are deterministic and return a score in `[0.0, 1.0]`.

## Reward Design

Reward is shaped during the trajectory, not only at terminal states:
- Positive reward for correct incremental actions
- Additional reward component for immediate score improvement
- Penalties for invalid actions, repeated-loop actions, and destructive behavior

This encourages steady progress and discourages random or unsafe policies.

Safety controls included:
- Unsafe action counter (invalid, destructive, repeated-loop behavior)
- Early safety cutoff when unsafe behavior persists
- Additional step telemetry: score delta and cumulative safety violations in `info`

## Setup

```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## Run Locally

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

API endpoints for interactive environment control:
- `GET /tasks`
- `POST /reset?task_id=email_triage`
- `POST /step` (JSON body follows `Action` model)
- `GET /state`
- `GET /metrics`
- `GET /action-space`
- `POST /simulate` (batch actions with optional reset)

## One-Command Preflight

Run local readiness checks (task mechanics + deterministic baseline):

```bash
python preflight.py
```

## Validate OpenEnv Spec

If `openenv` CLI is available in your environment:

```bash
openenv validate
```

If it is not installed, use the official hackathon/OpenEnv validator installation instructions first, then run the same command.

## Baseline Inference (OpenAI Client)

The baseline runner evaluates all tasks with a deterministic decoding setup.

Requirements:
- Set API credential in `HF_TOKEN`

Run:

```bash
HF_TOKEN=<your_token> python baseline_inference.py --model gpt-4.1-mini --max-turns 10
```

Fully local deterministic reference baseline:

```bash
python baseline_inference.py --policy heuristic --max-turns 10
```

Output:
- Per-task score in `[0.0, 1.0]`
- Mean benchmark score across all tasks

## Baseline Performance Scores

Reference baseline configuration:
- Model: `gpt-4.1-mini`
- Temperature: `0`
- Max turns per task: `10`

Measured deterministic reference baseline (`--policy heuristic`, max-turns `10`):

| Task | Score |
|---|---:|
| email_triage | 1.0000 |
| ticket_routing | 1.0000 |
| content_moderation | 1.0000 |
| average | 1.0000 |

Reproducibility notes:
- The environment itself is deterministic.
- Remaining variance is model/provider-side.
- Keep identical model name and parameters for stable comparisons.

## Containerized Execution

Build:

```bash
docker build -t real-world-openenv .
```

Run:

```bash
docker run --rm -p 7860:7860 real-world-openenv
```

## Automated Windows Deployment

You can run end-to-end checks/build with one command:

```powershell
./deploy.ps1
```

Optional flags:
- `-SkipValidator`
- `-SkipDocker`

## Hugging Face Spaces Deployment

This repo is configured for Docker Spaces via README frontmatter (`sdk: docker`) and includes the `openenv` tag.

Minimal HF Space steps:
1. Create a new Space with Docker SDK.
2. Push this repository.
3. Ensure any required secrets (for baseline runs) are set, including `HF_TOKEN`.

Automated Space deployment:

```bash
HF_TOKEN=<your_hf_token> python deploy_hf_space.py
```

Optional custom Space id:

```bash
HF_SPACE_ID=<username>/<space_name> HF_TOKEN=<your_hf_token> python deploy_hf_space.py
```
