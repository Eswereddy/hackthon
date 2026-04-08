from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ActionType(str, Enum):
    TRIAGE_EMAIL = "triage_email"
    ROUTE_TICKET = "route_ticket"
    MODERATE_CONTENT = "moderate_content"
    NOOP = "noop"
    DELETE_ALL = "delete_all"


class Action(BaseModel):
    action_type: ActionType
    payload: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> "Action":
        payload = self.payload

        if self.action_type in {ActionType.NOOP, ActionType.DELETE_ALL}:
            return self

        if self.action_type == ActionType.TRIAGE_EMAIL:
            if not isinstance(payload.get("message_id"), int):
                raise ValueError("triage_email requires payload.message_id as int")
            if payload.get("category") not in {"urgent", "normal", "spam"}:
                raise ValueError("triage_email requires payload.category in urgent|normal|spam")
            return self

        if self.action_type == ActionType.ROUTE_TICKET:
            if not isinstance(payload.get("ticket_id"), int):
                raise ValueError("route_ticket requires payload.ticket_id as int")
            if payload.get("queue") not in {"technical", "billing", "general"}:
                raise ValueError("route_ticket requires payload.queue in technical|billing|general")
            if payload.get("priority") not in {"p1", "p2", "p3"}:
                raise ValueError("route_ticket requires payload.priority in p1|p2|p3")
            return self

        if self.action_type == ActionType.MODERATE_CONTENT:
            if not isinstance(payload.get("post_id"), int):
                raise ValueError("moderate_content requires payload.post_id as int")
            if payload.get("decision") not in {"allow", "warn", "remove"}:
                raise ValueError("moderate_content requires payload.decision in allow|warn|remove")
            return self

        return self


class Observation(BaseModel):
    task_id: str
    difficulty: Difficulty
    objective: str
    context: Dict[str, Any]
    progress: float = Field(ge=0.0, le=1.0)
    remaining_steps: int = Field(ge=0)
    recent_feedback: List[str] = Field(default_factory=list)


class Reward(BaseModel):
    value: float
    reason: str


class EnvironmentState(BaseModel):
    task_id: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    observation: Optional[Observation] = None
    cumulative_reward: float = 0.0
    step_count: int = 0
    done: bool = False
    unsafe_action_count: int = 0
    history: List[Action] = Field(default_factory=list)


class StepInfo(BaseModel):
    grader_score: float = Field(ge=0.0, le=1.0)
    score_delta: float = 0.0
    episode_score: float = Field(ge=0.0, le=1.0)
    max_steps_reached: bool = False
    invalid_action: bool = False
    loop_detected: bool = False
    destructive_action: bool = False
    safety_violation_count: int = 0


class SimulationRequest(BaseModel):
    task_id: str
    actions: List[Action] = Field(default_factory=list)
    reset_first: bool = True


class SimulationResponse(BaseModel):
    task_id: str
    step_results: List[Dict[str, Any]] = Field(default_factory=list)
    final_metrics: Dict[str, Any] = Field(default_factory=dict)


StepReturn = tuple[Observation, Reward, bool, Dict[str, Any]]
