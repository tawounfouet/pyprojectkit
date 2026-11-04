# ADR-M2-05 - WorkItemRef est une référence, pas un Aggregate Root

- Date : 2026-11-04
- Statut : PROPOSED / revue humaine requise
- Tranche : M2-A, M2-02

## Contexte
M0/M1 définissent `Project`, `Task`, `RegistryEntry` et `NextAction`. Le terme `Work Item` chez Pythos désigne une unité opératoire, pas un agrégat M1 existant.

## Décision candidate
`WorkItemRef(kind="TASK", id=TaskId)` identifie une `Task` déjà persistée. `BuildAuthorizedOperatingBrief` résout cette référence via le reader `RegistryService.list_tasks`. Toute nouvelle famille de travail nécessitera un ADR et un cas métier supplémentaire.

## Rejet
Pas de classe `WorkItem` dans `domain.py`, pas de table universelle `work_items`, pas de seconde machine à états.

## Validation
La tâche doit appartenir au projet demandé et être visible sous les permissions M1, y compris propriétaire et classification. Les versions M1 sont conservées sous forme de watermark de projection.
