from __future__ import annotations

from fastapi import FastAPI
from pydantic import ValidationError

from src.openenv_hackathon.environment import RealWorldOpsEnv
from src.openenv_hackathon.models import Action, SimulationRequest, SimulationResponse

app = FastAPI(title="Real-World OpenEnv Benchmark")
env = RealWorldOpsEnv(task_id="email_triage")
env.reset()


@app.get("/")
def root() -> dict:
    obs = env.state().observation
    return {
        "message": "OpenEnv benchmark is running.",
        "tasks": env.tasks,
        "sample_observation": obs.model_dump() if obs else None,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tasks")
def tasks() -> dict:
    return {"tasks": env.tasks}


@app.post("/reset")
def reset(task_id: str = "email_triage") -> dict:
    observation = env.reset(task_id=task_id)
    return {"observation": observation.model_dump()}


@app.get("/state")
def state() -> dict:
    return env.state().model_dump()


@app.get("/metrics")
def metrics() -> dict:
    return env.metrics()


@app.get("/action-space")
def action_space() -> dict:
    return env.action_space()


@app.post("/step")
def step(action: Action) -> dict:
    try:
        observation, reward, done, info = env.step(action)
        return {
            "observation": observation.model_dump(),
            "reward": reward.model_dump(),
            "done": done,
            "info": info,
            "metrics": env.metrics(),
        }
    except ValidationError as exc:
        return {
            "error": "invalid_action_payload",
            "details": exc.errors(),
            "metrics": env.metrics(),
        }


@app.post("/simulate")
def simulate(request: SimulationRequest) -> dict:
    if request.reset_first:
        env.reset(task_id=request.task_id)

    step_results = []
    for idx, action in enumerate(request.actions, start=1):
        observation, reward, done, info = env.step(action)
        step_results.append(
            {
                "index": idx,
                "action": action.model_dump(),
                "reward": reward.model_dump(),
                "done": done,
                "grader_score": info.get("grader_score", 0.0),
                "feedback": observation.recent_feedback,
            }
        )
        if done:
            break

    response = SimulationResponse(
        task_id=request.task_id,
        step_results=step_results,
        final_metrics=env.metrics(),
    )
    return response.model_dump()
