# R0-03 - Glossaire minimal et mapping M0

> Statut : PROPOSED / REVIEW | Ne remplace pas les spécifications 04 à 12 V2.
>
> But : fixer un langage *candidat* suffisamment précis pour rédiger M0 sans créer des agrégats ou interfaces concurrents.

## Concepts et propriétaires

| Terme | Sens proposé | Ownership / frontière | À ne pas confondre |
|---|---|---|---|
| `Project` | Initiative pilotée, identité et cycle métier | AR M0 `Project` | Dépôt Git, `PortfolioDecision` |
| `Task` | Unité de travail avec identité, statut et `ProjectId` | AR M0 `Task` | `WorkItem` universel obligatoire |
| `WorkItem` | Langage commun de travail, notamment Pythos | Concept, pas AR M0 | Deuxième `Task` |
| `ActionItem` | Action issue d'une décision/revue | Concept M1/C3 selon cas | Transition implicite de Task |
| `NextAction` | Recommandation de reprise | Projection M1, potentiellement datée | Une Task créée automatiquement |
| `Milestone` | Jalon daté du Project, éventuellement obligatoire | Entity au sein de `Project` M0 | AR Milestone sans besoin |
| `Dependency` | Lien orienté prédécesseur -> successeur | VO / lien contrôlé, application + graphe | Graphe de parenté des sous-tâches |
| `DependencyGraph` | Contrôle des cycles, sur snapshot fiable | Domain Service, port applicatif de stockage | Repository canonique des tâches |
| `ProjectRegistryEntry` | Vue d'index projet | Read Model M1 | Second Aggregate Project |
| `EvidenceRef` | Référence contextualisée à une preuve | VO M1 | Verdict `VERIFIED` automatique |
| `Observation` | Ce qui a été constaté à un instant | Historical Record M1 | Source d'autorité universelle |
| `VerificationAssessment` | Évaluation d'une affirmation | Historical Record M1 | `Approval` |
| `ProjectSnapshot` | Photographie datée, éventuellement partielle | Historical Read Model M1 | État courant autoritatif |
| `OperatingBriefDTO` | Entrée bornée par mandat Pythos | Adapter M2 | Entité du domaine |
| `ExecutionReportDTO` | Rapport de contribution Pythos | Adapter M2 | Mutation approuvée |

## Axes d'état séparés

- `ProjectStatus` : `DRAFT / PLANNED / ACTIVE / ON_HOLD / COMPLETED / CANCELLED`. Règles candidates 05 §8 et 07 §8.
- `TaskStatus` : `TODO / READY / IN_PROGRESS / BLOCKED / IN_REVIEW / DONE / CANCELLED`. Règles candidates 05 §9 et 07 §9.
- `WorkItemStatus` du modèle opératoire Pythos : workflow de *travail agentique* ; **n'est pas** universellement `TaskStatus`.
- Statut probant Py*Kit : `CONCEPTUAL / SPECIFIED / IMPLEMENTED / TESTED / QUALIFIED / PUBLISHED / OPERATED` ; distinct du statut métier.
- Évaluation d'une affirmation : `UNKNOWN / DECLARED / OBSERVED / VERIFIED` (candidats M1) ; pas une preuve d'approbation.
- `PortfolioDecision` : `KEEP / MERGE / PARK / RETIRE` ; `PARK` n'est pas `ProjectStatus.ON_HOLD`.
- `Approval` : décision par une autorité habilitée ; distincte de `VerificationAssessment`.

## Noms publics à arbitrer

| Intention métier | Variante trouvée | Candidate canonique | Source |
|---|---|---|---|
| Suspendre projet | `PauseProject`, `PutProjectOnHold` | `PutProjectOnHold` | 07 §8.2 / 08 §11.4 / 09 §10 |
| Fait de suspension | `ProjectPaused`, `ProjectPutOnHold` | `ProjectPutOnHold` | 08 §11.4 / 09 §10 |
| Rendre tâche prête | `MarkTaskReady` | `MarkTaskReady` | 08 §11.7 |
| Fait de préparation | `TaskReadied`, `TaskMarkedReady` | `TaskMarkedReady` | 08 §11.7 / 09 §11 |
| Date de jalon | `target_date`, `due_at?` dans payload candidat | `target_date` obligatoire pour l'entité M0 ; payload à préciser | 07 §11 / 09 §13 |

Les valeurs « Candidate canonique » sont **des orientations à soumettre**, pas des API publiées ni un changement adopté.

## Règles temporelles proposées

- `Instant` : horodatage timezone-aware, origine de `Clock` injectable et conservée.
- `DateRange` : bornes comparables, ordre valide, inclusivité explicitée par le contrat.
- `planned_*` : intention de calendrier ; `actual_*` : date métier de transition accomplie.
- `observed_at`, `recorded_at`, `verified_at`, `captured_at` ne sont pas synonymes (M1).
- `reached_at` pour Milestone atteint, absent si non atteint.
- `EntityVersion` : révision de l'agrégat ; `graph_version` ou jeton commun protège les mutations de liens, si la politique de concurrence le décide.

## Identités et sécurité

- `ProjectId`, `TaskId`, `MilestoneId` sont distincts et immuables.
- `ActorId` ne se déduit ni d'un nom d'utilisateur dans un rapport ni d'une adresse email.
- `ProjectId` n'est pas `ContextScope`, et `ContextScope` n'est ni une permission ni un tenant.
- `Task.project_id` est une référence, non un Aggregate `Project` embarqué.
- Toute projection sensible est autorisée et filtrée avant d'être retournée.

## Validation attendue

- [ ] Approbation du langage M0 et des alias historiques éventuels.
- [ ] Vérification des identifiants d'exception, de Command et d'Event des documents 08, 09 et 11.
- [ ] Pas de second Aggregate `WorkItem` sans cas métier démontré.
- [ ] Alignement des futures signatures M0, tests et documentation.

Références : 04 §§5-10, 79 ; 05 §§8-11 ; 07 §§8-11 ; 08 §§9-12 ; 09 §§10-13 ; 12 §§9-17.
