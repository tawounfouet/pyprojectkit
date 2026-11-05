# ARCH-03 - Contrat d'acceptation exécutable VS-REBOOT-01

> Sources : plan ARCH-03..05 fourni, rubrique 5.7 (`RB-AC-01..10`) ; V2 `00`, `07`, `10`, `11`, `12`.

## RB-AC - Index de preuve

| ID | Invariant vérifiable | Tests directs au nouveau SHA | Qualification indicative |
|---|---|---|---|
| `RB-AC-01` | Projet DRAFT, owner/scope ; aucun Task requis | `test_create_and_read_project`, `test_arch03_synthetic_oracles[O03-01]` | `SCOPED_PASS` |
| `RB-AC-02` | Clôture invalide sans mutation | `test_closure_refuses_open_task_and_does_not_emit_event`, `test_project_closure_policy_blocks_open_task_without_mutating_version_or_events` | `SCOPED_PASS` |
| `RB-AC-03` | Cycle Task et dates/events | `test_task_happy_path_and_project_closure`, `test_block_unblock_preserves_no_stale_reason`, `test_review_return_to_work_preserves_progress_and_start` | `SCOPED_PASS` |
| `RB-AC-04` | Graphe acyclique / refus de cycles | `test_ac004_ac005_ordered_prerequisites_and_atomic_cycle_guard`, `test_graph_uow_conflict_cannot_create_concurrent_cycle` | `SCOPED_PASS` |
| `RB-AC-05` | Rollback inter-agrégats sans événement | `test_uow_rollback_isolation_and_atomicity`, `test_graph_milestone_transaction_rollback_and_events_atomic` | `SCOPED_PASS` |
| `RB-AC-06` | Concurrence CAS sans lost update | `test_uow_optimistic_conflict_preserves_state_and_events`, `test_concurrent_assignment_and_progress_conflict_without_partial_write` | `SCOPED_PASS` |
| `RB-AC-07` | Owner/scope, query/command sans fuite | `test_sec_rb_02_03_04_project_absent_and_invisible_use_identical_public_error`, `test_sec_rb_03_04_task_absent_and_invisible_use_identical_public_error`, `test_sec_rb_12_authorized_list_invariant_under_hidden_projects_and_tasks` | `PARTIAL` : identité hôte non vérifiée et PRIVATE non implémenté |
| `RB-AC-08` | Clock et IDs déterministes | `test_rb_ac_08_same_clock_and_ids_same_synthetic_outcome`, `test_arch03_synthetic_oracles[O03-16]` | `SCOPED_PASS` |
| `RB-AC-09` | Wheel et import indépendants | CI dédiée VS01, smoke wheel, `mypy --strict`, `test_arch04_domain_and_application_import_fitness` | `PASS` sur SHA GitHub vert uniquement |
| `RB-AC-10` | Rapport complet, statut honnête, SHA et gate séparé | `G2_NUCLEUS_DECISION_DOSSIER.md`, manifests et rapport de CI | `PREPARED`, approbation humaine `PENDING` |

## Catégories d'oracles

Fichiers livrés : `tests/fixtures/synthetic/g2_acceptance_cases.json` (schema, 5 scénarios, classification `SYNTHETIC_ONLY`), `tests/test_reboot_g2_fixtures.py` (pilotage), `tests/test_reboot_g2_security_contract.py` (non-divulgation et défaillances).

Les tests sont réels sur le package expérimental et ne prennent **jamais** des résultats issus de la CI legacy comme preuve du nouveau code. L'hôte fiable, `PRIVATE` métier et les données réelles sont exclus de cette preuve limitée.
