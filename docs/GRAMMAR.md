# Grammaire NovaIR - Specification EBNF

> Grammaire formelle du langage NovaIR en notation EBNF

---

## Vue d'ensemble

NovaIR utilise une syntaxe inspiree de YAML avec des annotations specifiques.
La grammaire ci-dessous definit la structure complete d'un fichier `.novair`.

---

## Grammaire EBNF

```ebnf
(* ============================================ *)
(* STRUCTURE PRINCIPALE                         *)
(* ============================================ *)

program         = system_decl, { section } ;

system_decl     = "system", identifier, [ version_annotation ], newline ;

version_annotation = "@version", "(", string_literal, ")" ;

section         = state_section
                | constraints_section
                | objectives_section
                | actions_section
                | tick_section ;

(* ============================================ *)
(* SECTION STATE                                *)
(* ============================================ *)

state_section   = "state:", newline, { state_binding } ;

state_binding   = indent, identifier, "<-", source_path, newline ;

source_path     = identifier, { ".", identifier } ;

(* ============================================ *)
(* SECTION CONSTRAINTS                          *)
(* ============================================ *)

constraints_section = "constraints:", newline, { constraint_decl } ;

constraint_decl = indent, identifier, ":", expression, severity_annotation, newline ;

expression      = identifier, comparison_op, value_with_unit ;

comparison_op   = "<=" | ">=" | "==" | "!=" | "<" | ">" ;

severity_annotation = "@critical" | "@warning" ;

(* ============================================ *)
(* SECTION OBJECTIVES                           *)
(* ============================================ *)

objectives_section = "objectives:", newline, { objective_decl } ;

objective_decl  = indent, identifier, ":", identifier, "->", objective_type, priority_annotation, newline ;

objective_type  = "target", "(", value_with_unit, ")"
                | "min"
                | "max" ;

priority_annotation = "@priority", "(", integer, ")" ;

(* ============================================ *)
(* SECTION ACTIONS                              *)
(* ============================================ *)

actions_section = "actions:", newline, { action_decl } ;

action_decl     = indent, identifier, ":", newline,
                  [ parameters_block ],
                  effects_block,
                  [ cost_line ] ;

parameters_block = indent2, "parameters:", "[", parameter_list, "]", newline ;

parameter_list  = parameter, { ",", parameter } ;

parameter       = identifier, ":", range_type ;

range_type      = integer, "..", integer ;

effects_block   = indent2, "effects:", newline, { effect_line } ;

effect_line     = indent3, identifier, ":", effect_value, newline ;

effect_value    = signed_value_with_unit
                | range_effect ;

range_effect    = signed_value_with_unit, "to", signed_value_with_unit ;

signed_value_with_unit = [ "+" | "-" ], value_with_unit ;

cost_line       = indent2, "cost:", cost_level, newline ;

cost_level      = "low" | "medium" | "high" ;

(* ============================================ *)
(* SECTION TICK                                 *)
(* ============================================ *)

tick_section    = "tick:", newline, { tick_property } ;

tick_property   = indent, tick_key, ":", tick_value, newline ;

tick_key        = "interval" | "action_threshold" | "mode" ;

tick_value      = duration
                | decimal
                | tick_mode ;

duration        = integer, duration_unit ;

duration_unit   = "ms" | "s" | "m" | "h" ;

tick_mode       = "continuous" | "reactive" ;

(* ============================================ *)
(* VALEURS ET UNITES                            *)
(* ============================================ *)

value_with_unit = number, [ unit ] ;

unit            = temperature_unit
                | percentage_unit
                | data_unit
                | time_unit
                | frequency_unit
                | custom_unit ;

temperature_unit = "°C" | "°F" | "K" ;

percentage_unit  = "%" ;

data_unit        = "B" | "KB" | "MB" | "GB" | "TB" ;

time_unit        = "ms" | "s" | "m" | "h" ;

frequency_unit   = "Hz" | "kHz" | "MHz" | "GHz" ;

custom_unit      = identifier ;

(* ============================================ *)
(* TOKENS DE BASE                               *)
(* ============================================ *)

identifier      = letter, { letter | digit | "_" } ;

string_literal  = '"', { character - '"' }, '"' ;

integer         = digit, { digit } ;

decimal         = integer, [ ".", integer ] ;

number          = decimal ;

letter          = "a".."z" | "A".."Z" ;

digit           = "0".."9" ;

character       = ? any printable character ? ;

newline         = "\n" ;

indent          = "  " ;                  (* 2 espaces *)

indent2         = "    " ;                (* 4 espaces *)

indent3         = "      " ;              (* 6 espaces *)

comment         = "#", { character }, newline ;
```

---

## Exemples de tokens

### Identifiants valides
```
temperature
cpu_usage
maxTemp
sensor1
GPU_Temp
```

### Identifiants invalides
```
1sensor      (commence par un chiffre)
max-temp     (tiret interdit)
cpu usage    (espace interdit)
```

### Valeurs avec unites
```
85°C         (temperature Celsius)
100%         (pourcentage)
4GB          (donnees)
500ms        (duree)
60           (sans unite)
```

### Effets
```
+10%                    (augmentation fixe)
-5°C                    (diminution fixe)
-5°C to -15°C           (plage d'effet)
+20% to +100%           (plage pourcentage)
```

---

## Precedence des operateurs

| Priorite | Operateur | Associativite |
|----------|-----------|---------------|
| 1 (haute) | `->` | Gauche |
| 2 | `<=`, `>=`, `<`, `>` | Gauche |
| 3 | `==`, `!=` | Gauche |
| 4 (basse) | `:` (binding) | Droite |

---

## Mots reserves

Les mots suivants sont reserves et ne peuvent pas etre utilises comme identifiants :

```
system      state       constraints     objectives
actions     tick        target          min
max         parameters  effects         cost
interval    mode        continuous      reactive
low         medium      high            to
```

---

## Annotations

| Annotation | Contexte | Description |
|------------|----------|-------------|
| `@version("x.y")` | system | Version du systeme |
| `@critical` | constraint | Contrainte critique |
| `@warning` | constraint | Contrainte d'alerte |
| `@priority(n)` | objective | Priorite (1-10) |

---

## Commentaires

```novair
# Ceci est un commentaire sur une ligne

system Example @version("1.0")

state:
  temp <- sensors.cpu  # Commentaire en fin de ligne
```

---

## Validation

Un fichier NovaIR valide doit :
1. Commencer par une declaration `system`
2. Avoir au moins une section `state:`
3. Avoir au moins une section `constraints:` ou `objectives:`
4. Respecter l'indentation (2 espaces par niveau)
5. Terminer chaque ligne par un saut de ligne

---

## Exemples de validation

### Valide
```novair
system Test @version("1.0")

state:
  x <- source.x

constraints:
  limit : x <= 100 @critical
```

### Invalide - pas de state
```novair
system Test @version("1.0")

constraints:
  limit : x <= 100 @critical
```
Erreur : `state: section required`

### Invalide - indentation incorrecte
```novair
system Test @version("1.0")

state:
x <- source.x    # Manque l'indentation
```
Erreur : `expected indent at line 4`

---

*Grammaire NovaIR v1.0 - Specification formelle*
