"""
NovaIR Engine - The main runtime that orchestrates everything.

This is the heart of NovaIR: it reads state, evaluates constraints,
scores actions, and executes the best one.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import time
import threading

from ..parser.ast import System
from .state import StateManager
from .scorer import Scorer, ActionCandidate, ConstraintStatus


@dataclass
class EngineConfig:
    """Configuration for the NovaIR engine."""
    tick_interval_ms: int = 100
    action_threshold: float = 0.5
    continuous_mode: bool = True
    max_actions_per_tick: int = 1
    dry_run: bool = False  # If True, don't execute actions


@dataclass
class TickResult:
    """Result of a single tick evaluation."""
    timestamp: datetime
    constraints: List[ConstraintStatus]
    violations: List[ConstraintStatus]
    candidates_evaluated: int
    selected_action: Optional[ActionCandidate]
    action_executed: bool
    execution_time_ms: float

    def __repr__(self) -> str:
        action_str = str(self.selected_action) if self.selected_action else "None"
        return (f"Tick @ {self.timestamp.strftime('%H:%M:%S.%f')[:-3]}: "
                f"{len(self.violations)} violations, action={action_str}")


class Engine:
    """The NovaIR runtime engine."""

    def __init__(self, system: System, config: Optional[EngineConfig] = None):
        self.system = system
        self.config = config or EngineConfig()

        # Use tick config from system if available
        if system.tick:
            self.config.tick_interval_ms = system.tick.interval_ms
            self.config.action_threshold = system.tick.action_threshold
            self.config.continuous_mode = system.tick.mode.value == "continuous"

        # State manager
        self.state = StateManager()

        # Initialize state metadata from system
        for state_def in system.states:
            self.state.set_metadata(state_def.name, source=str(state_def.source))

        # Scorer
        self.scorer = Scorer(system, self.state)

        # Callbacks
        self._state_readers: Dict[str, Callable[[], float]] = {}
        self._action_handlers: Dict[str, Callable[[Dict[str, int]], None]] = {}
        self._tick_callbacks: List[Callable[[TickResult], None]] = []

        # Runtime state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick_count = 0
        self._history: List[TickResult] = []

    # ==========================================
    # Configuration
    # ==========================================

    def register_state_reader(self, name: str, reader: Callable[[], float]) -> None:
        """Register a function that reads a state value.

        Example:
            engine.register_state_reader("temperature", lambda: sensor.read_temp())
        """
        self._state_readers[name] = reader

    def register_action_handler(self, name: str,
                                handler: Callable[[Dict[str, int]], None]) -> None:
        """Register a function that executes an action.

        Example:
            engine.register_action_handler("increase_fan",
                lambda params: fan.set_speed(fan.speed + params.get("amount", 10)))
        """
        self._action_handlers[name] = handler

    def on_tick(self, callback: Callable[[TickResult], None]) -> None:
        """Register a callback to be called after each tick."""
        self._tick_callbacks.append(callback)

    def set_state(self, name: str, value: float) -> None:
        """Manually set a state value (for testing or simulation)."""
        self.state.update(name, value)

    def set_states(self, values: Dict[str, float]) -> None:
        """Manually set multiple state values."""
        self.state.update_all(values)

    # ==========================================
    # Execution
    # ==========================================

    def read_states(self) -> Dict[str, float]:
        """Read all states from registered readers."""
        values = {}
        for state_def in self.system.states:
            name = state_def.name
            if name in self._state_readers:
                try:
                    values[name] = self._state_readers[name]()
                except Exception as e:
                    print(f"Warning: Failed to read state '{name}': {e}")
        self.state.update_all(values)
        return values

    def execute_action(self, candidate: ActionCandidate) -> bool:
        """Execute an action candidate."""
        if self.config.dry_run:
            return False

        name = candidate.action.name
        if name in self._action_handlers:
            try:
                self._action_handlers[name](candidate.parameters)
                return True
            except Exception as e:
                print(f"Warning: Failed to execute action '{name}': {e}")
                return False
        return False

    def tick(self) -> TickResult:
        """Execute one tick of the engine."""
        start_time = time.time()
        self._tick_count += 1

        # 1. Read current state
        self.read_states()
        self.state.snapshot()

        # 2. Check constraints
        constraints = self.scorer.check_constraints()
        violations = [c for c in constraints if c.is_violated]

        # 3. Generate and score candidates
        candidates = self.scorer.generate_candidates()
        for candidate in candidates:
            self.scorer.score_candidate(candidate, violations)

        # 4. Select best action
        selected = self.scorer.select_best_action(self.config.action_threshold)

        # 5. Execute if threshold met
        executed = False
        if selected:
            executed = self.execute_action(selected)

        # Create result
        execution_time = (time.time() - start_time) * 1000
        result = TickResult(
            timestamp=datetime.now(),
            constraints=constraints,
            violations=violations,
            candidates_evaluated=len(candidates),
            selected_action=selected,
            action_executed=executed,
            execution_time_ms=execution_time
        )

        # Store history
        self._history.append(result)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

        # Call tick callbacks
        for callback in self._tick_callbacks:
            try:
                callback(result)
            except Exception as e:
                print(f"Warning: Tick callback failed: {e}")

        return result

    def run(self, duration_seconds: Optional[float] = None) -> None:
        """Run the engine in the current thread.

        Args:
            duration_seconds: How long to run (None = forever until stop())
        """
        self._running = True
        start_time = time.time()

        while self._running:
            self.tick()

            if duration_seconds and (time.time() - start_time) >= duration_seconds:
                break

            time.sleep(self.config.tick_interval_ms / 1000.0)

    def start(self) -> None:
        """Start the engine in a background thread."""
        if self._thread and self._thread.is_alive():
            return

        self._running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the engine."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    # ==========================================
    # Inspection
    # ==========================================

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        constraints = self.scorer.check_constraints()
        violations = [c for c in constraints if c.is_violated]

        return {
            "running": self._running,
            "tick_count": self._tick_count,
            "state": dict(self.state.current),
            "constraints": {c.constraint.name: not c.is_violated for c in constraints},
            "violations": [c.constraint.name for c in violations],
            "history_size": len(self._history),
        }

    def get_last_tick(self) -> Optional[TickResult]:
        """Get the most recent tick result."""
        return self._history[-1] if self._history else None

    def explain_decision(self, candidate: Optional[ActionCandidate] = None) -> str:
        """Explain why an action was or wasn't selected."""
        if candidate is None:
            candidate = self.scorer.select_best_action(self.config.action_threshold)

        if candidate is None:
            violations = self.scorer.get_critical_violations()
            if violations:
                return (f"No action resolves the {len(violations)} violations: "
                        f"{[v.constraint.name for v in violations]}")
            return f"No action scores above threshold ({self.config.action_threshold})"

        lines = [
            f"Selected: {candidate.action.name}",
            f"  Parameters: {candidate.parameters}",
            f"  Total Score: {candidate.score:.2f}",
            f"  - Constraint Resolution: {candidate.constraint_resolution_score:.2f}",
            f"  - Objective Optimization: {candidate.objective_score:.2f}",
            f"  - Cost Penalty: -{candidate.cost_penalty:.2f}",
            f"  Predicted Effects: {candidate.predicted_effects}",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f"Engine({self.system.name}, "
                f"tick={self.config.tick_interval_ms}ms, "
                f"running={self._running})")
