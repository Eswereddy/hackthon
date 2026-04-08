from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


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
    history: List[Action] = Field(default_factory=list)


class StepInfo(BaseModel):
    grader_score: float = Field(ge=0.0, le=1.0)
    max_steps_reached: bool = False
    invalid_action: bool = False
    loop_detected: bool = False
    destructive_action: bool = False


StepReturn = tuple[Observation, Reward, bool, Dict[str, Any]]
