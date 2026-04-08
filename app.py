from __future__ import annotations

from fastapi import FastAPI

from src.openenv_hackathon.environment import RealWorldOpsEnv
from src.openenv_hackathon.models import Action

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


@app.post("/step")
def step(action: Action) -> dict:
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }
