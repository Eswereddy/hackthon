# Final Submission Text (Copy/Paste)

## Project Title
Real-World OpenEnv Benchmark: Customer Support Operations

## Environment Overview
This project implements a realistic OpenEnv environment focused on customer support operations tasks that humans perform in real organizations.

Domain tasks:
1. Email triage (easy)
2. Ticket routing (medium)
3. Content moderation (hard)

These are non-toy workflows with deterministic grading and reward shaping for incremental progress.

## OpenEnv Specification Compliance
The environment implements:
1. Typed Pydantic models for Observation, Action, Reward
2. reset() -> initial Observation
3. step(action) -> (observation, reward, done, info)
4. state() -> current state
5. openenv.yaml metadata file

Main implementation files:
- src/openenv_hackathon/models.py
- src/openenv_hackathon/environment.py
- src/openenv_hackathon/tasks.py
- openenv.yaml

## Tasks and Graders
1. email_triage (easy)
- Objective: classify messages as urgent/normal/spam
- Grader: exact-match accuracy over all messages

2. ticket_routing (medium)
- Objective: assign ticket queue + priority
- Grader: exact route match per ticket

3. content_moderation (hard)
- Objective: choose allow/warn/remove for posts
- Grader: per-post policy accuracy with over-action penalty

All graders are deterministic and return score in [0.0, 1.0].

## Reward Function
The reward function is trajectory-shaped:
1. Positive reward for correct incremental actions
2. Score-improvement bonus across steps
3. Penalties for invalid actions
4. Penalties for repeated-loop behavior
5. Penalties for destructive actions

## Baseline Inference
The baseline inference script is implemented in baseline_inference.py.

Requirements:
1. OpenAI client path uses HF_TOKEN environment variable
2. Reproducible deterministic local baseline mode available via --policy heuristic

Example commands:
- HF_TOKEN=<token> python baseline_inference.py --model gpt-4.1-mini --max-turns 10
- python baseline_inference.py --policy heuristic --max-turns 10

## Non-Functional Requirements
### Hugging Face Spaces
1. README frontmatter is configured for Docker Space
2. openenv tag included

### Containerized Execution
Dockerfile provided and validated.

Build:
- docker build -t real-world-openenv .

Run:
- docker run --rm -p 7860:7860 real-world-openenv

### Documentation
README includes:
1. Environment overview and motivation
2. Action/observation space definitions
3. Task descriptions and difficulty levels
4. Setup and usage instructions
5. Baseline performance scores

## Validation Evidence
Local preflight command:
- python preflight.py

Observed result:
- PASS openenv.yaml present
- PASS deterministic task scores
  - email_triage: 1.0
  - ticket_routing: 1.0
  - content_moderation: 1.0
- PASS baseline heuristic average: 1.0

Container runtime checks:
- curl http://localhost:7860/health -> {"status":"ok"}
- GET /tasks returns all three tasks

## Note on openenv validate
The official hackathon validator CLI command openenv validate depends on the exact validator toolchain provided by organizers. In this machine, openenv command was not available on PATH. The environment code and metadata are prepared for validator execution once the official CLI is installed.

## Included Automation
Windows deployment helper:
- deploy.ps1

One-command local checks/build flow:
- powershell -ExecutionPolicy Bypass -File .\deploy.ps1

Optional flags:
- -SkipValidator
- -SkipDocker
