# Hackathon Submission Report

## Selected Domain
Customer Support Operations

## Environment Summary
This environment simulates realistic support operations tasks performed by human teams:
1. Email triage (easy)
2. Ticket routing (medium)
3. Content moderation (hard)

## Functional Requirements Coverage
1. Real-world task simulation
- All tasks are practical support workflows used in production support orgs.

2. OpenEnv interface compliance
- Typed Pydantic models for Observation, Action, Reward.
- step(action) -> (observation, reward, done, info)
- reset() -> initial observation
- state() -> current state
- openenv.yaml metadata included

3. Three tasks with deterministic graders
- Each task has a clear objective and deterministic scoring in [0.0, 1.0].
- Difficulty progression: easy -> medium -> hard.

4. Meaningful reward shaping
- Incremental positive rewards for correct progress.
- Penalties for invalid actions, repeated loops, and destructive actions.

5. Baseline inference
- OpenAI API client path available in baseline_inference.py.
- Credentials read from HF_TOKEN.
- Deterministic local baseline mode available for reproducibility.

## Non-Functional Requirements Coverage
1. Hugging Face Spaces
- Docker Space frontmatter present in README.
- openenv tag included.

2. Containerized execution
- Dockerfile included and configured for app startup on port 7860.

3. Documentation
- README includes overview, spaces definitions, task details, setup, usage, and baseline scores.

## Local Validation Results
Command: python preflight.py

Result:
- PASS openenv.yaml present
- PASS deterministic task scores:
  - email_triage: 1.0
  - ticket_routing: 1.0
  - content_moderation: 1.0
- PASS baseline heuristic mode:
  - average: 1.0

## Final Commands To Run On Submission Machine
1. Install dependencies
- pip install -r requirements.txt

2. Run local preflight
- python preflight.py

3. Run official validator
- openenv validate

4. Build and run container
- docker build -t real-world-openenv .
- docker run --rm -p 7860:7860 real-world-openenv

## Notes
If docker build or openenv validate cannot run locally, execute them in a machine with Docker daemon and official hackathon OpenEnv validator installed.
