from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Dict, Optional

from .models import Action, EnvironmentState, Observation, Reward, StepInfo, StepReturn
from .tasks import BaseTask, build_tasks


class RealWorldOpsEnv:
    """OpenEnv-style environment with typed observation/action/reward models."""

    def __init__(self, task_id: str = "email_triage") -> None:
        self._tasks = build_tasks()
        if task_id not in self._tasks:
            raise ValueError(f"Unknown task_id: {task_id}")

        self._active_task_id = task_id
        self._active_task: BaseTask = self._tasks[task_id]
        self._task_context: Dict[str, Any] = {}
        self._state = EnvironmentState()
        self._last_action_signature: Optional[str] = None

    def _build_observation(self) -> Observation:
        grader_score = self._active_task.grade(self._task_context)
        remaining_steps = max(0, self._active_task.spec.max_steps - self._state.step_count)

        context_for_agent = deepcopy(self._task_context)
        if "expected" in context_for_agent:
            del context_for_agent["expected"]

        if "target" in context_for_agent:
            context_for_agent["target_count"] = len(context_for_agent["target"])
            del context_for_agent["target"]

        return Observation(
            task_id=self._active_task.spec.task_id,
            difficulty=self._active_task.spec.difficulty,
            objective=self._active_task.spec.objective,
            context=context_for_agent,
            progress=grader_score,
            remaining_steps=remaining_steps,
            recent_feedback=[] if not self._state.observation else self._state.observation.recent_feedback,
        )

    def reset(self, task_id: Optional[str] = None) -> Observation:
        if task_id is not None:
            if task_id not in self._tasks:
                raise ValueError(f"Unknown task_id: {task_id}")
            self._active_task_id = task_id
            self._active_task = self._tasks[task_id]

        self._task_context = self._active_task.initial_context()
        self._state = EnvironmentState(
            task_id=self._active_task.spec.task_id,
            difficulty=self._active_task.spec.difficulty,
            cumulative_reward=0.0,
            step_count=0,
            done=False,
            history=[],
        )
        self._last_action_signature = None
        observation = self._build_observation()
        self._state.observation = observation
        return observation

    def state(self) -> EnvironmentState:
        return self._state.model_copy(deep=True)

    def step(self, action: Action) -> StepReturn:
        if self._state.done:
            obs = self._build_observation()
            reward = Reward(value=0.0, reason="Episode already complete. Call reset() to start again.")
            info = StepInfo(grader_score=obs.progress, max_steps_reached=True).model_dump()
            return obs, reward, True, info

        prev_score = self._active_task.grade(self._task_context)
        self._state.step_count += 1

        delta_progress, invalid_action, destructive_action, reason = self._active_task.apply_action(action, self._task_context)

        action_signature = json.dumps(action.model_dump(), sort_keys=True)
        loop_detected = self._last_action_signature == action_signature
        self._last_action_signature = action_signature

        if loop_detected:
            delta_progress -= 0.03
            reason += " Repeated identical action detected."

        new_score = self._active_task.grade(self._task_context)
        shaped_reward = delta_progress + (new_score - prev_score)

        if invalid_action:
            shaped_reward -= 0.02

        if destructive_action:
            shaped_reward -= 0.08

        max_steps_reached = self._state.step_count >= self._active_task.spec.max_steps
        done = max_steps_reached or new_score >= 1.0
        self._state.done = done

        observation = self._build_observation()
        observation.recent_feedback = [reason]
        reward = Reward(value=round(shaped_reward, 4), reason=reason)

        self._state.cumulative_reward += reward.value
        self._state.observation = observation
        self._state.history.append(action)

        info = StepInfo(
            grader_score=new_score,
            max_steps_reached=max_steps_reached,
            invalid_action=invalid_action,
            loop_detected=loop_detected,
            destructive_action=destructive_action,
        ).model_dump()

        return observation, reward, done, info

    @property
    def tasks(self) -> Dict[str, str]:
        return {task_id: task.spec.title for task_id, task in self._tasks.items()}
