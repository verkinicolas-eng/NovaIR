#!/usr/bin/env python3
"""
NovaIR Full Demo - Shows the complete system in action.

This demo:
1. Parses a NovaIR file
2. Creates a simulated system
3. Runs the engine
4. Shows how NovaIR makes decisions

Run: python -m src.demo
"""

import time
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import parse_file
from src.runtime import Engine, EngineConfig
from src.connectors import SimulatedSystem


def print_header(text: str) -> None:
    """Print a section header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(engine: Engine, sim: SimulatedSystem) -> None:
    """Print current status."""
    status = engine.get_status()

    print(f"\n--- Tick {engine._tick_count} ---")
    print(f"State: {', '.join(f'{k}={v:.1f}' for k, v in status['state'].items())}")

    if status['violations']:
        print(f"VIOLATIONS: {status['violations']}")

    last = engine.get_last_tick()
    if last and last.selected_action:
        print(f"Action: {last.selected_action}")
        print(f"  Score: {last.selected_action.score:.2f}")
        print(f"  Effects: {last.selected_action.predicted_effects}")


def demo_thermostat():
    """Demo the thermostat scenario."""
    print_header("THERMOSTAT DEMO")

    # 1. Parse the NovaIR file
    print("\n[1] Parsing thermostat.novair...")
    system = parse_file("examples/thermostat.novair")
    print(f"    Loaded: {system.name} v{system.version}")
    print(f"    States: {[s.name for s in system.states]}")
    print(f"    Constraints: {[c.name for c in system.constraints]}")
    print(f"    Objectives: {[o.name for o in system.objectives]}")
    print(f"    Actions: {[a.name for a in system.actions]}")

    # 2. Create simulation
    print("\n[2] Creating simulated system...")
    sim = SimulatedSystem(scenario="thermostat")
    print(f"    Initial state: {sim.read_all()}")

    # 3. Create engine
    print("\n[3] Creating NovaIR engine...")
    config = EngineConfig(
        tick_interval_ms=100,
        action_threshold=0.3,
        dry_run=False
    )
    engine = Engine(system, config)

    # 4. Connect simulation to engine
    print("\n[4] Connecting simulation...")

    # State readers
    engine.register_state_reader("temperature", lambda: sim.read("temperature"))
    engine.register_state_reader("target", lambda: sim.read("target"))
    engine.register_state_reader("fan_speed", lambda: sim.read("fan_speed"))

    # Action handlers
    engine.register_action_handler("increase_fan",
        lambda p: sim.apply_action("increase_fan", p))
    engine.register_action_handler("decrease_fan",
        lambda p: sim.apply_action("decrease_fan", p))
    engine.register_action_handler("emergency_cooling",
        lambda p: sim.apply_action("emergency_cooling", p))

    # 5. Run simulation
    print("\n[5] Running simulation (20 ticks)...")
    print("    Scenario: Normal operation, then temperature spike")

    for i in range(20):
        # Inject spike at tick 8
        if i == 8:
            print("\n>>> INJECTING TEMPERATURE SPIKE <<<")
            sim.inject_event("spike")

        # Tick both simulation and engine
        sim.tick()
        result = engine.tick()

        # Print status every 4 ticks
        if i % 4 == 0 or result.violations:
            print_status(engine, sim)

        time.sleep(0.05)

    # 6. Final status
    print("\n[6] Final Status")
    print(f"    Temperature: {sim.read('temperature'):.1f}°C")
    print(f"    Fan Speed: {sim.read('fan_speed'):.1f}%")
    print(f"    Violations: {engine.scorer.get_critical_violations()}")

    # Explain last decision
    print("\n[7] Decision Explanation")
    print(engine.explain_decision())


def demo_load_balancer():
    """Demo the load balancer scenario."""
    print_header("LOAD BALANCER DEMO")

    system = parse_file("examples/load_balancer.novair")
    sim = SimulatedSystem(scenario="load_balancer")

    config = EngineConfig(tick_interval_ms=50, action_threshold=0.3)
    engine = Engine(system, config)

    # Connect
    for state in ["cpu_usage", "memory_usage", "queue_depth", "latency_p95", "active_lanes"]:
        engine.register_state_reader(state, lambda s=state: sim.read(s))

    for action in ["scale_up", "scale_down", "shed_load", "throttle", "free_cache"]:
        engine.register_action_handler(action, lambda p, a=action: sim.apply_action(a, p))

    print("\n[5] Running simulation (15 ticks)...")
    print("    Scenario: Load increases until critical, then stabilizes")

    for i in range(15):
        if i == 5:
            print("\n>>> INJECTING TRAFFIC SPIKE <<<")
            sim.inject_event("spike")

        sim.tick()
        result = engine.tick()

        if i % 3 == 0 or result.violations:
            print_status(engine, sim)

        time.sleep(0.03)

    print("\n[6] Final Status")
    print(f"    CPU: {sim.read('cpu_usage'):.1f}%")
    print(f"    Queue: {sim.read('queue_depth'):.0f}")
    print(f"    Active Lanes: {sim.read('active_lanes'):.0f}")


def demo_comparison():
    """Demo: NovaIR vs traditional if/else."""
    print_header("COMPARISON: NovaIR vs If/Else")

    print("""
Traditional approach (if/else):
-------------------------------
```python
if temperature > 85:
    increase_fan(max_level)
elif temperature > 75:
    increase_fan(medium_level)
elif temperature < 60:
    decrease_fan()
```

Problems:
- What if temp is 84.9? Nothing happens.
- What if fan is already at max? Stuck.
- Adding "energy saving mode"? Rewrite all logic.
- New sensor added? More if/else chains.

NovaIR approach:
----------------
```novair
constraints:
  max_temp : temperature <= 85  @critical

objectives:
  comfort : temperature -> target(65)  @priority(8)
  silence : fan_speed -> min           @priority(4)
```

Advantages:
- Handles ALL temperature values via scoring
- Balances multiple objectives automatically
- Adding new rule = 1 line
- Runtime adapts to unforeseen cases
""")

    # Demonstrate with a tricky case
    print("\nDemo: Tricky case (temp=84, fan at 90%)")
    print("-" * 40)

    system = parse_file("examples/thermostat.novair")
    sim = SimulatedSystem(scenario="thermostat")

    # Set tricky initial state
    sim.metrics["temperature"].value = 84
    sim.metrics["fan_speed"].value = 90

    engine = Engine(system, EngineConfig(action_threshold=0.1))
    engine.register_state_reader("temperature", lambda: sim.read("temperature"))
    engine.register_state_reader("fan_speed", lambda: sim.read("fan_speed"))
    engine.register_state_reader("target", lambda: sim.read("target"))

    # Single tick
    engine.read_states()
    result = engine.tick()

    print(f"State: temp={sim.read('temperature'):.1f}, fan={sim.read('fan_speed'):.1f}")
    print(f"Constraints: {[(c.constraint.name, c.margin) for c in engine.scorer.check_constraints()]}")
    print(f"\nNovaIR decision: {result.selected_action}")
    print(f"\nExplanation:\n{engine.explain_decision()}")


def main():
    print("""
================================================================
                    NovaIR Runtime Demo

  "When machines express their needs"
================================================================
""")

    try:
        demo_thermostat()
        demo_load_balancer()
        demo_comparison()

        print_header("DEMO COMPLETE")
        print("""
NovaIR successfully demonstrated:
✓ Parsing declarative system definitions
✓ Constraint checking with severity levels
✓ Objective optimization with priorities
✓ Action scoring and selection
✓ Simulated system control
✓ Response to unexpected events (spikes)

The system made autonomous decisions based on:
- Current state values
- Constraint violations (critical/warning)
- Objective priorities
- Predicted action effects
- Action costs
""")

    except FileNotFoundError as e:
        print(f"Error: Could not find example file. Run from NovaIR root directory.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
