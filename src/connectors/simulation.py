"""
NovaIR Simulated System - For testing and demonstration.

This module provides a simulated system that responds to actions
in a realistic way, perfect for testing NovaIR without real hardware.
"""

import random
import math
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SimulatedMetric:
    """A simulated metric with realistic behavior."""
    name: str
    value: float
    min_value: float = 0.0
    max_value: float = 100.0
    noise: float = 0.5  # Random noise percentage
    drift: float = 0.0  # Natural drift per tick
    inertia: float = 0.8  # How slowly it responds to changes (0-1)

    _target: float = field(default=None, init=False)

    def __post_init__(self):
        self._target = self.value

    def set_target(self, target: float) -> None:
        """Set target value (actual value will approach this over time)."""
        self._target = max(self.min_value, min(self.max_value, target))

    def apply_effect(self, delta: float) -> None:
        """Apply an effect (change target by delta)."""
        self.set_target(self._target + delta)

    def tick(self) -> float:
        """Update value for one tick."""
        # Apply inertia (gradual approach to target)
        diff = self._target - self.value
        self.value += diff * (1 - self.inertia)

        # Apply drift
        self.value += self.drift

        # Apply noise
        noise_amount = self.value * (self.noise / 100) * random.uniform(-1, 1)
        self.value += noise_amount

        # Clamp to bounds
        self.value = max(self.min_value, min(self.max_value, self.value))

        return self.value


class SimulatedSystem:
    """A fully simulated system for testing NovaIR.

    This simulates a thermal system (like a CPU cooler) with realistic
    physics: temperature rises under load, fan cools it down, etc.
    """

    def __init__(self, scenario: str = "thermostat"):
        self.scenario = scenario
        self.metrics: Dict[str, SimulatedMetric] = {}
        self.tick_count = 0
        self._load_scenario(scenario)

    def _load_scenario(self, scenario: str) -> None:
        """Load a predefined scenario."""
        if scenario == "thermostat":
            self._setup_thermostat()
        elif scenario == "load_balancer":
            self._setup_load_balancer()
        elif scenario == "frame_optimizer":
            self._setup_frame_optimizer()
        else:
            self._setup_thermostat()  # Default

    def _setup_thermostat(self) -> None:
        """Setup thermostat scenario."""
        self.metrics = {
            "temperature": SimulatedMetric(
                name="temperature",
                value=65.0,
                min_value=20.0,
                max_value=100.0,
                noise=0.3,
                drift=0.1,  # Naturally heats up
                inertia=0.9
            ),
            "fan_speed": SimulatedMetric(
                name="fan_speed",
                value=30.0,
                min_value=0.0,
                max_value=100.0,
                noise=0.1,
                inertia=0.7
            ),
            "target": SimulatedMetric(
                name="target",
                value=65.0,
                min_value=20.0,
                max_value=80.0,
                noise=0.0,
                inertia=1.0  # Instant
            ),
        }

    def _setup_load_balancer(self) -> None:
        """Setup load balancer scenario."""
        self.metrics = {
            "cpu_usage": SimulatedMetric(
                name="cpu_usage",
                value=50.0,
                min_value=0.0,
                max_value=100.0,
                noise=2.0,
                drift=0.5,  # Load naturally increases
                inertia=0.85
            ),
            "memory_usage": SimulatedMetric(
                name="memory_usage",
                value=40.0,
                min_value=0.0,
                max_value=100.0,
                noise=1.0,
                drift=0.2,
                inertia=0.9
            ),
            "queue_depth": SimulatedMetric(
                name="queue_depth",
                value=500.0,
                min_value=0.0,
                max_value=20000.0,
                noise=5.0,
                drift=50.0,  # Requests keep coming
                inertia=0.7
            ),
            "latency_p95": SimulatedMetric(
                name="latency_p95",
                value=30.0,
                min_value=1.0,
                max_value=500.0,
                noise=3.0,
                inertia=0.8
            ),
            "active_lanes": SimulatedMetric(
                name="active_lanes",
                value=4.0,
                min_value=1.0,
                max_value=8.0,
                noise=0.0,
                inertia=1.0
            ),
        }

    def _setup_frame_optimizer(self) -> None:
        """Setup frame optimizer scenario."""
        self.metrics = {
            "fps": SimulatedMetric(
                name="fps",
                value=55.0,
                min_value=10.0,
                max_value=144.0,
                noise=2.0,
                inertia=0.85
            ),
            "frame_time": SimulatedMetric(
                name="frame_time",
                value=18.0,
                min_value=7.0,
                max_value=100.0,
                noise=1.0,
                inertia=0.85
            ),
            "gpu_usage": SimulatedMetric(
                name="gpu_usage",
                value=70.0,
                min_value=0.0,
                max_value=100.0,
                noise=1.5,
                drift=0.3,
                inertia=0.9
            ),
            "vram_usage": SimulatedMetric(
                name="vram_usage",
                value=60.0,
                min_value=0.0,
                max_value=100.0,
                noise=0.5,
                drift=0.1,
                inertia=0.95
            ),
            "render_quality": SimulatedMetric(
                name="render_quality",
                value=3.0,
                min_value=1.0,
                max_value=5.0,
                noise=0.0,
                inertia=1.0
            ),
        }

    def read(self, metric: str) -> float:
        """Read a metric value."""
        if metric in self.metrics:
            return self.metrics[metric].value
        return 0.0

    def read_all(self) -> Dict[str, float]:
        """Read all metric values."""
        return {name: m.value for name, m in self.metrics.items()}

    def apply_action(self, action: str, parameters: Dict[str, int]) -> bool:
        """Apply an action to the system."""
        if self.scenario == "thermostat":
            return self._apply_thermostat_action(action, parameters)
        elif self.scenario == "load_balancer":
            return self._apply_load_balancer_action(action, parameters)
        elif self.scenario == "frame_optimizer":
            return self._apply_frame_action(action, parameters)
        return False

    def _apply_thermostat_action(self, action: str, params: Dict[str, int]) -> bool:
        """Apply thermostat actions."""
        level = params.get("amount", params.get("level", 1))

        if action == "increase_fan":
            self.metrics["fan_speed"].apply_effect(level * 10)
            # Fan increase -> temperature decrease
            self.metrics["temperature"].apply_effect(-level * 3)
            return True

        elif action == "decrease_fan":
            self.metrics["fan_speed"].apply_effect(-level * 10)
            # Fan decrease -> temperature increase
            self.metrics["temperature"].apply_effect(level * 2)
            return True

        elif action == "emergency_cooling":
            self.metrics["fan_speed"].set_target(100)
            self.metrics["temperature"].apply_effect(-15)
            return True

        return False

    def _apply_load_balancer_action(self, action: str, params: Dict[str, int]) -> bool:
        """Apply load balancer actions."""
        if action == "scale_up":
            lanes = params.get("lanes", 1)
            self.metrics["active_lanes"].apply_effect(lanes)
            self.metrics["cpu_usage"].apply_effect(-lanes * 10)
            self.metrics["queue_depth"].apply_effect(-lanes * 500)
            return True

        elif action == "scale_down":
            lanes = params.get("lanes", 1)
            self.metrics["active_lanes"].apply_effect(-lanes)
            self.metrics["cpu_usage"].apply_effect(lanes * 8)
            return True

        elif action == "shed_load":
            percent = params.get("percent", 10)
            self.metrics["queue_depth"].apply_effect(-percent * 100)
            self.metrics["cpu_usage"].apply_effect(-percent * 2)
            return True

        elif action == "throttle":
            self.metrics["cpu_usage"].apply_effect(-15)
            self.metrics["latency_p95"].apply_effect(20)
            return True

        elif action == "free_cache":
            self.metrics["memory_usage"].apply_effect(-15)
            self.metrics["latency_p95"].apply_effect(5)
            return True

        return False

    def _apply_frame_action(self, action: str, params: Dict[str, int]) -> bool:
        """Apply frame optimizer actions."""
        if action == "increase_quality":
            self.metrics["render_quality"].apply_effect(1)
            self.metrics["gpu_usage"].apply_effect(15)
            self.metrics["fps"].apply_effect(-10)
            return True

        elif action == "decrease_quality":
            self.metrics["render_quality"].apply_effect(-1)
            self.metrics["gpu_usage"].apply_effect(-12)
            self.metrics["fps"].apply_effect(8)
            return True

        elif action == "flush_vram":
            self.metrics["vram_usage"].apply_effect(-20)
            self.metrics["frame_time"].apply_effect(5)
            return True

        elif action == "dynamic_resolution":
            scale = params.get("scale", 75) / 100.0
            self.metrics["gpu_usage"].apply_effect(-(1 - scale) * 30)
            self.metrics["fps"].apply_effect((1 - scale) * 20)
            return True

        return False

    def tick(self) -> Dict[str, float]:
        """Advance simulation by one tick."""
        self.tick_count += 1

        # Apply scenario-specific physics
        self._apply_physics()

        # Update all metrics
        for metric in self.metrics.values():
            metric.tick()

        return self.read_all()

    def _apply_physics(self) -> None:
        """Apply physics relationships between metrics."""
        if self.scenario == "thermostat":
            # Higher fan speed -> lower temperature drift
            fan = self.metrics["fan_speed"].value
            self.metrics["temperature"].drift = 0.3 - (fan / 100) * 0.4

        elif self.scenario == "load_balancer":
            # Higher CPU usage -> higher latency
            cpu = self.metrics["cpu_usage"].value
            self.metrics["latency_p95"].drift = cpu * 0.1

            # Queue depth affects CPU
            queue = self.metrics["queue_depth"].value
            self.metrics["cpu_usage"].drift = 0.1 + (queue / 20000) * 0.5

        elif self.scenario == "frame_optimizer":
            # GPU usage inversely affects FPS
            gpu = self.metrics["gpu_usage"].value
            self.metrics["fps"].drift = -gpu * 0.02

            # FPS and frame_time are inversely related
            fps = self.metrics["fps"].value
            if fps > 0:
                self.metrics["frame_time"].set_target(1000 / fps)

    def inject_event(self, event: str) -> None:
        """Inject a simulated event (spike, chaos, etc.)."""
        if event == "spike":
            if self.scenario == "thermostat":
                self.metrics["temperature"].apply_effect(15)
            elif self.scenario == "load_balancer":
                self.metrics["queue_depth"].apply_effect(5000)
                self.metrics["cpu_usage"].apply_effect(25)
            elif self.scenario == "frame_optimizer":
                self.metrics["gpu_usage"].apply_effect(20)

        elif event == "emergency":
            if self.scenario == "thermostat":
                self.metrics["temperature"].set_target(92)
            elif self.scenario == "load_balancer":
                self.metrics["cpu_usage"].set_target(95)
            elif self.scenario == "frame_optimizer":
                self.metrics["gpu_usage"].set_target(98)

        elif event == "calm":
            # Return to normal
            for metric in self.metrics.values():
                metric.set_target((metric.min_value + metric.max_value) / 2)

    def __repr__(self) -> str:
        values = ", ".join(f"{k}={v:.1f}" for k, v in self.read_all().items())
        return f"SimulatedSystem({self.scenario}, tick={self.tick_count}, {values})"
