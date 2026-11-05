# R3.1 - Contrat de non-régression M0/M1/M2

> Baseline : `main@a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`  
> Date : 2026-11-05  
> Statut : `REVIEW / CHARACTERIZATION_BASELINE`  
> Cet inventaire décrit les assertions à conserver pour les prochains travaux R3.2, M3-A et ProjectHub. Il ne constitue pas une exécution indépendante.

## 1. Matrice comportement / preuves

| Invariant ou contrat | Référence code | Tests de caractérisation | Résultat baseline |
|---|---|---|---|
| Projet autonome, états, clôture contrôlée | `domain.Project`, `ProjectService` | `tests/test_m0.py` : `test_ac001_project_creation_without_tasks`, `test_ac002_invalid_project_state_and_complete_policy` | CI PASS |
| Tâches : transitions, blocages, revue | `domain.Task` | `test_ac003_lifecycle_assign_block_unblock_review_and_done` | CI PASS |
| Graphe acyclique et contrôles de dépendance | `domain.Dependency`, `assert_acyclic` | `test_ac004_ac005_dependency_guards_and_cycles` | CI PASS |
| Identifiants et horloge injectables | `ports.IdFactory`, `Clock` | `test_ac007_ids_clock_determinism` | CI PASS |
| UoW transactionnelle, rollback et copies | `memory.InMemoryUnitOfWork` | `test_ac008_repository_copy_isolation_rollback_and_atomicity` | CI PASS |
| CAS et graphes concurrents | `memory.py`, `service.py` | `test_ac008_optimistic_conflict_preserves_global_state`, `test_ac008_graph_concurrent_writes_cannot_create_cycle` | CI PASS |
| Domain Events après commit confirmé | `UnitOfWork.record/commit` | `test_ac009_events_only_after_confirmed_commit` | CI PASS |
| Noyau importable sans adaptateur externe | `src/pyprojectkit/__init__.py` | `test_ac010_architecture_imports_without_infrastructure` + wheel smoke CI | CI PASS |
| Restriction de scope, droits et owner | `m1.security.TrustedHost`, `m1.service.RegistryService` | `tests/test_m1.py` et tests sécurité M2-C | CI PASS synthétique |
| SQLite : migrations, backup, historique | `m1/schema.py`, `m1/sqlite.py` | `tests/test_m1.py`, `tests/test_m2b.py` | CI PASS synthétique |
| Mandat, cible exacte, révocation | `m2/mandates.py`, `m2/application.py` | `tests/test_m2a.py` | CI PASS synthétique |
| Inbox et reports idempotents | `m2/inbox.py`, `m2/reports.py` | `tests/test_m2b.py`, `tests/test_m2c_security_*.py` | CI PASS synthétique |
| Réconciliation effet incertain | `CommitOutcomeUnknown`, inbox | `tests/test_m2b.py`, `tests/test_m2c_resume.py` | CI PASS synthétique |
| Reprise : missing/stale/provenance | `m2/resume_view.py` | `tests/test_m2c_resume.py` | CI PASS synthétique |
| Déclarations de l'agent non probantes | `m2/governance.py`, `m2/qualification.py` | `tests/test_m2c_security_a.py`, `tests/test_m2c_security_b.py` | CI PASS synthétique |
| Pilotes hétérogènes non mutationnels | `examples/m2c_pilots_demo.py` | `tests/test_m2c_pilots.py` | CI PASS synthétique |

`CI PASS` signifie uniquement que le job a réussi sur le SHA indiqué. Cette matrice n'affirme pas un test supplémentaire lancé durant R3.1 et n'exige pas que les tests portent exactement le même nom en cas de renommage futur : la garantie métier et la preuve restent obligatoires.

## 2. Prérequis au changement d'architecture

1. Geler les contrats publics exposés par `__init__.py` avant de déplacer des modules, ou adopter explicitement une politique de compatibilité.
2. Garder le schéma SQLite existant et les checksums des migrations 0001..0003.
3. Introduire des tests de contrat communs avant de déclarer deux adapters interchangeables.
4. Tester la confidentialité avant toute agrégation, pagination, count et export ProjectHub.
5. Préserver la séparation `ProjectStatus` / `TaskStatus` / assessments / preuve / approbation.
6. Ne pas étendre `WorkItemRef(kind="TASK")` sans ADR, version de contrat et migration de tests.
7. Maintenir l'absence de dépendance obligatoire au framework web, PostgreSQL ou runtime Pythos.
8. Conserver `AccessDenied`, `NotFound`, `Conflict`, `CommitOutcomeUnknown` avec leurs différences de sens.
9. Requalifier chaque nouveau SHA, pas recycler la preuve d'une CI sur un autre commit.
10. Garder toute publication ou déploiement sous un gate distinct des contrôles techniques.

## 3. Gate de contrôle de toute PR R3.x

| Check | Obligatoire ? | Mode |
|---|---|---|
| Python 3.12 / 3.13 pytest | Oui | CI |
| `mypy --strict` | Oui | CI |
| Wheel et import isolé | Oui | CI |
| Migrations/restauration si le schéma change | Oui, conditionnel | Tests dédiés |
| Contrats par adapter et mode d'échec | Oui, si ports modifiés | Tests nouveaux |
| Tests d'absence de divulgation | Oui, si Query modifiée | Tests négatifs |
| ADR et impacts API | Oui, si frontière modifiée | Revue humaine |
| Revue humaine et protection de branche | Oui pour intégration autorisée | GitHub + gate |
| Décision de release | Toujours séparée | Propriétaire habilité |

## 4. Baseline de vérification

- SHA : [a523d9c](https://github.com/tawounfouet/pyprojectkit/commit/a523d9c61c30ef41afe3bc9cf0723beafe3c2d38)
- CI : [run 41919258680](https://github.com/tawounfouet/pyprojectkit/actions/runs/41919258680)
- Jobs : `m1 (3.12)` et `m1 (3.13)`, nom historique des jobs malgré les tests M0-M2.
- 168 tests `PASS` par version, typecheck strict et wheel smoke `PASS`.
- 9 critères M2 `PASS_SYNTHETIC`, 2 `PARTIAL` (AC-031, AC-034). `Q-M2 HUMAN_PENDING`.

**Verdict :** `BASELINE_CHARACTERIZED` au SHA d'origine, mais `R3_1_GATE = REVIEW_REQUIRED` et `GOVERNANCE_NOT_CLOSED`.
