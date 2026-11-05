# ARCH-03 - Revue de contrat de parité et oracles

> Nature : revue technique de Pythos, **non indépendante**, sans signature humaine ; G1 non démontré.

## Exécution réalisée

- Baseline Git M0/M1/M2 indexée à `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`.
- Onze familles `PAR-00..10` classées, écarts d'API explicites, M1/M2 différés.
- Exécuteur de cinq fixtures synthétiques (O03-01/02/03/12/16) ; tests de security semantics sur les cas non-divulgation.
- Comparaison différentielle réelle M0 versus VS01 dans `tests/test_reboot_vs01_contract.py::test_differential_core_scenario_against_legacy_m0` **exécutée en CI du dépôt**, sautée uniquement dans le dossier local isolé sans package legacy.

## Oracles O03-01..18

| ID | Observable | Statut ciblé | Référence de test / réserve |
|---|---|---|---|
| O03-01 | Projet DRAFT sans tâche | `COVERED` | `g2_acceptance_cases.json`, `test_create_and_read_project` |
| O03-02 | Cycle DRAFT->PLANNED->ACTIVE | `COVERED` | Fixture, `test_project_lifecycle_pause_resume_keeps_original_start` |
| O03-03 | Transition terminale interdite | `COVERED` | Fixture, `test_invalid_project_transition_does_not_write` |
| O03-04 | Clôture policy / tâche ouverte | `COVERED` | `test_closure_refuses_open_task_and_does_not_emit_event` |
| O03-05 | BLOCKED/UNBLOCKED / DONE | `COVERED` | `test_block_unblock_preserves_no_stale_reason` |
| O03-06 | BLOCKED->DONE direct refusé | `COVERED` | `test_task_happy_path_and_project_closure` + `test_reboot_vs01_parity.py` |
| O03-07 | Cycle graphe interdit | `COVERED` | `test_ac004_ac005_ordered_prerequisites_and_atomic_cycle_guard` |
| O03-08 | Graphe inter-projet rejeté | `COVERED` | `test_cross_project_and_scope_edges_rejected` |
| O03-09 | Deux écritures concurrentes | `COVERED` | `test_uow_optimistic_conflict_preserves_state_and_events` |
| O03-10 | Rollback sans événements | `COVERED` | `test_uow_rollback_isolation_and_atomicity` |
| O03-11 | Double commit rejeté | `COVERED` | `test_sec_rb_06_double_commit_is_explicitly_rejected_without_duplicate_event` |
| O03-12 | Hors owner/scope non divulgué | `COVERED_SCOPED` | Tests de refus uniformes ; AuthN host encore absent |
| O03-13 | PRIVATE M1 sans accès | `DEFERRED` | Aucun attribut de classification privé dédié dans VS01 |
| O03-14 | Count/page après filtrage | `PARTIAL` | Liste filtrée, ni pagination ni facettes disponibles |
| O03-15 | Payload actor/scope forgé | `PARTIAL` | Pas d'entrée réseau ; `ActorContext` constructible par l'appelant |
| O03-16 | Identité/temps déterministes | `COVERED` | Fixture, `test_rb_ac_08_same_clock_and_ids_same_synthetic_outcome` |
| O03-17 | Import headless et wheel | `COVERED_IF_CI_GREEN` | Workflow VS01, wheel smoke et fitness |
| O03-18 | Pythos/assessment non auto-PASS | `DEFERRED` | Aucune ingestion M2 dans VS01 |

## Désaccords/risques à arbitrer

1. L'API d'identités historiques est à base d'UUID, VS01 s'appuie sur des valeurs string et un bridge explicite.
2. Les étiquettes d'événements et la granularité de droits ne sont pas une reproduction API stricte.
3. Réponse unifiée `NotFound("ressource indisponible")` sur ressource absente/cachée dans le code VS01 (tests actualisés, comportement public expérimental modifié).
4. Un contexte d'acteur construit par un client non fiable **peut imiter** un propriétaire. Le test le met en évidence et ne valide pas une AuthN inexistante.
5. Le manque de G1 restaurable et de revue humaine empêche toute clôture formelle G2.

**Sortie ARCH-03 :** contrat de parité caractérisé, statut `TECHNICALLY_PREPARED_WITH_DECLARED_GAPS`, pas de `G2=GO`.
