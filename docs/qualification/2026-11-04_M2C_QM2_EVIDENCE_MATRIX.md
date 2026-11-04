# Q-M2 - Matrice des 11 critères d'acceptation (M2-C, pilote local synthétique)

> **Date** : 4 novembre 2026  
> **Plan source** : `21_PYPROJECTKIT_M2C_IMPLEMENTATION_PLAN.md`  
> **Code et tests qualifiés** : `301ba8f73de903fcf0f70e541a363935163f04ce`  
> **CI de référence** : [GitHub Actions #199](https://github.com/tawounfouet/pyprojectkit/actions/runs/41913081827)  
> **Pythons** : 3.12 job `126865466590`, 3.13 job `126865466792`  
> **Résultats vérifiés** : 168 tests PASS sur chaque Python, `mypy --strict` PASS (24 source files comptés par le job), deux pilotes, reprise interprocessus, wheel isolée PASS.  
> **Human gate** : PENDING ; **Adoption** : NOT_GRANTED. Aucune fusion, publication ou release.
>
> Note de vérité : les résultats sont ceux des tests du **pilote synthétique**. Aucune preuve n'est produite pour le vrai PySRMKit, une CI distante ou un Pythos réel. Les status PASS ci-dessous sont bornés aux tests locaux et ne sont **pas** des approvals Q-M2.

## Sources exactes des fixtures Git

| Python | SHA commit local synthétique | SHA tree | Working tree |
|---|---|---|---|
| 3.12 | `116555b73884336db206fc19f84afe6ab2e9e8f7` | `7cb7404575dbfcf338064f83091594d2c37b0e5e` | CLEAN |
| 3.13 | `4e72ea59cbedcdb0fd6917095c5ea8f843fa74b4` | `7cb7404575dbfcf338064f83091594d2c37b0e5e` | CLEAN |

Les SHA de commit diffèrent entre jobs en raison de l'horodatage du commit local ; les arbres Git des fixtures sont identiques. Ils ne sont pas les SHA du véritable dépôt PySRMKit.

## Matrice par critère

| ID | Statut pilote | Scénarios CI probants | Réserve |
|---|---|---|---|
| AC-027 | PASS_SYNTHETIC | `test_m2a::test_18_end_to_end_authorized_brief`, `test_m2c_pilots::test_p1_audit_001_local_git_sha_and_tree_unchanged` | Brief limité aux projets INTERNAL, pas de Pythos réel |
| AC-028 | PASS_SYNTHETIC | `test_m2b::test_m2b_05_report_is_declared_with_atomic_m1_links`, `test_m2c_pilots::test_p1_audit_001_local_git_sha_and_tree_unchanged` | Report du fake, non preuve d'exécution distante |
| AC-029 | PASS_SYNTHETIC | `test_m2c_security_b::test_sec_16_qualified_declaration_does_not_change_m0_m1`, `test_sec_17_fake_verifier_pass_does_not_create_m1_pass` | Vérificateur source synthétique |
| AC-030 | PASS_SYNTHETIC | `test_m2c_pilots::test_p1_audit_001_local_git_sha_and_tree_unchanged`, `test_sec_20_prompt_injection_is_data_not_instruction` | Pas d'outils externes d'écriture |
| AC-031 | PARTIAL | `test_sec_06_unauthorized_a4_or_a5_mandate_rejected`, `test_sec_07_no_merge_publish_delete_tool_exposed`, `test_sec_08_no_project_priority_command_on_m2_boundary` | **NOT_APPLICABLE_NO_TOOL** : aucune surface réelle merge/publish/delete/priority à évaluer |
| AC-032 | PASS_SYNTHETIC | `test_sec_03_cross_scope_is_fail_closed`, `test_sec_10_wrong_task_or_exact_revision_denied`, `test_sec_15_fake_actor_and_credential_not_authorized` | Refus sur les commandes réellement exposées uniquement |
| AC-033 | PASS_SYNTHETIC | `test_m2b::test_m2b_06_retries_and_idempotency_collisions`, `test_sec_12_many_identical_retries_one_intention`, `test_sec_14_lost_ack_reconciles_without_second_report`, `test_res_10_replayed_report_is_single_logical_intention` | Idempotence locale SQLite, pas exactly-once distribué |
| AC-034 | PARTIAL | `test_sec_25_agent_requester_cannot_self_approve`, `test_sec_26_one_human_request_one_decision`, `test_qm2_02_pass_eleven_is_not_human_go` | Gate Q-M2/G5/overlay réellement approuvé non démontré, décision humaine en attente |
| AC-035 | PASS_SYNTHETIC | `test_sec_03_cross_scope_is_fail_closed`, `test_sec_04_other_owner_same_scope_cannot_list_report`, `test_sec_05_private_scope_is_not_delegated_even_with_read_private`, `test_sec_21_list_count_export_protected_without_size_leak` | Exclusion explicite PRIVATE, pas de contexte externe réel |
| AC-036 | PASS_SYNTHETIC | `test_res_01_02_new_process_rehydrates_without_mandate_memory`, `test_res_04_missing_snapshot_is_not_invented`, `test_res_05_stale_snapshot_after_explicit_task_update`, `test_res_12_repeat_query_is_deterministic_and_read_only` | Identité du nouveau processus toujours host-side ; snapshot M1 project-level |
| AC-037 | PASS_SYNTHETIC | `test_p2_edu_001_no_software_gate_or_package_requirements`, `test_p2_n01_n02_no_forced_release_or_qualified_business_state`, `test_res_12_repeat_query_is_deterministic_and_read_only` | Pilote pédagogique fictif |

## Bilan et interprétation

| Champ | Valeur |
|---|---|
| `assessed_count` | 11/11, avec réserves explicites |
| `passed_count` | 9 (dans le périmètre synthétique local uniquement) |
| `partial_count` | 2 : AC-031 et AC-034 |
| `failed_count` | 0 |
| `unassessed_count` | 0 (chaque AC possède un résultat ou une limitation) |
| `technical_status` | PILOTS_AND_REGRESSIONS_CI_PASS, **Q-M2_INCOMPLETE** |
| `technical_recommendation` | NO_GO_RECOMMENDED pour l'adoption globale non bornée ; revue humaine des deux réserves |
| `human_gate` | PENDING |
| `adoption_decision` | NOT_GRANTED |

La fonction `build_qualification_dossier` traite un AC de sécurité `PARTIAL` comme bloquant le GO automatique et maintient toujours l'autorité de gate hors du moteur de calcul.

## Vérifications restantes pour un vrai GO

1. Faire approuver ou amender les ADR-M2-01 à ADR-M2-08.
2. Obtenir l'avis indépendant d'un reviewer humain, avec date, périmètre, risques acceptés et preuve signée/consignée.
3. Décider si AC-031 peut être considéré hors périmètre d'un GO *strictement local synthétique*, ou si un outil réel doit être introduit sous mandat séparé.
4. Prouver séparément toute éventuelle intégration Pythos réelle et des sources CI/GitHub réelles.
5. Requalifier les PR #16 puis #17 puis #18 sur les commits résultants si une décision humaine autorise leur fusion.

**La création de ce manifeste ne signe aucune décision Q-M2.**
