# ARCH-03 - Matrice de parité comportementale `PAR-00..10`

> Date : 2026-11-05 | Baseline legacy : `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38` | VS01 baseline : `dd8ec1c945ece80362f2c009ad56493fa855825f` | État : `TECHNICAL_QUALIFICATION_IN_PROGRESS`.

**Convention :** `PASS_SCOPED` est une réussite sur la surface explicitement démontrée, **pas** la parité intégrale M0/M1/M2. `PARTIAL` signifie qu'un comportement est prouvé mais qu'une sous-garantie reste absente. `DEFERRED` n'est ni un échec de test ni un PASS. Les résultats deviennent `PASS_AT_SHA` après exécution effective au nouveau SHA de la CI.

| ID | Oracle | Garanties | Statut candidat | Tests / preuves | Réserve |
|---|---|---|---|---|---|
| `PAR-00` | M0 | ProjectId/TaskId/MilestoneId, horloge, versions et exceptions | `PASS_SCOPED` | `tests/test_reboot_vs01_contract.py + tests/test_reboot_g2_security_contract.py` | Le format `str` diffère des UUID M0 ; conversion explicite ; toute compatibilité signature reste à valider. |
| `PAR-01` | M0 | Project DRAFT/PLANNED/ACTIVE/ON_HOLD/COMPLETED/CANCELLED, dates | `PARTIAL` | `tests/test_reboot_vs01.py + test_differential_core_scenario_against_legacy_m0` | La comparaison différentielle couvre un scénario commun, pas toute l API et les événements. |
| `PAR-02` | M0 | Task TODO/READY/IN_PROGRESS/BLOCKED/IN_REVIEW/DONE/CANCELLED, progression | `PARTIAL` | `tests/test_reboot_vs01_task_semantics.py` | Certaines signatures, la granularité AuthZ et les events diffèrent du legacy. |
| `PAR-03` | M0 | Dépendances acycliques, garde des prédécesseurs, conflit concurrent | `PASS_SCOPED` | `tests/test_reboot_vs01_parity.py` | Atomicité sur adapter InMemory uniquement. |
| `PAR-04` | M0/M1 | Repository, UoW, CAS, rollback, événements post-commit | `PARTIAL` | `tests/test_reboot_vs01.py + tests/test_reboot_g2_security_contract.py` | Pas de durabilité, outcome unknown ni outbox ; adapter Memory mono-processus. |
| `PAR-05` | M1 | Owner, scope, lecture non divulguante, PRIVATE, acteur vérifié | `PARTIAL` | `tests/test_reboot_g2_security_contract.py` | Erreur NotFound homogénéisée. Acteur forgé accepté si host non fiable ; modèle PRIVATE M1 non implémenté. |
| `PAR-06` | M1 | SQLite, migration, checksum, backup/restore | `DEFERRED_ARCH06` | `Aucun test VS01` | Les migrations historiques 0001..0003 restent inchangées. |
| `PAR-07` | M1 | Provenance, observations, assessments | `DEFERRED` | `Non implémenté` | Pas d autorité issue des sources externes. |
| `PAR-08` | M1 | Snapshots, handoffs, reprise | `DEFERRED` | `Non implémenté` | Un read model n est pas la reprise historique. |
| `PAR-09` | M2 | Mandats, TTL, inbox/report, absence auto-PASS | `DEFERRED` | `Non implémenté` | Q-M2 et AC-031/034 restent séparés. |
| `PAR-10` | M3 | Portfolio/WorkItemView et ProjectHub | `DEFERRED_ARCH07` | `Non implémenté` | Projet/famille non-tech sans gates logiciels obligatoires. |

## Correspondance aux arbitrages G0-04

- HD-05 : `M0=PRESERVE` signifie préserver le comportement **à qualifier** ; cela ne donne pas un droit de remplacer immédiatement les signatures `pyprojectkit.*`.
- HD-05 : `M1=DEFER`, `M2=DEFER` ; `PAR-06..09` restent hors VS01, avec des tests historiques toujours actifs.
- HD-06 : uniquement des fixtures synthétiques, aucune lecture/écriture de base réelle.
- HD-08 : reviewer indépendant reporté ; aucune revue fictive.
- HD-10 : `CONDITIONAL GO` stratégique, pas approbation de G2.

## Écarts visibles nécessitant ADR ou compatibilité

1. M0 expose des objets UUID (`ProjectId.value: UUID`) ; VS01 expose actuellement `ProjectId.value: str`, avec `from_uuid/to_uuid` explicites. **Pas de substitution transparente**.
2. Le legacy dispose de droits explicites (`PROJECT_VIEW`, `TASK_EDIT`, etc.) ; VS01 utilise `owner+scope` et des actions de granularité réduite. **RBAC externe non reproduit**.
3. Pour des ressources invisibles ou absentes, VS01 renvoie désormais `NotFound("ressource indisponible")`. C'est une correction de non-divulgation et un changement observable par rapport aux précédentes assertions de VS01. L'erreur `AccessDenied` reste pour la création ou une permission explicitement inconnue.
4. M0/M1 ont un modèle versionné, événements, projections et transactions différents. Le test différentiel mesure seulement un scénario commun et ne fait pas autorité sur les champs ou événements non comparés.
5. `PRIVATE` n'est pas une classification implémentée dans `Project` VS01 ; un scope nommé `PRIVATE` n'est pas une policy de visibilité M1.

**Verdict ARCH-03 :** matrice produite et étayée ; parité ciblée démontrable, **parité historique globale NON QUALIFIÉE**. `G1=PENDING` et `G2=PENDING`.
