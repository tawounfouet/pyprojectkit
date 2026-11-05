# ARCH-03 - Index des oracles historiques M0/M1/M2

> Date : 2026-11-05 | Nature : caractérisation, non autorisation de remplacement | Classification : données synthétiques.

## Baselines Git vérifiables

- Référence legacy historique : [`main@a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`](https://github.com/tawounfouet/pyprojectkit/commit/a523d9c61c30ef41afe3bc9cf0723beafe3c2d38). Le code historique M0, M1 et M2 est conservé sur `main` ; cela **ne constitue pas** un G1 ni une sauvegarde Git indépendante restaurée.
- Référence VS01 intégrée avant ce lot : [`main@dd8ec1c945ece80362f2c009ad56493fa855825f`](https://github.com/tawounfouet/pyprojectkit/commit/dd8ec1c945ece80362f2c009ad56493fa855825f) après les PR [#21](https://github.com/tawounfouet/pyprojectkit/pull/21), [#22](https://github.com/tawounfouet/pyprojectkit/pull/22) et [#23](https://github.com/tawounfouet/pyprojectkit/pull/23).
- CI VS01 au SHA de départ : [workflow complet 42098158719](https://github.com/tawounfouet/pyprojectkit/actions/runs/42098158719) (257 tests par Python 3.12/3.13), [workflow VS01 42098158836](https://github.com/tawounfouet/pyprojectkit/actions/runs/42098158836) (89 tests par version, wheel isolée et typage strict). Ces preuves portent **uniquement** sur dd8ec1c945ece80362f2c009ad56493fa855825f.
- Source de référence M0 : `src/pyprojectkit/domain.py`, `service.py`, `ports.py`, `memory.py` et `tests/test_m0.py` à `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`.
- Sources M1 : `src/pyprojectkit/m1/` et migrations `0001..0003` à la baseline ; sources M2 : `src/pyprojectkit/m2/`, tests `test_m2*.py` et qualification Q-M2 (toujours en attente).

## Méthode de comparaison

L'oracle historique est observable, pas normatif à lui seul. Pour chaque famille, comparer : exigences V2, code legacy au SHA historique, fixture synthétique, test du nouveau code à son propre SHA, et écarts documentés. Une divergence ne devient jamais un PASS en « harmonisant » un rapport.

| Famille | Oracle historique principal | Nouveau test / périmètre | Limite |
|---|---|---|---|
| `PAR-00` | `tests/test_m0.py::test_ac007_ids_clock_determinism` | `test_reboot_vs01_contract.py::test_uuid_boundary_roundtrip_and_explicit_rejections`, `test_reboot_g2_security_contract.py::test_rb_ac_08_same_clock_and_ids_same_synthetic_outcome` | Nouvel ID `str` avec passerelle UUID ; pas de compatibilité des signatures |
| `PAR-01` | `tests/test_m0.py::test_ac001_project_creation_without_tasks`, `::test_ac002_invalid_project_state_and_complete_policy` | `test_reboot_vs01.py`, test différentiel réel `test_differential_core_scenario_against_legacy_m0` | Sémantique commune seulement |
| `PAR-02` | `tests/test_m0.py::test_ac003_lifecycle_assign_block_unblock_review_and_done` | `test_reboot_vs01_task_semantics.py`, différentiel M0 | API, événements, versions différents |
| `PAR-03` | `tests/test_m0.py::test_ac004_ac005_dependency_guards_and_cycles` | `test_reboot_vs01_parity.py`, tests de conflit concurrent | Memory uniquement |
| `PAR-04` | `tests/test_m0.py::test_ac008_optimistic_conflict_preserves_global_state`, `::test_ac009_events_only_after_confirmed_commit` | `test_reboot_vs01.py`, `test_reboot_g2_security_contract.py` | Pas de SQLite ni de commit ambigu réel |
| `PAR-05` | `tests/test_m0.py::test_security_denies_commands_queries_and_scope`; M1 `security.py` | `test_reboot_g2_security_contract.py` | Owner + scope InMemory ; pas de rôle PRIVATE complet ni AuthN |
| `PAR-06` | M1 migrations et sauvegarde SQLite historiques | Aucun test de l'adapter SQLite reboot | `DEFERRED_ARCH06` |
| `PAR-07` | M1 claims/observations/provenance/assessments | Non implémenté | `DEFERRED` |
| `PAR-08` | M1 snapshots/handoffs | Non implémenté | `DEFERRED` |
| `PAR-09` | M2 mandat/rapport/inbox/TTL | Non implémenté | `DEFERRED` ; Q-M2 séparé |
| `PAR-10` | M3 ProjectHub, projet de read models | Non implémenté | `DEFERRED_ARCH07` |

## Intégrité et lacune G1

Aucun tag d'archive restauré, bundle indépendant restauré, coffre chiffré, manifeste de conservation ni responsable d'archive vérifié n'a été fourni dans ce périmètre. **G1 reste PENDING**. Les preuves CI et l'historique Git ne remplacent pas le test de restauration. L'index est utilisable en mode lecture/CI, sans déclencher ARCH-02.
