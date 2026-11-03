# D-03 - Graphe de dépendances et concurrence

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-03`, `ADR-06-003`, `ADR-06-016`, `ADR-07-003`, `ADR-APP-04`, `ADR-PJ-10-06`.

## Problème

Les liens `TaskDependency` sont orientés. Deux transactions peuvent vérifier séparément un graphe acyclique, puis écrire chacune un lien qui crée un cycle à leur réunion. Une révision individuelle de Task ne protège pas automatiquement cet invariant collectif.

## Alternatives

**A - RECOMMANDEE :** port `DependencyGraphPort` orienté projet, lecture de `DependencyGraphSnapshot` versionné, mutation conditionnelle `replace_if_version` dans la même UoW locale que l'effet du use case. Protection par verrou ou compare-and-swap sur **une même révision du graphe par Project**, selon l'adapter.

**B :** `DependencyReader` et `DependencyWriter` séparés, sous contrat de snapshot/version commun explicite. Pertinent lorsque la taille du graphe rend A coûteux ; sans garantie partagée, cette variante n'est pas sûre.

**C :** DFS sur snapshot suivi d'ajout d'edge sans contrôle de version. Acceptable seulement pour une démonstration strictement mono-écriture, pas pour un contrat de concurrence sûr.

## Règles proposées

- `Dependency` : VO de lien dirigé. `TaskId` et `depends_on_task_id` sont distincts, identifiables, du même Project pour M0.
- Une dépendance non bloquante n'est pas nécessairement requise avant `StartTask` ; interpréter le type `FINISH_TO_START` selon policy.
- Refuser identité A = A, doublon et A->B->C->A.
- Autorisation vérifiée sur les deux extrémités, aucune révélation d'un TaskId cross-scope.
- `load_for_project` retourne un snapshot cohérent et sa version. Deux écritures concurrentes sur N doivent conduire à au plus une écriture validée pour N, sauf sérialisation équivalente.
- L'événement `TaskDependencyAdded` ne quitte le buffer de succès qu'après confirmation du commit.

## Tests obligatoires

1. A->A refusé et aucune modification.
2. A->B, B->C, C->A refusé ; état de graphe inchangé.
3. A->B et B->A depuis deux snapshots de même version : l'un échoue, ou la sérialisation rejette le second. Jamais de cycle.
4. Perte de commit ou conflit : pas d'événement de succès. Relecture sur issue de commit inconnue.
5. Cross-project/cross-scope : refus non-divulgant.
6. Simulation concurrente InMemory réellement contrôlée ; **ne pas étendre les conclusions à PostgreSQL sans test du backend**.

## Limites assumées

Un UoW InMemory ne démontre pas une isolation SQL. Le port proposé n'est pas un `ProjectSnapshot` M1, ni un Event Store. Un mécanisme de révision par Project est un **choix d'implémentation proposé**, pas une garantie déjà obtenue.

## Sources

`05 V2 §11`; `06 V2 §§15-17, 59`; `07 V2 §10`; `10 V2 §§15, 36`; `11 V2 §16`; `12 V2 §28`.

## Décision

**Option A préconisée pour M0 sous preuve de CAS/verrou ; PROPOSED**. À soumettre à l'autorité humaine avec les limites de concurrence explicitement acceptées.