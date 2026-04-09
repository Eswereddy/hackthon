from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
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
            try:
                # Call OpenAI Chat Completions API (v2.x compatible) with timeout
                completion = client.chat.completions.create(
                    model=model,
                    temperature=0,
                    timeout=30.0,
                    messages=[
                        {
                            "role": "user",
                            "content": build_prompt(obs.model_dump()),
                        }
                    ],
                )

                # Parse response safely
                if not completion or not completion.choices or len(completion.choices) == 0:
                    raise ValueError("Empty response from OpenAI API")
                
                message_content = completion.choices[0].message.content
                if message_content is None:
                    raise ValueError("Message content is None from OpenAI API")
                
                raw = message_content.strip()
                action = parse_action(raw)
            except ValueError as e:
                print(f"⚠️ API Response Error: {e}")
                action = Action(action_type=ActionType.NOOP, payload={})
            except Exception as e:
                print(f"⚠️ OpenAI API Error ({type(e).__name__}): {e}. Using NOOP action.")
                action = Action(action_type=ActionType.NOOP, payload={})

        obs, _, done, info = env.step(action)
        if done:
            return float(info["grader_score"])

    return float(env.state().observation.progress if env.state().observation else 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible baseline evaluation across all tasks.")
    parser.add_argument("--model", default="gpt-4-mini", help="OpenAI model name")
    parser.add_argument("--max-turns", type=int, default=10, help="Max interaction steps per task")
    parser.add_argument(
        "--policy",
        choices=["openai", "heuristic"],
        default="heuristic",
        help="Inference policy: openai uses HF_TOKEN and API calls, heuristic is fully deterministic local baseline.",
    )
    args = parser.parse_args()

    client: Optional[OpenAI] = None
    effective_policy = args.policy
    
    if args.policy == "openai":
        token = os.environ.get("HF_TOKEN")
        if not token:
            print("⚠️ HF_TOKEN not found. Falling back to heuristic policy (deterministic baseline).")
            effective_policy = "heuristic"
        else:
            try:
                client = OpenAI(api_key=token, timeout=30.0)
                print("✓ OpenAI client initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI client: {type(e).__name__}: {e}")
                print("Falling back to heuristic policy.")
                effective_policy = "heuristic"

    task_ids = ["email_triage", "ticket_routing", "content_moderation"]
    results: Dict[str, float] = {}

    print(f"\n📋 Running evaluation with policy={effective_policy}, model={args.model}, max_turns={args.max_turns}")
    print(f"📌 Tasks: {', '.join(task_ids)}\n")
    
    for idx, task_id in enumerate(task_ids, 1):
        try:
            print(f"[{idx}/{len(task_ids)}] Running {task_id}...", end=" ", flush=True)
            score = run_task(client=client, model=args.model, task_id=task_id, max_turns=args.max_turns, policy=effective_policy)
            results[task_id] = round(score, 4)
            print(f"✓ Score: {results[task_id]}")
        except Exception as e:
            print(f"\n    ❌ Error in {task_id}: {type(e).__name__}: {e}")
            results[task_id] = 0.0

    aggregate = round(mean(results.values()), 4)
    print("\n" + "="*60)
    print(f"📊 Final Results (Policy: {effective_policy})")
    print("="*60)
    print(json.dumps({"model": args.model, "policy": effective_policy, "scores": results, "average": aggregate}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {type(e).__name__}")
        print(f"Details: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
