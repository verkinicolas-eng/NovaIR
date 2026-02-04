# FAQ - NovaIR

> Questions frequemment posees sur NovaIR

---

## General

### Qu'est-ce que NovaIR ?

NovaIR (Nova Intermediate Representation) est un langage declaratif (DSL) ou les systemes expriment leurs **contraintes** et **objectifs**, plutot que des instructions etape par etape. Le runtime NovaIR decide automatiquement de la meilleure action a entreprendre.

### En quoi est-ce different de la programmation traditionnelle ?

| Approche | Programmation traditionnelle | NovaIR |
|----------|------------------------------|--------|
| Style | Imperatif (if/else, boucles) | Declaratif (contraintes, objectifs) |
| Qui decide | Le programmeur ecrit toutes les decisions | Le runtime trouve la meilleure action |
| Cas imprevus | Comportement indefini | Le scoring trouve une action adaptee |
| Evolution | Modifier le code | Ajouter une ligne de contrainte |

### A quoi sert NovaIR ?

NovaIR est concu pour la **regulation de systemes** :
- Thermoregulation (CPU, GPU, datacenters)
- Load balancing (serveurs, microservices)
- Optimisation de ressources (memoire, energie)
- Systemes embarques avec contraintes multiples
- IoT et automatisation industrielle

---

## Technique

### NovaIR est-il un langage de programmation complet ?

Non. NovaIR est un **DSL** (Domain-Specific Language) specialise pour la regulation. Il ne remplace pas Python, Rust ou C++. Il se concentre uniquement sur l'expression de contraintes et objectifs.

### Comment fonctionne le scoring ?

A chaque tick, le runtime :
1. Lit l'etat actuel du systeme
2. Verifie les violations de contraintes
3. Evalue chaque action candidate
4. Calcule un score base sur les objectifs et leurs priorites
5. Execute l'action avec le meilleur score (si > seuil)

```
score(action) = SUM(priority[obj] * impact_estime(action, obj))
```

### Qu'est-ce qu'une contrainte @critical vs @warning ?

- **@critical** : Violation inacceptable. Le runtime priorise les actions qui resolvent cette violation.
- **@warning** : Situation a eviter mais tolerable temporairement.

### Que signifie le `tick` ?

Le `tick` definit la frequence de decision du runtime :
```novair
tick:
  interval: 100 ms    # Evaluer toutes les 100ms
  action_threshold: 0.5  # Score minimum pour agir
  mode: continuous    # Mode continu vs reactive
```

---

## Performance

### NovaIR est-il plus lent que if/else ?

Les benchmarks montrent que NovaIR a un temps de reponse ~1.67x plus eleve que if/else classique (0.38ms vs 0.12ms). C'est acceptable pour la majorite des cas d'usage de regulation.

### Quels sont les avantages mesures ?

| Metrique | Avantage NovaIR |
|----------|-----------------|
| Conformite | +2% en moyenne |
| Oscillations | -33% |
| Temps de recuperation | -26% |
| Lignes de code | -67% |
| Complexite cyclomatique | -75% |

---

## Implementation

### Existe-t-il un parser/runtime NovaIR ?

Le projet inclut un parser basique en Python dans `src/parser/`. Un runtime de reference est prevu mais pas encore disponible.

### Puis-je utiliser NovaIR en production ?

NovaIR est actuellement un **prototype de recherche**. Il demontre la viabilite du paradigme declaratif pour la regulation. Une implementation production-ready necessiterait :
- Parser robuste avec gestion d'erreurs
- Runtime optimise
- Integration avec des systemes de monitoring
- Tests extensifs

### Comment contribuer ?

Voir [CONTRIBUTING.md](../CONTRIBUTING.md) pour les guidelines de contribution.

---

## Philosophie

### Pourquoi "les machines expriment leurs besoins" ?

L'idee centrale de NovaIR est d'inverser le paradigme historique :
- **Avant** : Humain anticipe tout → ecrit des if/else → machine execute aveuglement
- **NovaIR** : Machine declare son cadre (contraintes, objectifs) → runtime autonome decide

C'est comme passer de "dis-moi exactement quoi faire" a "voici mes limites et mes objectifs, trouve la meilleure solution".

### NovaIR remplace-t-il l'intelligence humaine ?

Non. L'humain definit toujours :
- Les etats a observer
- Les contraintes a respecter
- Les objectifs et leurs priorites
- Les actions possibles et leurs effets

Le runtime automatise uniquement la **decision** dans ce cadre defini par l'humain.

---

*Pour plus de details, voir la [Specification](SPECIFICATION.md) et le [Manifesto](MANIFESTO.md).*
