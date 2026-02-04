"""
NovaIR Abstract Syntax Tree (AST) definitions.

This module defines the data structures that represent a parsed NovaIR program.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum


class Severity(Enum):
    """Constraint severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"


class CostLevel(Enum):
    """Action cost levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ObjectiveType(Enum):
    """Objective optimization types."""
    TARGET = "target"
    MIN = "min"
    MAX = "max"


class TickMode(Enum):
    """Tick execution modes."""
    CONTINUOUS = "continuous"
    REACTIVE = "reactive"


@dataclass
class SourcePath:
    """A source path like 'sensors.cpu.temp'."""
    parts: List[str]

    def __str__(self) -> str:
        return ".".join(self.parts)


@dataclass
class ValueWithUnit:
    """A numeric value with optional unit like '85°C' or '100%'."""
    value: float
    unit: Optional[str] = None

    def __str__(self) -> str:
        if self.unit:
            return f"{self.value}{self.unit}"
        return str(self.value)


@dataclass
class Effect:
    """An action effect like 'temperature: -5°C to -15°C'."""
    metric: str
    min_effect: ValueWithUnit
    max_effect: Optional[ValueWithUnit] = None  # None if single value

    def __str__(self) -> str:
        if self.max_effect:
            return f"{self.metric}: {self.min_effect} to {self.max_effect}"
        return f"{self.metric}: {self.min_effect}"


@dataclass
class Parameter:
    """An action parameter like 'level: 1..5'."""
    name: str
    min_value: int
    max_value: int

    def __str__(self) -> str:
        return f"{self.name}: {self.min_value}..{self.max_value}"


@dataclass
class State:
    """A state binding like 'temperature <- sensors.cpu.temp'."""
    name: str
    source: SourcePath

    def __str__(self) -> str:
        return f"{self.name} <- {self.source}"


@dataclass
class Constraint:
    """A constraint declaration."""
    name: str
    metric: str
    operator: str  # <=, >=, ==, !=, <, >
    value: ValueWithUnit
    severity: Severity

    def __str__(self) -> str:
        return f"{self.name}: {self.metric} {self.operator} {self.value} @{self.severity.value}"


@dataclass
class Objective:
    """An objective declaration."""
    name: str
    metric: str
    type: ObjectiveType
    target_value: Optional[ValueWithUnit] = None  # Only for TARGET type
    priority: int = 5

    def __str__(self) -> str:
        if self.type == ObjectiveType.TARGET:
            return f"{self.name}: {self.metric} -> target({self.target_value}) @priority({self.priority})"
        return f"{self.name}: {self.metric} -> {self.type.value} @priority({self.priority})"


@dataclass
class Action:
    """An action declaration."""
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
    cost: CostLevel = CostLevel.LOW

    def __str__(self) -> str:
        lines = [f"{self.name}:"]
        if self.parameters:
            params_str = ", ".join(str(p) for p in self.parameters)
            lines.append(f"  parameters: [{params_str}]")
        lines.append("  effects:")
        for effect in self.effects:
            lines.append(f"    {effect}")
        lines.append(f"  cost: {self.cost.value}")
        return "\n".join(lines)


@dataclass
class Tick:
    """Tick configuration."""
    interval_ms: int = 100
    action_threshold: float = 0.5
    mode: TickMode = TickMode.CONTINUOUS

    def __str__(self) -> str:
        return f"tick:\n  interval: {self.interval_ms} ms\n  action_threshold: {self.action_threshold}\n  mode: {self.mode.value}"


@dataclass
class System:
    """The root AST node representing a complete NovaIR program."""
    name: str
    version: Optional[str] = None
    states: List[State] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    objectives: List[Objective] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    tick: Optional[Tick] = None

    def __str__(self) -> str:
        lines = [f"system {self.name}"]
        if self.version:
            lines[0] += f' @version("{self.version}")'
        lines.append("")

        if self.states:
            lines.append("state:")
            for state in self.states:
                lines.append(f"  {state}")
            lines.append("")

        if self.constraints:
            lines.append("constraints:")
            for constraint in self.constraints:
                lines.append(f"  {constraint}")
            lines.append("")

        if self.objectives:
            lines.append("objectives:")
            for objective in self.objectives:
                lines.append(f"  {objective}")
            lines.append("")

        if self.actions:
            lines.append("actions:")
            for action in self.actions:
                action_lines = str(action).split("\n")
                for line in action_lines:
                    lines.append(f"  {line}")
            lines.append("")

        if self.tick:
            lines.append(str(self.tick))

        return "\n".join(lines)

    def validate(self) -> List[str]:
        """Validate the system and return a list of errors (empty if valid)."""
        errors = []

        if not self.name:
            errors.append("System name is required")

        if not self.states:
            errors.append("At least one state is required")

        if not self.constraints and not self.objectives:
            errors.append("At least one constraint or objective is required")

        # Check that constraint/objective metrics reference existing states
        state_names = {s.name for s in self.states}

        for constraint in self.constraints:
            if constraint.metric not in state_names:
                errors.append(f"Constraint '{constraint.name}' references unknown state '{constraint.metric}'")

        for objective in self.objectives:
            if objective.metric not in state_names:
                errors.append(f"Objective '{objective.name}' references unknown state '{objective.metric}'")

        # Check priority ranges
        for objective in self.objectives:
            if not 1 <= objective.priority <= 10:
                errors.append(f"Objective '{objective.name}' has invalid priority {objective.priority} (must be 1-10)")

        return errors
