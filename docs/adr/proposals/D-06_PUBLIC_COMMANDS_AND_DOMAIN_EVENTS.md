# D-06 - Langage public M0 et sémantique des Domain Events

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-04` (API), `ADR-PJ-RM-06` (événements), `ADR-PJ-10-07`, `ADR-APP-14`.

## Problème

Un même changement métier ne doit pas avoir plusieurs noms publics ou être déclaré réussi avant commit. Les commandes sont des intentions ; les Domain Events expriment des faits survenus. Le statut `Task.DONE` n'est pas la qualification du projet logiciel.

## Alternatives

**A - RECOMMANDEE :** API headless synchrone, noms publics canoniques issus du catalogue V1 préservé en V2, événements immuables collectés pendant une transition puis rendus observables **après** commit réussi.

**B :** maintenir simultanément `PauseProject` et `PutProjectOnHold`, `ProjectPaused` et `ProjectPutOnHold`, `TaskReadied` et `TaskMarkedReady` comme autant de contrats équivalents. Risque d'incohérence et de documentation double.

**C :** dispatcher les notifications avant commit puis compenser en cas d'échec. Risque de faux événements et d'effets extérieurs non réversibles ; non retenu comme contrat M0.

## Paires canoniques candidates

| Command | Domain Event | Réserve |
|---|---|---|
| `CreateProject` | `ProjectCreated` | Seulement après création confirmée |
| `PlanProject` | `ProjectPlanned` | Transition réelle |
| `StartProject` | `ProjectStarted` | Guards métier et autorisation |
| `PutProjectOnHold` | `ProjectPutOnHold` | Conserver noms V1, pas de second événement `ProjectPaused` |
| `ResumeProject` | `ProjectResumed` | Préconditions explicites |
| `MarkTaskReady` | `TaskMarkedReady` | Pas de doublon `TaskReadied` |
| `CompleteTask` | `TaskCompleted` | DONE != QUALIFIED |
| `AddTaskDependency` | `TaskDependencyAdded` | Lien dirigé ; project cohérent |
| `MarkMilestoneReached` | `MilestoneReached` | `Project` owner de l'Entity |

Le catalogue complet M0 inclut davantage d'événements ; ce tableau est un **sous-ensemble de validation des noms**, pas une réduction définitive des use cases de 08/09 V2.

## Contrat proposé

1. Chaque event décrit un fait métier et peut contenir `event_id`, type, `event_version`, aggregate ID/version, `occurred_at` injecté et payload minimal.
2. Les `PendingDomainEvents` sont des données temporaires internes ; aucun dispatch externe avant commit.
3. Après commit : dispatch local possible, **sans garantie durable de livraison** si crash entre commit et dispatch. Une Outbox devient nécessaire seulement si le besoin de livraison durable est approuvé.
4. Aucun événement de succès après refus d'autorisation, invariant violé, rollback ou commit connu comme échoué.
5. `CommitOutcomeUnknown` ne peut être présenté comme réussite, même si l'écriture a peut-être été validée.
6. Le contenu du payload et des logs est filtré ; pas de secret ni de copie intégrale de l'aggregate.
7. Un rapport agent Pythos, un audit et une projection ne deviennent pas des Domain Events autoritaires par simple import.

## Tests d'acceptation futurs

- `TaskCompleted` produit une occurrence seulement après commit confirmé.
- Exception après mutation en mémoire avant commit => aucun succès observable.
- Échec du dispatcher postcommit => état persistant confirmé, échec de dispatch distinct, aucune « annulation » fictive.
- `ProjectPutOnHold` et `TaskMarkedReady` correspondent aux noms stabilisés ; pas d'alias duplicatif non approuvé.
- Import du core sans framework web ni SDK d'agent.
- Les IDs d'événements et timestamps sont injectables et reproductibles.

## Sources

`07 V2 §8`; `08 V2 §§7, 9-11`; `09 V2 §§6-8, 10-15, 29-32`; `10 V2 §38`; `11 V2 §§17-18`.

## Décision

**Option A recommandée ; PROPOSED**, avec sous-décisions de nommage et d'enveloppe. Les API concrètes et le bus sont à tester, pas à présumer existants.
