from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from src.openenv_hackathon.environment import RealWorldOpsEnv
from src.openenv_hackathon.models import Action, SimulationRequest, SimulationResponse

app = FastAPI(title="Real-World OpenEnv Benchmark")
env = RealWorldOpsEnv(task_id="email_triage")
env.reset()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
        return """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>OpenEnv Support Ops Benchmark</title>
    <style>
        :root {
            --bg: #f4f7fb;
            --panel: #ffffff;
            --ink: #1f2a37;
            --muted: #5b6675;
            --accent: #0f766e;
            --border: #d8e1ec;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            color: var(--ink);
            background: radial-gradient(circle at 15% 10%, #e2f4f1, transparent 35%),
                                    radial-gradient(circle at 85% 20%, #dde8ff, transparent 40%),
                                    var(--bg);
            min-height: 100vh;
        }
        .wrap {
            max-width: 1080px;
            margin: 0 auto;
            padding: 24px;
        }
        .hero {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 8px 30px rgba(15, 23, 42, 0.06);
            margin-bottom: 16px;
        }
        .hero h1 { margin: 0 0 6px; font-size: 1.6rem; }
        .hero p { margin: 0; color: var(--muted); }
        .grid {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }
        .card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .card h2 {
            margin: 0 0 10px;
            font-size: 1.02rem;
            color: var(--accent);
        }
        .pill {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: #e8f7f5;
            border: 1px solid #c7ece8;
            font-size: 0.82rem;
            margin-right: 8px;
            margin-bottom: 6px;
        }
        pre {
            margin: 0;
            padding: 10px;
            border-radius: 10px;
            overflow: auto;
            border: 1px solid var(--border);
            background: #f8fbff;
            font-size: 0.8rem;
            line-height: 1.35;
        }
        .status {
            font-weight: 600;
            color: var(--accent);
        }
        .footer {
            margin-top: 16px;
            color: var(--muted);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class=\"wrap\">
        <section class=\"hero\">
            <h1>Customer Support Operations Benchmark</h1>
            <p>Real-world OpenEnv environment for email triage, ticket routing, and content moderation.</p>
            <p class=\"status\" id=\"health\">Checking service health...</p>
        </section>
        <section class=\"grid\">
            <article class=\"card\">
                <h2>Available Tasks</h2>
                <div id=\"tasks\"></div>
            </article>
            <article class=\"card\">
                <h2>Current Metrics</h2>
                <pre id=\"metrics\">Loading...</pre>
            </article>
            <article class=\"card\">
                <h2>Current State Snapshot</h2>
                <pre id=\"state\">Loading...</pre>
            </article>
        </section>
        <p class=\"footer\">Tip: API endpoints are still available at /tasks, /state, /step, /simulate.</p>
    </div>
    <script>
        async function getJson(url) {
            const res = await fetch(url);
            if (!res.ok) throw new Error(url + ' failed with ' + res.status);
            return await res.json();
        }

        async function load() {
            try {
                const [health, tasks, metrics, state] = await Promise.all([
                    getJson('/health'),
                    getJson('/tasks'),
                    getJson('/metrics'),
                    getJson('/state')
                ]);

                document.getElementById('health').textContent =
                    health.status === 'ok' ? 'Service healthy and running.' : 'Service status unknown.';

                const tasksEl = document.getElementById('tasks');
                tasksEl.innerHTML = '';
                Object.entries(tasks.tasks || {}).forEach(([k, v]) => {
                    const span = document.createElement('span');
                    span.className = 'pill';
                    span.textContent = k + ': ' + v;
                    tasksEl.appendChild(span);
                });

                document.getElementById('metrics').textContent = JSON.stringify(metrics, null, 2);
                document.getElementById('state').textContent = JSON.stringify(state, null, 2);
            } catch (err) {
                document.getElementById('health').textContent = 'Failed to load dashboard data.';
            }
        }

        load();
    </script>
</body>
</html>
"""


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
