# R0-07 - Traçabilité AC-001..AC-012 vers tests M0

> Statut : TEST_PLAN_PROPOSED / NOT_EXECUTED
>
> Source des AC : `00_PYPROJECTKIT_REQUIREMENTS_ANALYSIS_V2.md` §34. WorkItems : roadmap 13 §§8 et 15. Aucune preuve d'exécution n'est déclarée.

| AC | Scénario conforme aux exigences V2 | Use case / invariant / contrat | WorkItem | Preuve à produire |
|---|---|---|---|---|
| AC-001 | Import + création de Project sans framework web ni réseau | `AUC-M0-P01`, `INV-PROJ-001..003` | M0-01/05 | `test_create_project_without_network`, import propre |
| AC-002 | Refus d'une transition Project invalide | `AUC-M0-P02/P03/P07`, `BR-PROJ-001..005` | M0-05 | `test_project_invalid_transition_is_atomic` |
| AC-003 | Créer, affecter, démarrer, bloquer, débloquer et terminer Task | `AUC-M0-T01..T08`, `INV-TASK-001..009`, `BR-TASK-DONE-*` | M0-06/07 | `test_task_lifecycle_complete` |
| AC-004 | Refuser démarrage si prédécesseur obligatoire non DONE | `AUC-M0-T04`, `BR-DEP-002`, `BR-TASK-START-002` | M0-09 | `test_blocking_dependency_prevents_start` |
| AC-005 | Refuser cycle du graphe A->B->C->A | `AUC-M0-D01`, `INV-DEP-001/003`, `APP-DEP-002` | M0-09/13 | `test_dependency_cycle_rejected_unchanged` ; concurrence à qualifier séparément |
| AC-006 | Créer et atteindre un jalon, avec dates valides | `AUC-M0-M01/M02`, `INV-MILE-001..004` | M0-08 | `test_milestone_dates_and_reach` |
| AC-007 | Temps et IDs déterministes | `Clock/FixedClock/IDFactory` | M0-02 | `test_fixed_clock_and_injected_ids` |
| AC-008 | Repository in-memory contract sans ORM | `CT-10-M0-01/02/03/04/05/07/08` | M0-10/11 | Repository roundtrip, rollback et test multi-repository |
| AC-009 | Événements uniquement après mutation et commit réussis | `TaskCompleted`, `ProjectCreated`, 09 V2 §8, `CT-10-M0-10` | M0-14/15 | `test_no_success_event_on_failed_commit` |
| AC-010 | Pas de dépendance du core à FastAPI/Django/SQLAlchemy/Pythos/PyAgentsKit | `PORT-001/012`, architecture fitness | M0-03/16 | `test_no_forbidden_core_imports` |
| AC-011 | Typage des exemples de l'API documentée | Exemples importables, contrat API M0 | M0-17 | `mypy` sur exemples et import smoke |
| AC-012 | Tests reproductibles en environnement isolé | CI + dépendances documentées | M0-16/18 | SHA + environnement + commandes + résultats |

## Contrôles transversaux indispensables (hors numérotation AC)

| Référence locale | Justification documentaire | Scénario |
|---|---|---|
| SEC-M0-01..06 | 12 V2 §4 ; 10 V2 `CT-10-M0-12` | Autorisation, scope, non-divulgation et logs minimisés |
| UOW-M0-01 | 10 V2 §17 ; 11 V2 §17 | Rollback sur exception et sans commit, pas de fuite mutationnelle |
| UOW-M0-02 | 11 V2 §17 | `CommitOutcomeUnknown` sans faux succès ni retry aveugle (simulation/contrat) |
| CON-M0-01 | 07 V2 `APP-DEP-001` ; 10 V2 §15 | Garantie de concurrence limitée explicitement et testée si revendiquée |
| DOC-M0-01 | 13 V2 §17 ; 14 §24.3 | Aucun PASS attribué sans preuve sur SHA qualifié |

## Dossier d'exécution attendu au gate Q-M0

- commit SHA exact et état de branche ;
- version et plateforme Python, dépendances/outillage réellement utilisés ;
- commandes lint / type checking / tests / build / import et résultats ;
- table `AC-001..012` avec statut `PASS/FAIL/NOT_ASSESSED` ;
- scénarios négatifs UoW, droits, graphes et états ;
- limites de concurrence et d'effets externes ;
- approbation humaine ou réserves, plus le handoff.

## Statut actuel

**Aucun test de ce tableau n'a été exécuté**, car M0 n'est pas démarré. Les noms des tests sont candidats et peuvent être ajustés sans renuméroter les AC normatifs.
