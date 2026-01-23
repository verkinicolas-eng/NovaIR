# NovaIR SPECIFICATION

## Overview

NovaIR is an intermediate representation where machines express their states, constraints, and objectives. The NovaIR runtime makes autonomous decisions within this defined framework.

## Architecture

```
+-----------------------------------------------------------+
|                      NovaIR Runtime                        |
+-----------------------------------------------------------+
|  +---------+  +-------------+  +------------------+       |
|  | Current |  | Declared    |  |   Objectives     |       |
|  |  State  |  | Constraints |  | (with priorities)|       |
|  +----+----+  +------+------+  +--------+---------+       |
|       |              |                  |                 |
|       +--------------+------------------+                 |
|                      v                                    |
|            +------------------+                           |
|            |    Candidate     |                           |
|            |    Evaluator     |                           |
|            +--------+---------+                           |
|                     v                                     |
|            +------------------+                           |
|            |    Available     |                           |
|            |    Actions       |                           |
|            +--------+---------+                           |
|                     v                                     |
|            +------------------+                           |
|            |    Decision      |                           |
|            |    (scoring)     |                           |
|            +--------+---------+                           |
|                     v                                     |
|            +------------------+                           |
|            |    Execution     |                           |
|            +------------------+                           |
+-----------------------------------------------------------+
```

## Declaration Format

### States

```yaml
states:
  cpu_usage:
    type: percentage
    source: system

  ram_usage:
    type: bytes
    source: system

  latency:
    type: duration_ms
    source: measurement

  mode:
    type: enum
    values: [normal, degraded, emergency]
```

### Constraints

```yaml
constraints:
  - name: cpu_max
    metric: cpu_usage
    operator: "<="
    value: 80%
    violation: critical

  - name: ram_max
    metric: ram_usage
    operator: "<="
    value: 4GB
    violation: critical

  - name: latency_max
    metric: latency
    operator: "<="
    value: 100ms
    violation: warning
```

### Objectives

```yaml
objectives:
  - name: low_latency
    metric: latency
    target: "<= 50ms"
    priority: 10

  - name: cpu_efficient
    metric: cpu_usage
    target: "<= 50%"
    priority: 5

  - name: stability
    metric: jitter
    target: "<= 10ms"
    priority: 7
```

### Actions

```yaml
actions:
  - name: throttle
    parameters:
      - lane: string
      - factor: float [0.0, 1.0]
    effects:
      - cpu_usage: decreases
      - latency: may increase

  - name: pause
    parameters:
      - lane: string
      - duration: duration_ms
    effects:
      - cpu_usage: decreases significantly
      - throughput: decreases

  - name: free_cache
    parameters: []
    effects:
      - ram_usage: decreases
      - latency: may increase temporarily
```

## Decision Algorithm

```
Each tick:
  1. READ current_state

  2. FOR EACH constraint:
       IF violation(constraint, current_state):
         mark urgency(constraint)

  3. candidates = []
     FOR EACH action IN available_actions:
       FOR EACH parameterization IN parameterizations(action):
         candidate = {action, parameterization}
         candidate.score = calculate_score(candidate, objectives, current_state)
         candidates.append(candidate)

  4. IF urgency_active:
       candidates = filter(candidates, resolves_urgency)

  5. best = max(candidates, by=score)

  6. IF best.score > minimum_threshold:
       execute(best.action)
     ELSE:
       do_nothing()
```

## Score Calculation

```
score(candidate) = SUM(priority[obj] * estimated_impact(candidate, obj))

estimated_impact = prediction of the action's effect on the objective's metric
```

## Lifecycle

```
INIT -> RUNNING -> ADAPTING -> RUNNING -> ... -> SHUTDOWN
          ^           |
          +-----------+
```

- **INIT**: Loading declarations (states, constraints, objectives, actions)
- **RUNNING**: Normal tick loop
- **ADAPTING**: Response to constraint violation or environment change
- **SHUTDOWN**: Clean shutdown
