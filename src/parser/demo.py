#!/usr/bin/env python3
"""
NovaIR Parser Demo - Demonstrates parsing of NovaIR files.

Run: python -m src.parser.demo
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.parser import parse_string, parse_file


def demo_parse_string():
    """Demo parsing a NovaIR string."""
    source = '''
system Thermostat @version("1.0")

state:
  temperature <- sensors.cpu.temp
  fan_speed <- actuators.fan.speed

constraints:
  max_temp : temperature <= 85 @critical
  min_temp : temperature >= 30 @warning

objectives:
  comfort : temperature -> target(65) @priority(8)
  silence : fan_speed -> min @priority(4)

actions:
  increase_fan:
    parameters: [level: 1..5]
    effects:
      temperature: -5 to -15
      fan_speed: +20 to +100
    cost: low

  decrease_fan:
    effects:
      temperature: +3 to +10
      fan_speed: -20 to -100
    cost: low

tick:
  interval: 100 ms
  action_threshold: 0.5
  mode: continuous
'''

    print("=" * 60)
    print("NovaIR Parser Demo")
    print("=" * 60)
    print()
    print("Input source:")
    print("-" * 40)
    print(source)
    print("-" * 40)
    print()

    try:
        system = parse_string(source)

        print("Parsed successfully!")
        print()
        print(f"System: {system.name} (v{system.version})")
        print()

        print("States:")
        for state in system.states:
            print(f"  - {state}")
        print()

        print("Constraints:")
        for constraint in system.constraints:
            print(f"  - {constraint}")
        print()

        print("Objectives:")
        for objective in system.objectives:
            print(f"  - {objective}")
        print()

        print("Actions:")
        for action in system.actions:
            print(f"  - {action.name}:")
            if action.parameters:
                print(f"      params: {[str(p) for p in action.parameters]}")
            print(f"      effects: {[str(e) for e in action.effects]}")
            print(f"      cost: {action.cost.value}")
        print()

        if system.tick:
            print(f"Tick: {system.tick.interval_ms}ms, threshold={system.tick.action_threshold}, mode={system.tick.mode.value}")
        print()

        # Validate
        errors = system.validate()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Validation: OK")

        print()
        print("=" * 60)
        print("Reconstructed output:")
        print("=" * 60)
        print(system)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def demo_parse_file():
    """Demo parsing a .novair file."""
    # Find example files
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")

    if os.path.exists(examples_dir):
        print()
        print("=" * 60)
        print("Parsing example files:")
        print("=" * 60)

        for filename in os.listdir(examples_dir):
            if filename.endswith(".novair"):
                filepath = os.path.join(examples_dir, filename)
                print(f"\nFile: {filename}")
                print("-" * 40)

                try:
                    system = parse_file(filepath)
                    print(f"  System: {system.name}")
                    print(f"  States: {len(system.states)}")
                    print(f"  Constraints: {len(system.constraints)}")
                    print(f"  Objectives: {len(system.objectives)}")
                    print(f"  Actions: {len(system.actions)}")

                    errors = system.validate()
                    if errors:
                        print(f"  Validation: {len(errors)} errors")
                        for error in errors:
                            print(f"    - {error}")
                    else:
                        print("  Validation: OK")

                except Exception as e:
                    print(f"  Error: {e}")


if __name__ == "__main__":
    demo_parse_string()
    demo_parse_file()
