"""
NovaIR State Manager - Manages system state and history.

This module tracks current state values and maintains history for analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque


@dataclass
class StateSnapshot:
    """A snapshot of all state values at a point in time."""
    timestamp: datetime
    values: Dict[str, float]

    def get(self, name: str, default: float = 0.0) -> float:
        """Get a state value by name."""
        return self.values.get(name, default)


@dataclass
class StateManager:
    """Manages current state and history."""

    # Current state values
    current: Dict[str, float] = field(default_factory=dict)

    # History of state snapshots (for jitter/trend analysis)
    history: deque = field(default_factory=lambda: deque(maxlen=100))

    # State metadata (units, bounds, etc.)
    metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def update(self, name: str, value: float) -> None:
        """Update a single state value."""
        self.current[name] = value

    def update_all(self, values: Dict[str, float]) -> None:
        """Update multiple state values at once."""
        self.current.update(values)

    def get(self, name: str, default: float = 0.0) -> float:
        """Get current value of a state."""
        return self.current.get(name, default)

    def snapshot(self) -> StateSnapshot:
        """Take a snapshot of current state and add to history."""
        snap = StateSnapshot(
            timestamp=datetime.now(),
            values=dict(self.current)
        )
        self.history.append(snap)
        return snap

    def get_history(self, name: str, count: int = 10) -> List[float]:
        """Get recent history of a state value."""
        values = []
        for snap in list(self.history)[-count:]:
            if name in snap.values:
                values.append(snap.values[name])
        return values

    def calculate_jitter(self, name: str, window: int = 10) -> float:
        """Calculate jitter (variance) of a state over recent history."""
        values = self.get_history(name, window)
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5  # Standard deviation

    def calculate_trend(self, name: str, window: int = 10) -> float:
        """Calculate trend (slope) of a state over recent history.

        Returns:
            Positive = increasing, Negative = decreasing, ~0 = stable
        """
        values = self.get_history(name, window)
        if len(values) < 2:
            return 0.0

        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def set_metadata(self, name: str, **kwargs) -> None:
        """Set metadata for a state (unit, min, max, etc.)."""
        if name not in self.metadata:
            self.metadata[name] = {}
        self.metadata[name].update(kwargs)

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a state."""
        return self.metadata.get(name, {})

    def normalize(self, name: str, value: Optional[float] = None) -> float:
        """Normalize a value to 0-1 range based on metadata bounds.

        If value is None, uses current state value.
        """
        if value is None:
            value = self.get(name)

        meta = self.get_metadata(name)
        min_val = meta.get("min", 0)
        max_val = meta.get("max", 100)

        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))

    def __repr__(self) -> str:
        states = ", ".join(f"{k}={v:.1f}" for k, v in self.current.items())
        return f"StateManager({states})"
