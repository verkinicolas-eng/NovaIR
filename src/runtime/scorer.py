"""
NovaIR Scorer - Evaluates and scores action candidates.

This module implements the core scoring algorithm that determines
which action to take based on constraints and objectives.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ..parser.ast import (
    System, Constraint, Objective, Action, Effect,
    Severity, ObjectiveType, CostLevel
)
from .state import StateManager


class ViolationType(Enum):
    """Type of constraint violation."""
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ConstraintStatus:
    """Status of a constraint evaluation."""
    constraint: Constraint
    current_value: float
    threshold: float
    violation: ViolationType
    margin: float  # How close to violation (negative = violated)

    @property
    def is_violated(self) -> bool:
        return self.violation != ViolationType.NONE

    def __repr__(self) -> str:
        status = "OK" if not self.is_violated else self.violation.value.upper()
        return f"{self.constraint.name}: {self.current_value:.1f} {self.constraint.operator} {self.threshold:.1f} [{status}]"


@dataclass
class ActionCandidate:
    """A candidate action with its parameters and score."""
    action: Action
    parameters: Dict[str, int] = field(default_factory=dict)
    score: float = 0.0
    constraint_resolution_score: float = 0.0
    objective_score: float = 0.0
    cost_penalty: float = 0.0
    predicted_effects: Dict[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        params = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.action.name}({params}) score={self.score:.2f}"


class Scorer:
    """Evaluates and scores action candidates."""

    # Cost penalties
    COST_PENALTIES = {
        CostLevel.LOW: 0.0,
        CostLevel.MEDIUM: 0.2,
        CostLevel.HIGH: 0.5,
    }

    def __init__(self, system: System, state_manager: StateManager):
        self.system = system
        self.state = state_manager

    def check_constraints(self) -> List[ConstraintStatus]:
        """Check all constraints against current state."""
        results = []

        for constraint in self.system.constraints:
            current = self.state.get(constraint.metric)
            threshold = constraint.value.value

            # Evaluate constraint
            margin = self._evaluate_constraint(current, constraint.operator, threshold)

            if margin < 0:
                violation = (ViolationType.CRITICAL
                             if constraint.severity == Severity.CRITICAL
                             else ViolationType.WARNING)
            else:
                violation = ViolationType.NONE

            results.append(ConstraintStatus(
                constraint=constraint,
                current_value=current,
                threshold=threshold,
                violation=violation,
                margin=margin
            ))

        return results

    def _evaluate_constraint(self, current: float, operator: str, threshold: float) -> float:
        """Evaluate a constraint and return margin (negative = violated)."""
        if operator == "<=":
            return threshold - current
        elif operator == ">=":
            return current - threshold
        elif operator == "<":
            return threshold - current - 0.001
        elif operator == ">":
            return current - threshold - 0.001
        elif operator == "==":
            return -abs(current - threshold)
        elif operator == "!=":
            return abs(current - threshold) - 0.001
        return 0.0

    def get_critical_violations(self) -> List[ConstraintStatus]:
        """Get list of critical constraint violations."""
        return [c for c in self.check_constraints()
                if c.violation == ViolationType.CRITICAL]

    def get_all_violations(self) -> List[ConstraintStatus]:
        """Get list of all constraint violations (critical and warning)."""
        return [c for c in self.check_constraints()
                if c.violation != ViolationType.NONE]

    def generate_candidates(self) -> List[ActionCandidate]:
        """Generate all possible action candidates with parameter variations."""
        candidates = []

        for action in self.system.actions:
            if action.parameters:
                # Generate candidates for each parameter combination
                param_values = self._generate_parameter_combinations(action)
                for params in param_values:
                    candidates.append(ActionCandidate(
                        action=action,
                        parameters=params
                    ))
            else:
                # No parameters
                candidates.append(ActionCandidate(action=action))

        return candidates

    def _generate_parameter_combinations(self, action: Action) -> List[Dict[str, int]]:
        """Generate parameter combinations (simplified: just min, mid, max)."""
        combinations = []

        if len(action.parameters) == 1:
            param = action.parameters[0]
            # Generate low, medium, high values
            values = [
                param.min_value,
                (param.min_value + param.max_value) // 2,
                param.max_value
            ]
            for v in values:
                combinations.append({param.name: v})
        else:
            # Multiple parameters: just use mid values for simplicity
            combo = {}
            for param in action.parameters:
                combo[param.name] = (param.min_value + param.max_value) // 2
            combinations.append(combo)

        return combinations

    def predict_effects(self, candidate: ActionCandidate) -> Dict[str, float]:
        """Predict the effects of an action on state values."""
        effects = {}

        for effect in candidate.action.effects:
            # Calculate effect magnitude based on parameters
            if effect.max_effect:
                # Range effect: interpolate based on parameter
                min_eff = effect.min_effect.value
                max_eff = effect.max_effect.value

                # Use first parameter to interpolate (simplified)
                if candidate.parameters:
                    param_name = list(candidate.parameters.keys())[0]
                    param_value = candidate.parameters[param_name]
                    param_def = next((p for p in candidate.action.parameters
                                      if p.name == param_name), None)
                    if param_def:
                        ratio = ((param_value - param_def.min_value) /
                                 (param_def.max_value - param_def.min_value))
                        effect_value = min_eff + (max_eff - min_eff) * ratio
                    else:
                        effect_value = (min_eff + max_eff) / 2
                else:
                    effect_value = (min_eff + max_eff) / 2
            else:
                effect_value = effect.min_effect.value

            effects[effect.metric] = effect_value

        candidate.predicted_effects = effects
        return effects

    def score_candidate(self, candidate: ActionCandidate,
                        violations: List[ConstraintStatus]) -> float:
        """Score a candidate action."""
        # Predict effects
        self.predict_effects(candidate)

        # 1. Constraint resolution score (highest priority)
        constraint_score = self._score_constraint_resolution(candidate, violations)
        candidate.constraint_resolution_score = constraint_score

        # 2. Objective optimization score
        objective_score = self._score_objectives(candidate)
        candidate.objective_score = objective_score

        # 3. Cost penalty
        cost_penalty = self.COST_PENALTIES.get(candidate.action.cost, 0.0)
        candidate.cost_penalty = cost_penalty

        # Combine scores
        # Constraint resolution has absolute priority when violations exist
        if violations:
            # Weight heavily toward constraint resolution
            total = constraint_score * 10 + objective_score - cost_penalty
        else:
            # Normal optimization mode
            total = objective_score - cost_penalty

        candidate.score = total
        return total

    def _score_constraint_resolution(self, candidate: ActionCandidate,
                                     violations: List[ConstraintStatus]) -> float:
        """Score how well this action resolves constraint violations."""
        if not violations:
            return 0.0

        resolution_score = 0.0

        for violation in violations:
            metric = violation.constraint.metric
            if metric in candidate.predicted_effects:
                effect = candidate.predicted_effects[metric]
                current = self.state.get(metric)
                threshold = violation.threshold
                operator = violation.constraint.operator

                # Calculate how much this helps
                if operator in ["<=", "<"]:
                    # We need to decrease the value
                    if effect < 0:  # Negative effect = decrease
                        improvement = min(abs(effect), current - threshold)
                        resolution_score += improvement * 2  # Bonus for resolving
                elif operator in [">=", ">"]:
                    # We need to increase the value
                    if effect > 0:
                        improvement = min(effect, threshold - current)
                        resolution_score += improvement * 2

        return resolution_score

    def _score_objectives(self, candidate: ActionCandidate) -> float:
        """Score how well this action optimizes objectives."""
        total_score = 0.0
        total_priority = sum(o.priority for o in self.system.objectives)

        if total_priority == 0:
            return 0.0

        for objective in self.system.objectives:
            metric = objective.metric
            priority_weight = objective.priority / 10.0  # Normalize to 0-1

            if metric in candidate.predicted_effects:
                effect = candidate.predicted_effects[metric]
                current = self.state.get(metric)

                if objective.type == ObjectiveType.MIN:
                    # Lower is better
                    if effect < 0:
                        total_score += abs(effect) * priority_weight
                    else:
                        total_score -= effect * priority_weight * 0.5

                elif objective.type == ObjectiveType.MAX:
                    # Higher is better
                    if effect > 0:
                        total_score += effect * priority_weight
                    else:
                        total_score -= abs(effect) * priority_weight * 0.5

                elif objective.type == ObjectiveType.TARGET:
                    target = objective.target_value.value
                    new_value = current + effect
                    old_distance = abs(current - target)
                    new_distance = abs(new_value - target)

                    if new_distance < old_distance:
                        # Getting closer to target
                        improvement = old_distance - new_distance
                        total_score += improvement * priority_weight
                    else:
                        # Getting further from target
                        degradation = new_distance - old_distance
                        total_score -= degradation * priority_weight * 0.5

        return total_score

    def select_best_action(self, threshold: float = 0.0) -> Optional[ActionCandidate]:
        """Select the best action based on current state.

        Args:
            threshold: Minimum score required to take action

        Returns:
            Best action candidate, or None if no action should be taken
        """
        # Use ALL violations (critical + warning) for scoring
        violations = self.get_all_violations()
        candidates = self.generate_candidates()

        # Score all candidates
        for candidate in candidates:
            self.score_candidate(candidate, violations)

        # Filter by violations if any exist
        if violations:
            # Only consider actions that help resolve violations
            resolving = [c for c in candidates if c.constraint_resolution_score > 0]
            if resolving:
                candidates = resolving

        # Sort by score
        candidates.sort(key=lambda c: c.score, reverse=True)

        if candidates and candidates[0].score > threshold:
            return candidates[0]

        return None
