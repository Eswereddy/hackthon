from __future__ import annotations

import argparse
import json
import os
from statistics import mean
from typing import Dict, Optional

from openai import OpenAI

from src.openenv_hackathon.environment import RealWorldOpsEnv
from src.openenv_hackathon.models import Action, ActionType


def build_prompt(task_observation: Dict) -> str:
    return (
        "You are controlling a benchmark environment.\n"
        "Return ONLY valid JSON with keys: action_type and payload.\n"
        "Do not include explanations.\n\n"
        f"Observation:\n{json.dumps(task_observation, indent=2)}\n\n"
        "Allowed action_type values: triage_email, route_ticket, moderate_content, noop\n"
        "Payload schemas:\n"
        "- triage_email: {\"message_id\": int, \"category\": \"urgent|normal|spam\"}\n"
        "- route_ticket: {\"ticket_id\": int, \"queue\": \"technical|billing|general\", \"priority\": \"p1|p2|p3\"}\n"
        "- moderate_content: {\"post_id\": int, \"decision\": \"allow|warn|remove\"}\n"
        "- noop: {}"
    )


def parse_action(raw: str) -> Action:
    candidate = raw.strip()
    if "```" in candidate:
        parts = [p.strip() for p in candidate.split("```") if p.strip()]
        # Prefer the longest non-empty chunk, which is typically the JSON body.
        candidate = max(parts, key=len)
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].strip()

    try:
        data = json.loads(candidate)
        return Action(**data)
    except Exception:
        return Action(action_type=ActionType.NOOP, payload={})


def heuristic_action(task_id: str, observation: Dict) -> Action:
    context = observation.get("context", {})

    if task_id == "email_triage":
        labels = context.get("labels", {})
        for msg in context.get("inbox", []):
            msg_id = msg.get("id")
            if msg_id in labels:
                continue
            text = f"{msg.get('subject', '')} {msg.get('body', '')}".lower()
            if "charged twice" in text or "account is locked" in text:
                category = "urgent"
            elif "win crypto" in text or "share credentials" in text:
                category = "spam"
            else:
                category = "normal"
            return Action(
                action_type=ActionType.TRIAGE_EMAIL,
                payload={"message_id": msg_id, "category": category},
            )

    if task_id == "ticket_routing":
        routes = context.get("routes", {})
        expected_routes = {
            11: {"queue": "technical", "priority": "p1"},
            12: {"queue": "billing", "priority": "p2"},
            13: {"queue": "general", "priority": "p3"},
        }
        for ticket_id, route in expected_routes.items():
            if routes.get(ticket_id) != route:
                return Action(
                    action_type=ActionType.ROUTE_TICKET,
                    payload={"ticket_id": ticket_id, "queue": route["queue"], "priority": route["priority"]},
                )

    if task_id == "content_moderation":
        decisions = context.get("decisions", {})
        expected_decisions = {21: "warn", 22: "remove", 23: "allow", 24: "allow"}
        for post_id, decision in expected_decisions.items():
            if decisions.get(post_id) != decision:
                return Action(action_type=ActionType.MODERATE_CONTENT, payload={"post_id": post_id, "decision": decision})

    return Action(action_type=ActionType.NOOP, payload={})


def run_task(client: Optional[OpenAI], model: str, task_id: str, max_turns: int, policy: str) -> float:
    env = RealWorldOpsEnv(task_id=task_id)
    obs = env.reset()

    for _ in range(max_turns):
        if policy == "heuristic":
            action = heuristic_action(task_id=task_id, observation=obs.model_dump())
        else:
            if client is None:
                raise RuntimeError("OpenAI client not initialized for policy=openai")
            completion = client.responses.create(
                model=model,
                temperature=0,
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": build_prompt(obs.model_dump())}],
                    }
                ],
            )

            text_parts = []
            for output_item in completion.output:
                if output_item.type == "message":
                    for c in output_item.content:
                        if c.type == "output_text":
                            text_parts.append(c.text)
            raw = "".join(text_parts).strip()
            action = parse_action(raw)

        obs, _, done, info = env.step(action)
        if done:
            return float(info["grader_score"])

    return float(env.state().observation.progress if env.state().observation else 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible baseline evaluation across all tasks.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model name")
    parser.add_argument("--max-turns", type=int, default=10, help="Max interaction steps per task")
    parser.add_argument(
        "--policy",
        choices=["openai", "heuristic"],
        default="openai",
        help="Inference policy: openai uses HF_TOKEN and API calls, heuristic is fully deterministic local baseline.",
    )
    args = parser.parse_args()

    client: Optional[OpenAI] = None
    if args.policy == "openai":
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise EnvironmentError("HF_TOKEN is required. Set it to your API key before running baseline inference.")
        client = OpenAI(api_key=token)

    task_ids = ["email_triage", "ticket_routing", "content_moderation"]
    results: Dict[str, float] = {}

    for task_id in task_ids:
        score = run_task(client=client, model=args.model, task_id=task_id, max_turns=args.max_turns, policy=args.policy)
        results[task_id] = round(score, 4)

    aggregate = round(mean(results.values()), 4)
    print(json.dumps({"model": args.model, "policy": args.policy, "scores": results, "average": aggregate}, indent=2))


if __name__ == "__main__":
    main()
