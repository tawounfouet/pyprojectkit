# D-02 - Milestone dans Project et règles de dates

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-02`, `ADR-06-002`, `ADR-07-001`, `ADR-APP-03`, `ADR-PJ-10-05`.

## Options et décision à prendre

Qui garantit l'identité, l'échéance et l'atteinte d'un jalon M0, et à quel endroit sa mutation est-elle sauvegardée ?

**A - RECOMMANDEE :** `Milestone` est une Entity possédée par `Project`, sauvegardée via `ProjectRepository`. Le jalon a un `MilestoneId` stable, une date cible, un éventuel `reached_at`, des règles de clôture locales ; il ne possède pas de Repository/UnitOfWork autonomes en M0.

**B :** `Milestone` Aggregate Root séparé avec `MilestoneRepository`, à envisager si contention ou owners indépendants démontrés.

## Contraintes proposées

- Cardinalité : `Project 1 -> 0..N Milestone`. Un `Project` peut donc exister sans jalon.
- `target_date` : obligatoire pour une Entity Milestone M0 selon `07 V2 INV-MILE-002`. Le payload d'event illustratif `due_at?` dans `09 V2 §13` ne modifie pas silencieusement cette règle.
- `reached_at` : présent uniquement lorsque le jalon est atteint, dérivé de `Clock` injectable et cohérent avec les règles de temps.
- Une date dépassée ne modifie pas automatiquement l'état : la vue `MISSED` peut être dérivée si la policy l'autorise.
- `MarkMilestoneReached` respecte l'autorisation du Project, son état et `expected_version`. Le changement persiste dans une seule transaction Project.
- Les liens entre `Task` et `Milestone` sont des IDs, et ne transforment pas `Task` en Entity interne au Project.

## Cas négatifs et preuves futures

- Rejeter échéance absente/invalide si `target_date` requis.
- Refuser d'atteindre un jalon inexistant, déjà atteint sans transition valable, ou non visible.
- Refuser un `save(Project)` avec version obsolète ; aucun événement de succès.
- Vérifier un `Project` sans jalon ; pas de restriction `1..*` issue de l'infographie.

## Compromis et points d'arbitrage

A évite la surarchitecture mais augmente le versionnement du Project en cas de changements fréquents des jalons. **Question explicite :** choisir le nom public canonique `target_date` et la conversion éventuelle en `due_at` de l'événement. Ne pas inventer la précision heure/jour sans règle métier.

## Sources

`05 V2 §10`; `06 V2 §§11, 13, 20`; `07 V2 §11 (INV-MILE-001..004)`; `08 V2 §11.13`; `09 V2 §13`; `10 V2 §14`.

## Verdict

**Option A recommandée ; PROPOSED.** Toute acceptation doit inclure la décision sur date cible et nommage événementiel ; tests et implémentation non exécutés.