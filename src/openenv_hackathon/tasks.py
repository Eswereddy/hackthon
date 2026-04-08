from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .models import Action, ActionType, Difficulty


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    title: str
    difficulty: Difficulty
    objective: str
    max_steps: int


class BaseTask(ABC):
    def __init__(self, spec: TaskSpec):
        self.spec = spec

    @abstractmethod
    def initial_context(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def apply_action(self, action: Action, context: Dict[str, Any]) -> Tuple[float, bool, bool, str]:
        """Returns: (delta_progress, invalid_action, destructive_action, reason)."""

    @abstractmethod
    def grade(self, context: Dict[str, Any]) -> float:
        ...


class EmailTriageTask(BaseTask):
    def __init__(self) -> None:
        super().__init__(
            TaskSpec(
                task_id="email_triage",
                title="Support Inbox Triage",
                difficulty=Difficulty.EASY,
                objective=(
                    "Categorize support inbox messages as urgent, normal, or spam so human agents can respond in priority order."
                ),
                max_steps=10,
            )
        )

    def initial_context(self) -> Dict[str, Any]:
        inbox = [
            {
                "id": 1,
                "subject": "Payment failed after card charge",
                "body": "My card was charged twice and my account is locked.",
            },
            {
                "id": 2,
                "subject": "Need enterprise pricing sheet",
                "body": "Please send product brochure and pricing when possible.",
            },
            {
                "id": 3,
                "subject": "Win crypto now",
                "body": "Click this link and share credentials to claim reward.",
            },
        ]
        expected = {1: "urgent", 2: "normal", 3: "spam"}
        return {"inbox": inbox, "labels": {}, "expected": expected}

    def apply_action(self, action: Action, context: Dict[str, Any]) -> Tuple[float, bool, bool, str]:
        if action.action_type not in {ActionType.TRIAGE_EMAIL, ActionType.NOOP, ActionType.DELETE_ALL}:
            return -0.05, True, False, "Wrong action type for this task."

        if action.action_type == ActionType.NOOP:
            return -0.02, False, False, "No progress made."

        if action.action_type == ActionType.DELETE_ALL:
            context["labels"] = {}
            return -0.3, False, True, "Destructive action removed all labels."

        message_id = action.payload.get("message_id")
        category = action.payload.get("category")
        if message_id not in context["expected"] or category not in {"urgent", "normal", "spam"}:
            return -0.05, True, False, "Invalid message_id or category."

        existing = context["labels"].get(message_id)
        context["labels"][message_id] = category
        expected = context["expected"][message_id]

        if category == expected:
            if existing == expected:
                return -0.01, False, False, "Duplicate triage for same message."
            return 0.2, False, False, "Correct triage decision."

        return -0.08, False, False, "Incorrect triage decision."

    def grade(self, context: Dict[str, Any]) -> float:
        expected = context["expected"]
        labels = context["labels"]
        correct = sum(1 for msg_id, expected_cat in expected.items() if labels.get(msg_id) == expected_cat)
        return correct / len(expected)


class TicketRoutingTask(BaseTask):
    def __init__(self) -> None:
        super().__init__(
            TaskSpec(
                task_id="ticket_routing",
                title="Queue And Priority Routing",
                difficulty=Difficulty.MEDIUM,
                objective=(
                    "Assign each support ticket to the right queue and priority based on issue type, SLA risk, and account tier."
                ),
                max_steps=12,
            )
        )

    def initial_context(self) -> Dict[str, Any]:
        tickets = [
            {
                "id": 11,
                "summary": "SSO login fails for 120 employees",
                "account_tier": "enterprise",
                "hours_open": 1,
            },
            {
                "id": 12,
                "summary": "Need VAT invoice copy",
                "account_tier": "pro",
                "hours_open": 8,
            },
            {
                "id": 13,
                "summary": "How to export my data?",
                "account_tier": "free",
                "hours_open": 5,
            },
        ]
        expected = {
            11: {"queue": "technical", "priority": "p1"},
            12: {"queue": "billing", "priority": "p2"},
            13: {"queue": "general", "priority": "p3"},
        }
        return {"tickets": tickets, "routes": {}, "expected": expected}

    def apply_action(self, action: Action, context: Dict[str, Any]) -> Tuple[float, bool, bool, str]:
        if action.action_type not in {ActionType.ROUTE_TICKET, ActionType.NOOP, ActionType.DELETE_ALL}:
            return -0.05, True, False, "Wrong action type for this task."

        if action.action_type == ActionType.NOOP:
            return -0.02, False, False, "No routing decision made."

        if action.action_type == ActionType.DELETE_ALL:
            context["routes"] = {}
            return -0.3, False, True, "Destructive action removed all routes."

        ticket_id = action.payload.get("ticket_id")
        queue = action.payload.get("queue")
        priority = action.payload.get("priority")
        if ticket_id not in context["expected"]:
            return -0.05, True, False, "Unknown ticket_id."
        if queue not in {"technical", "billing", "general"}:
            return -0.05, True, False, "Invalid queue."
        if priority not in {"p1", "p2", "p3"}:
            return -0.05, True, False, "Invalid priority."

        previous = context["routes"].get(ticket_id)
        context["routes"][ticket_id] = {"queue": queue, "priority": priority}
        expected_route = context["expected"][ticket_id]

        if context["routes"][ticket_id] == expected_route:
            if previous == expected_route:
                return -0.01, False, False, "Duplicate route submission."
            return 0.2, False, False, "Correct queue and priority."

        return -0.08, False, False, "Route or priority does not match expected policy."

    def grade(self, context: Dict[str, Any]) -> float:
        expected = context["expected"]
        routes = context["routes"]
        correct = 0
        for ticket_id, expected_route in expected.items():
            if routes.get(ticket_id) == expected_route:
                correct += 1
        return correct / len(expected)


class ContentModerationTask(BaseTask):
    def __init__(self) -> None:
        super().__init__(
            TaskSpec(
                task_id="content_moderation",
                title="Community Moderation Decisions",
                difficulty=Difficulty.HARD,
                objective=(
                    "Moderate community posts by choosing allow, warn, or remove based on abuse, phishing risk, and policy compliance."
                ),
                max_steps=16,
            )
        )

    def initial_context(self) -> Dict[str, Any]:
        posts = [
            {
                "id": 21,
                "text": "I hate this useless support team, all of you are idiots.",
            },
            {
                "id": 22,
                "text": "To fix billing issue, DM me your password and card number.",
            },
            {
                "id": 23,
                "text": "The export feature works after clearing cache, thanks everyone.",
            },
            {
                "id": 24,
                "text": "Your docs are unclear. Please improve the API examples.",
            },
        ]
        expected = {
            21: "warn",
            22: "remove",
            23: "allow",
            24: "allow",
        }
        return {"posts": posts, "decisions": {}, "expected": expected, "actions_taken": 0}

    def apply_action(self, action: Action, context: Dict[str, Any]) -> Tuple[float, bool, bool, str]:
        if action.action_type not in {ActionType.MODERATE_CONTENT, ActionType.NOOP, ActionType.DELETE_ALL}:
            return -0.05, True, False, "Wrong action type for this task."

        if action.action_type == ActionType.NOOP:
            return -0.02, False, False, "No moderation decision made."

        if action.action_type == ActionType.DELETE_ALL:
            context["decisions"] = {}
            return -0.35, False, True, "Destructive action removed moderation decisions."

        post_id = action.payload.get("post_id")
        decision = action.payload.get("decision")
        if post_id not in context["expected"]:
            return -0.05, True, False, "Unknown post_id."
        if decision not in {"allow", "warn", "remove"}:
            return -0.05, True, False, "Invalid decision."

        previous = context["decisions"].get(post_id)
        context["decisions"][post_id] = decision
        context["actions_taken"] += 1

        expected = context["expected"][post_id]
        if decision == expected:
            if previous == expected:
                return -0.01, False, False, "Duplicate moderation decision."
            return 0.14, False, False, "Correct moderation decision."

        if decision == "allow" and expected == "remove":
            return -0.15, False, False, "Severe policy miss: harmful content allowed."

        return -0.07, False, False, "Moderation decision does not match policy."

    def grade(self, context: Dict[str, Any]) -> float:
        expected = context["expected"]
        decisions = context["decisions"]
        correct = sum(1 for post_id, expected_decision in expected.items() if decisions.get(post_id) == expected_decision)
        accuracy = correct / len(expected)
        over_action_penalty = 0.02 * max(0, context["actions_taken"] - len(expected))
        return max(0.0, min(1.0, accuracy - over_action_penalty))


def build_tasks() -> Dict[str, BaseTask]:
    return {
        "email_triage": EmailTriageTask(),
        "ticket_routing": TicketRoutingTask(),
        "content_moderation": ContentModerationTask(),
    }
