from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.openenv_hackathon.environment import RealWorldOpsEnv
from src.openenv_hackathon.models import Action, ActionType


ROOT = Path(__file__).resolve().parent


def check_openenv_yaml() -> bool:
    path = ROOT / "openenv.yaml"
    if not path.exists():
        print("[FAIL] openenv.yaml not found")
        return False
    print("[PASS] openenv.yaml present")
    return True


def solve_email_triage() -> float:
    env = RealWorldOpsEnv("email_triage")
    env.reset()
    actions = [
        Action(action_type=ActionType.TRIAGE_EMAIL, payload={"message_id": 1, "category": "urgent"}),
        Action(action_type=ActionType.TRIAGE_EMAIL, payload={"message_id": 2, "category": "normal"}),
        Action(action_type=ActionType.TRIAGE_EMAIL, payload={"message_id": 3, "category": "spam"}),
    ]
    info = {"grader_score": 0.0}
    for action in actions:
        _, _, _, info = env.step(action)
    return float(info["grader_score"])


def solve_ticket_routing() -> float:
    env = RealWorldOpsEnv("ticket_routing")
    env.reset()
    actions = [
        Action(action_type=ActionType.ROUTE_TICKET, payload={"ticket_id": 11, "queue": "technical", "priority": "p1"}),
        Action(action_type=ActionType.ROUTE_TICKET, payload={"ticket_id": 12, "queue": "billing", "priority": "p2"}),
        Action(action_type=ActionType.ROUTE_TICKET, payload={"ticket_id": 13, "queue": "general", "priority": "p3"}),
    ]
    info = {"grader_score": 0.0}
    for action in actions:
        _, _, _, info = env.step(action)
    return float(info["grader_score"])


def solve_content_moderation() -> float:
    env = RealWorldOpsEnv("content_moderation")
    env.reset()
    actions = [
        Action(action_type=ActionType.MODERATE_CONTENT, payload={"post_id": 21, "decision": "warn"}),
        Action(action_type=ActionType.MODERATE_CONTENT, payload={"post_id": 22, "decision": "remove"}),
        Action(action_type=ActionType.MODERATE_CONTENT, payload={"post_id": 23, "decision": "allow"}),
        Action(action_type=ActionType.MODERATE_CONTENT, payload={"post_id": 24, "decision": "allow"}),
    ]
    info = {"grader_score": 0.0}
    for action in actions:
        _, _, _, info = env.step(action)
    return float(info["grader_score"])


def check_env_tasks() -> bool:
    scores = {
        "email_triage": solve_email_triage(),
        "ticket_routing": solve_ticket_routing(),
        "content_moderation": solve_content_moderation(),
    }
    ok = all(score == 1.0 for score in scores.values())
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] deterministic task scores: {json.dumps(scores)}")
    return ok


def check_baseline_heuristic() -> bool:
    cmd = [sys.executable, "baseline_inference.py", "--policy", "heuristic", "--max-turns", "10"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print("[FAIL] baseline_inference heuristic mode failed")
        print(proc.stderr.strip())
        return False
    print("[PASS] baseline_inference heuristic mode")
    print(proc.stdout.strip())
    return True


def main() -> None:
    checks = [
        check_openenv_yaml(),
        check_env_tasks(),
        check_baseline_heuristic(),
    ]
    if all(checks):
        print("\nAll local preflight checks passed.")
        print("Next: run official openenv validate and docker build/run on a machine with required tools available.")
        raise SystemExit(0)

    print("\nPreflight checks failed.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
