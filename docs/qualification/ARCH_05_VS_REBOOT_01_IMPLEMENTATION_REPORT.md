# ARCH-05 - Qualification du noyau `VS-REBOOT-01`

> Date 2026-11-05 | Baseline de départ `dd8ec1c945ece80362f2c009ad56493fa855825f` | Implémentation additive `pyprojectkit_next` | `M1/M2=DEFER`.

## Ce qui existe réellement

- Domaine `Project`, `Task`, `Milestone`, graphe de dépendances acyclique et Value Objects ; IDs `str` avec bridge UUID explicite.
- Ports `Clock`, `IdFactory`, `AuthorizationPolicy`, `UnitOfWork` et adaptateur transactionnel mono-processus InMemory.
- Commands/Queries Project/Task, tests de refus, CAS, rollback et événements post-commit.
- Correction de non-divulgation : classe/message `NotFound("ressource indisponible")` homogènes pour les lectures sur objet caché versus absent ; tests existants modifiés et nouveaux cas négatifs ajoutés.
- Fixture de cinq oracles exécutables, test différentiel legacy M0 à exécuter en CI et test d'architecture AST.

## Critères RB-AC-01..10

| ID | Résultat candidat | Tests | Limite |
|---|---|---|---|
| `RB-AC-01` | `PASS_SCOPED` | `test_create_and_read_project ; test_arch03_synthetic_oracles[O03-01]` | Création DRAFT sans tâche, owner/scope |
| `RB-AC-02` | `PASS_SCOPED` | `test_closure_refuses_open_task_and_does_not_emit_event ; test_project_closure_policy_blocks_open_task_without_mutating_version_or_events` | Clôture invalide sans écriture |
| `RB-AC-03` | `PASS_SCOPED` | `test_task_happy_path_and_project_closure ; test_review_return_to_work_preserves_progress_and_start` | Cycle Task et données cohérentes |
| `RB-AC-04` | `PASS_SCOPED` | `test_ac004_ac005_ordered_prerequisites_and_atomic_cycle_guard` | Cycle refusé sans mutation |
| `RB-AC-05` | `PASS_SCOPED` | `test_uow_rollback_isolation_and_atomicity` | Rollback atomique InMemory |
| `RB-AC-06` | `PASS_SCOPED` | `test_concurrent_assignment_and_progress_conflict_without_partial_write` | Conflits optimistes |
| `RB-AC-07` | `PARTIAL` | `test_sec_rb_02_03_04_project_absent_and_invisible_use_identical_public_error ; test_sec_rb_12_authorized_list_invariant_under_hidden_projects_and_tasks` | AuthN host et classification PRIVATE absents |
| `RB-AC-08` | `PASS_SCOPED` | `test_rb_ac_08_same_clock_and_ids_same_synthetic_outcome` | IDs/clock fixes |
| `RB-AC-09` | `PASS_IF_GITHUB_GREEN` | `Workflow reboot-vs01 sur Python 3.12/3.13 ; wheel isolée ; import fitness` | Preuve post-CI au SHA exact nécessaire |
| `RB-AC-10` | `PREPARED` | `Matrice PAR, index oracles, dossier G2, manifest de preuves` | Revue indépendante et G2 humain en attente |

## Scénarios SEC-RB-01..12

| ID | Statut candidat | Test discriminant | Réserve |
|---|---|---|---|
| `SEC-RB-01` | `PARTIAL` | `test_sec_rb_01_untrusted_actor_is_not_authenticated_by_this_kernel` | Démontre que forgery est possible si host non fiable ; aucun AuthN |
| `SEC-RB-02` | `PASS_SCOPED` | `test_sec_rb_02_03_04_project_absent_and_invisible_use_identical_public_error` | Cross-scope neutre pour ressources |
| `SEC-RB-03` | `PASS_SCOPED` | `test_sec_rb_03_04_task_absent_and_invisible_use_identical_public_error` | Autre owner : NotFound homogène |
| `SEC-RB-04` | `PARTIAL` | `test_sec_rb_02_03_04_project_absent_and_invisible_use_identical_public_error` | Scope PRIVATE simulable, pas de classification PRIVATE M1 |
| `SEC-RB-05` | `PASS_SCOPED` | `test_uow_rollback_isolation_and_atomicity` | Échec pré-commit sans événement |
| `SEC-RB-06` | `PASS_SCOPED` | `test_sec_rb_06_double_commit_is_explicitly_rejected_without_duplicate_event` | Second commit refusé |
| `SEC-RB-07` | `PASS_SCOPED` | `test_uow_optimistic_conflict_preserves_state_and_events` | CAS et course close/create |
| `SEC-RB-08` | `PASS_SCOPED` | `test_sec_rb_08_cross_scope_dependency_has_no_existence_or_count_oracle` | Graphe inter-projets et ressources cachées |
| `SEC-RB-09` | `PASS_SCOPED` | `test_sec_rb_09_external_instructions_are_opaque_domain_data` | Titre opaque non interprété |
| `SEC-RB-10` | `PARTIAL` | `test_sec_rb_05_10_event_buffer_stays_private_on_failed_commit` | Mutation directe via port sans event encore autorisée : pas de preuve de correspondance 1:1 |
| `SEC-RB-11` | `PASS_SCOPED` | `test_sec_rb_11_invalid_timestamp_and_ids_are_value_errors` | Validation domaine |
| `SEC-RB-12` | `PARTIAL` | `test_sec_rb_12_authorized_list_invariant_under_hidden_projects_and_tasks` | Liste filtrée ; count/page/facets non implémentés avant ARCH-06 |

## Mesures et sémantiques

- Exécution locale isolée (sans le package historique) : **106 PASS, 1 SKIP**, ce SKIP est le test différentiel M0 faute de legacy dans le dossier local. **Ne pas revendiquer 107 PASS sur le seul résultat local.**
- La CI intégrée du dépôt doit exécuter **ce test différentiel** en plus de toutes les suites, au nouveau SHA GitHub.
- Déterminisme : horloge injectée et IDs séquentiels, sans prétention à l'idempotence distribuée.
- Une mutation manuelle via UoW sans événement est actuellement possible : l'API de use case enregistre les événements, mais le port UoW n'impose pas une cardinalité un événement par write. `SEC-RB-10` reste partiel.
- Authentification : `ActorContext` est un DTO constructible par tout appelant ; le vrai bridge d'identité vérifiée est de responsabilité host, **non livré**.
- SQLite durable, outbox, commit ambigu, migrations et restauration ne sont pas qualifiés par Memory ; voir ARCH-06.

**Recommandation technique :** `CONDITIONAL_TECHNICAL_READY_FOR_G2_REVIEW`, pas un GO humain. Après CI, joindre manifeste de SHA/jobs et reviewer réellement identifié.
