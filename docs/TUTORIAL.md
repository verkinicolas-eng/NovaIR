# Tutoriel NovaIR - Guide pas a pas

> Apprenez a ecrire vos premieres declarations NovaIR

---

## Introduction

Ce tutoriel vous guide a travers la creation d'un systeme de regulation complet en NovaIR. A la fin, vous saurez :
- Declarer des etats systeme
- Definir des contraintes
- Exprimer des objectifs
- Definir des actions et leurs effets

---

## Etape 1 : Structure de base

Tout fichier NovaIR commence par la declaration du systeme :

```novair
system MonSysteme @version("1.0")
```

- `system` : mot-cle obligatoire
- `MonSysteme` : nom de votre systeme (PascalCase recommande)
- `@version("1.0")` : annotation de version (optionnel mais recommande)

---

## Etape 2 : Declarer les etats

Les **etats** representent les variables que votre systeme observe :

```novair
state:
  temperature <- sensors.cpu.temp
  fan_speed   <- actuators.fan.speed
  cpu_usage   <- metrics.cpu.percent
```

### Syntaxe
- `nom_etat <- source` : lie un etat a une source de donnees
- Sources typiques : `sensors.*`, `actuators.*`, `metrics.*`

### Types d'etats
| Type | Exemples |
|------|----------|
| Numerique | temperature, cpu_usage, latency |
| Pourcentage | usage: 0-100% |
| Enum | mode: [normal, degraded, emergency] |

---

## Etape 3 : Definir les contraintes

Les **contraintes** definissent les limites que le systeme ne doit pas depasser :

```novair
constraints:
  max_temp : temperature <= 85°C  @critical
  min_temp : temperature >= 30°C  @warning
```

### Syntaxe
- `nom : condition @severite`
- Severites : `@critical` (urgent) ou `@warning` (alerte)

### Operateurs disponibles
| Operateur | Signification |
|-----------|---------------|
| `<=` | Inferieur ou egal |
| `>=` | Superieur ou egal |
| `==` | Egal a |
| `!=` | Different de |
| `<` | Strictement inferieur |
| `>` | Strictement superieur |

### Exemple complet
```novair
constraints:
  cpu_limit    : cpu_usage <= 80%      @critical
  memory_limit : memory_usage <= 85%   @critical
  latency_ok   : latency <= 100ms      @warning
  temp_safe    : temperature <= 90°C   @critical
```

---

## Etape 4 : Exprimer les objectifs

Les **objectifs** definissent ce que le systeme cherche a atteindre :

```novair
objectives:
  comfort   : temperature -> target(65°C)  @priority(8)
  silence   : fan_speed -> min             @priority(4)
  economy   : power_usage -> min           @priority(3)
```

### Types d'objectifs

| Type | Syntaxe | Signification |
|------|---------|---------------|
| Target | `-> target(valeur)` | Atteindre une valeur cible |
| Minimize | `-> min` | Reduire au minimum |
| Maximize | `-> max` | Augmenter au maximum |

### Priorites
- Echelle de 1 a 10
- Plus le chiffre est eleve, plus l'objectif est important
- En cas de conflit, l'objectif avec la plus haute priorite gagne

### Exemple : conflits d'objectifs
```novair
objectives:
  performance : fps -> max           @priority(9)   # Haute priorite
  thermal     : gpu_temp -> min      @priority(6)   # Priorite moyenne
  silence     : fan_noise -> min     @priority(3)   # Basse priorite
```
Ici, le runtime privilegiera le FPS meme si cela augmente la temperature.

---

## Etape 5 : Definir les actions

Les **actions** sont les leviers que le runtime peut utiliser :

```novair
actions:
  increase_fan:
    parameters: [level: 1..5]
    effects:
      temperature: -5°C to -15°C
      fan_speed: +20% to +100%
      noise: +10dB to +30dB
    cost: low

  decrease_fan:
    parameters: [level: 1..5]
    effects:
      temperature: +3°C to +10°C
      fan_speed: -20% to -100%
      noise: -10dB to -30dB
    cost: low

  enable_boost:
    effects:
      performance: +30%
      temperature: +15°C to +25°C
      power: +50W
    cost: medium
```

### Elements d'une action

| Element | Description |
|---------|-------------|
| `parameters` | Variables ajustables (optionnel) |
| `effects` | Impact prevu sur les etats |
| `cost` | Cout de l'action : `low`, `medium`, `high` |

### Notation des effets
- `+10%` : augmentation fixe
- `-5°C to -15°C` : plage d'effet (selon parametres)
- `performance: +30%` : effet sur une metrique

---

## Etape 6 : Configurer le tick

Le **tick** definit quand et comment le runtime prend des decisions :

```novair
tick:
  interval: 100 ms
  action_threshold: 0.5
  mode: continuous
```

### Parametres

| Parametre | Description | Valeurs typiques |
|-----------|-------------|------------------|
| `interval` | Frequence d'evaluation | 50ms - 1000ms |
| `action_threshold` | Score minimum pour agir | 0.3 - 0.7 |
| `mode` | Mode de fonctionnement | `continuous`, `reactive` |

### Modes
- **continuous** : Evalue a chaque tick, meme si tout va bien
- **reactive** : N'evalue que quand une contrainte est violee

---

## Exemple complet : Thermostat CPU

```novair
system CPUThermostat @version("1.0")

# Etats observes
state:
  temperature <- sensors.cpu.temp
  fan_speed   <- actuators.fan.rpm
  cpu_load    <- metrics.cpu.percent

# Limites a ne pas depasser
constraints:
  max_temp : temperature <= 85°C  @critical
  min_temp : temperature >= 30°C  @warning
  max_fan  : fan_speed <= 5000    @warning

# Ce qu'on cherche a atteindre
objectives:
  comfort   : temperature -> target(65°C)  @priority(8)
  silence   : fan_speed -> min             @priority(5)
  longevity : temperature -> min           @priority(3)

# Actions disponibles
actions:
  increase_fan:
    parameters: [level: 1..5]
    effects:
      temperature: -5°C to -15°C
      fan_speed: +500 to +2000
    cost: low

  decrease_fan:
    parameters: [level: 1..5]
    effects:
      temperature: +3°C to +10°C
      fan_speed: -500 to -2000
    cost: low

  throttle_cpu:
    effects:
      temperature: -10°C to -20°C
      cpu_load: -20% to -40%
    cost: medium

# Configuration du runtime
tick:
  interval: 100 ms
  action_threshold: 0.4
  mode: continuous
```

---

## Exercice pratique

Creez un systeme NovaIR pour un **load balancer** avec :
- Etats : `cpu_usage`, `memory_usage`, `request_rate`
- Contraintes : CPU <= 80%, Memory <= 85%
- Objectifs : Maximiser les requetes, stabiliser le CPU a 60%
- Actions : `shed_load`, `scale_up`

<details>
<summary>Solution</summary>

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
  throughput : request_rate -> max       @priority(9)
  stability  : cpu_usage -> target(60%)  @priority(7)

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

tick:
  interval: 500 ms
  action_threshold: 0.5
  mode: continuous
```

</details>

---

## Prochaines etapes

- Consultez les [exemples](../examples/) pour plus de cas d'usage
- Lisez la [Specification complete](SPECIFICATION.md) pour les details techniques
- Explorez la [Grammaire EBNF](GRAMMAR.md) pour la syntaxe formelle

---

*NovaIR - Quand les machines expriment leurs besoins*
