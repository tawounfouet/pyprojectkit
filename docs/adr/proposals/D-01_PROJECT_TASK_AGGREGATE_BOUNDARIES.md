# D-01 - Frontières des agrégats Project et Task

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-01`, `ADR-06-001`, `ADR-07-002`. Ce fichier est un *dossier candidat*, pas un ADR historique accepté.

## Problème et exigences

Le noyau M0 doit permettre de créer, modifier et retrouver des projets et leurs tâches, sans devoir charger toutes les tâches pour une simple mutation du projet. Les règles de clôture ou de démarrage peuvent toutefois dépendre de plusieurs agrégats. La conformité doit porter sur des invariants métier, pas sur le placement des tables SQL.

## Options

**A - RECOMMANDEE :** deux Aggregate Roots `Project` et `Task` identifiés respectivement par `ProjectId` et `TaskId`; `Task.project_id` est une référence. `Milestone` reste dans `Project` (voir D-02). Les règles inter-AR vivent à la frontière Application/UnitOfWork.

**B :** un seul `Project` Aggregate englobant toutes les tâches. Inconvénients : lecture profonde, contention, mutation partielle difficile à maîtriser et croissance incontrôlée.

**C :** entité `WorkItem` générique racine avec spécialisation `Task`. Non justifiée par le premier cas M0 ; risque d'abstraction prématurée. `WorkItem` demeure un terme de langage commun.

## Contrat de conception proposé

- Une `Task` conserve sa propre identité et son propre `EntityVersion`. Son titre n'est ni une clé ni une preuve de qualification.
- `CreateTask` résout un Project visible, autorisé et en état admissible avant mutation.
- `CompleteProject` évalue une politique de clôture explicite : les jalons internes peuvent être vérifiés localement ; les autres Tasks et ressources exigent lecture/transaction adaptées, sans supposer une vue externe atomique.
- Une Task ne change pas d'état au seul motif qu'un rapport Pythos est reçu.
- Aucune classe `WorkItem` / `Subtask` séparée n'est imposée au M0 sans cas métier.
- Adapter in-memory et éventuel adapter durable doivent partager les garanties d'atomicité qu'ils annoncent.

## Scénarios obligatoires avant Q-M0

1. `CreateProject` sans tâche puis `CreateTask` sous Project valide : deux identités stables et deux stores séparés.
2. Création d'une Task dans un projet inexistant/invisible : refus sans mutation ni fuite d'identité.
3. Changement de version Task obsolète : conflit explicite, pas de lost update.
4. Clôture d'un projet avec tâche bloquante, selon policy retenue : refus atomique.
5. Import du domaine sans ORM, FastAPI, Django, Pythos ou réseau.

## Compromis et limites

Deux AR simplifient les opérations locales, mais ne rendent pas automatiquement atomiques les invariants inter-AR. Une transaction cohérente ou une policy de contrôle et version communes est nécessaire lorsque la contrainte est revendiquée. La qualification de package reste distincte de `TaskStatus.DONE`.

## Sources / frontières documentaires

`05 V2 §§8-9, 14-16`; `06 V2 §§11-13, 20`; `07 V2 §§8-10, 14`; `08 V2 §§9-11`; `10 V2 §§10-12, 17`; `12 V2 §§13-17`.

## Décision et suite

| Champ | Valeur |
|---|---|
| Option proposée | A |
| Approbation humaine | PENDING |
| Validité / version | À décider dans Q-R0 |
| Implémentation | NOT_STARTED |
| Evidence | Critères ci-dessus, tests non exécutés |

**Condition de promotion :** approbation humaine référencée + alignement baseline, puis tests sur SHA lors de M0.