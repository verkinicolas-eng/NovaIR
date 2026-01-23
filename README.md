# NovaIR — When Machines Express Their Needs

> **A declarative DSL where systems describe constraints and objectives, not step-by-step instructions.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange.svg)]()

## What is NovaIR?

NovaIR (Nova Intermediate Representation) inverts the historical programming paradigm:

- **Traditional (1950-today)**: Humans write instructions → Machine executes blindly
- **NovaIR**: Machine expresses states/constraints/objectives → Runtime finds optimal actions

Instead of writing `if temperature > 85: activate_cooling()`, you declare:

```novair
constraints:
  safe_temp : temperature <= 85°C  @critical

objectives:
  comfort : temperature -> target(65°C)  @priority(8)
```

The NovaIR runtime **automatically** selects the best action based on current state, constraints, and weighted objectives.

## Quick Examples

### 1. Thermostat Control

```novair
system Thermostat @version("1.0")

state:
  temperature <- sensors.cpu.temp
  fan_speed   <- actuators.fan.speed

constraints:
  max_temp : temperature <= 85°C  @critical
  min_temp : temperature >= 30°C  @warning

objectives:
  comfort   : temperature -> target(65°C)  @priority(8)
  silence   : fan_speed -> min             @priority(4)
  economy   : fan_speed -> min             @priority(3)

actions:
  increase_fan:
    parameters: [level: 1..5]
    effects:
      temperature: -5°C to -15°C
      fan_speed: +20% to +100%
    cost: low

  decrease_fan:
    parameters: [level: 1..5]
    effects:
      temperature: +3°C to +10°C
      fan_speed: -20% to -100%
    cost: low

tick:
  interval: 100 ms
  action_threshold: 0.5
  mode: continuous
```

### 2. Load Shedding

```novair
system LoadBalancer @version("1.0")

state:
  cpu_usage    <- metrics.cpu.percent
  memory_usage <- metrics.memory.percent
  request_rate <- metrics.requests.per_second

constraints:
  cpu_limit    : cpu_usage <= 80%     @critical
  memory_limit : memory_usage <= 85%  @critical

objectives:
  performance : request_rate -> max   @priority(9)
  stability   : cpu_usage -> target(60%)  @priority(7)

actions:
  shed_load:
    effects:
      cpu_usage: -15% to -30%
      request_rate: -10% to -20%
    cost: medium

  scale_up:
    effects:
      cpu_usage: -20% to -40%
    cost: high
```

### 3. Smoothness Optimization

```novair
system FrameRateOptimizer @version("1.0")

state:
  fps          <- graphics.framerate
  gpu_temp     <- sensors.gpu.temp
  render_load  <- graphics.render.load

constraints:
  thermal_limit : gpu_temp <= 90°C  @critical
  min_fps       : fps >= 30         @warning

objectives:
  smoothness : fps -> target(60)      @priority(10)
  thermal    : gpu_temp -> min        @priority(6)

actions:
  reduce_quality:
    parameters: [level: 1..3]
    effects:
      fps: +10 to +30
      gpu_temp: -5°C to -15°C
    cost: low
```

## Why NovaIR?

| Aspect | Traditional (if/else) | NovaIR |
|--------|----------------------|--------|
| Logic | Sequential branches | Declarative constraints |
| Adaptation | Modify code | Runtime adapts |
| Adding rules | New if/else | One line |
| Unforeseen cases | Undefined behavior | Scoring finds best action |
| Maintainability | O(n) complexity | O(1) declarations |

## Benchmark Results

NovaIR was tested against a traditional if/else regulator across 6 scenarios:

| Criterion | Result |
|-----------|--------|
| C1: Compliance >= Classic | **PASS** (102%) |
| C2: Response time <= 2x | **PASS** (1.67x) |
| C3: Handles unforeseen cases | **PASS** |
| C4: Dynamic constraint addition | **PASS** |
| C5: Reproducibility | **PASS** |

**NovaIR wins 4/6 scenarios** while maintaining comparable performance.

See [docs/COMPARATIF_PHASE4.md](docs/COMPARATIF_PHASE4.md) for detailed results.

## Documentation

- [Language Specification](docs/LANGAGE_NOVAIR_SPEC.md) — Complete NovaIR syntax
- [Tutorial](docs/TUTORIEL_COMPLET.md) — Step-by-step guide
- [FAQ](docs/FAQ.md) — Common questions
- [Benchmark Report](docs/COMPARATIF_PHASE4.md) — Proof of concept results
- [Grammar](docs/GRAMMAIRE_NOVAIR.md) — Formal EBNF grammar

## Project Status

**Research Prototype / Community Gift / Best Effort**

This is an open-source research project released as a gift to the community. See [MAINTENANCE.md](MAINTENANCE.md) for support expectations.

## License

Apache License 2.0 — See [LICENSE](LICENSE)

## Author

Created by **Nikola (NVK)**

---

*"When you teach a machine to express its needs, you no longer need to anticipate every scenario."*
