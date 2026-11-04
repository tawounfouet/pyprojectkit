# 20 - PyProjectKit - Rapport d'implémentation et qualification M2-B

> **Date** : 4 novembre 2026  
> **Tranche** : M2-B, M2-04 à M2-07  
> **Plan source** : `19_PYPROJECTKIT_M2B_IMPLEMENTATION_PLAN.md`  
> **Branche** : `feat/m2b-report-inbox`  
> **Base de travail** : `feat/m2a-authorized-brief`, PR #16 (draft, non fusionnée)  
> **PR M2-B** : [#17](https://github.com/tawounfouet/pyprojectkit/pull/17) (draft, non fusionnée)  
> **SHA du code et tests qualifiés** : `50c972d134b3a94c2a5df050acd2fc1a3d76822a`  
> **CI finale vérifiée après guide** : [run #160](https://github.com/tawounfouet/pyprojectkit/actions/runs/41887626111) sur `acc08b756b4f8f376ed729d43f5a4483b7335c91`  
> **Statut** : `IMPLEMENTED / TESTED / SYNTHETIC_LOCAL_TECHNICAL_PASS`  
> **Gate humain** : `PENDING` ; `Q-M2 = NOT_ASSESSED`.  
> **Aucune fusion, publication ou mise en production réalisée.**

## Résumé exécutif

Le chemin retour PyProjectKit M2-B est opérationnel en pilote **local synthétique**, sans runtime Pythos. Un brief émis par l'hôte est attesté dans SQLite avant livraison à l'adaptateur. Un `ExecutionReportDTO v1.0` est corrélé à l'émission, au mandat, au scope, au Project/Task et à la révision exacte. L'ingestion est atomique et idempotente. La consultation reste autorisée, et une interruption avant ou après commit est reprise sans double entrée. L'agent ne peut pas changer l'état métier à travers un report.

## WorkItems et éléments livrés

| WorkItem | Implémentation | Preuves |
|---|---|---|
| M2-04 | DTO v1, `ReportEvidenceRefDTO`, JSON strict, SHA-256 canonique, fixture | Schéma, round-trip, champs/dates/versions illégaux |
| M2-05 | `issue_brief`, table `m2_issued_briefs`, `receive`, inbox + liens history M1 | Émission réelle exigée, mandat, scope, owner, reçu `DECLARED` |
| M2-06 | `IndependentEvidenceVerifier`, `ReportGovernanceService`, demandes humaines et SoD | Fake indépendant, source indisponible `UNKNOWN`, demande `PENDING`, aucun PASS M1 automatique |
| M2-07 | Clé de retry + report ID par namespace, fingerprint, `reconcile` | Replay, collision, concurrence, crash injecté, commit inconnu, subprocess et backup |

## Preuves exactes d'exécution

**Run #160** : https://github.com/tawounfouet/pyprojectkit/actions/runs/41887626111

| Contrôle | Python 3.12 | Python 3.13 |
|---|---|---|
| Job CI | `126776240393` | `126776239846` |
| `pytest -q` | **105 tests PASS** | **105 tests PASS** |
| Baseline M0/M1/M2-A | 68 tests conservés | 68 tests conservés |
| Nouveaux tests M2-B | 37 tests | 37 tests |
| `mypy --strict` | PASS (21 fichiers source) | PASS (21 fichiers source) |
| `VS-M2-02` | PASS | PASS |
| `VS-M2-03` | PASS | PASS |
| Build wheel | PASS | PASS |
| Wheel isolée / import M2-B sans Pythos | PASS | PASS |

Le package conserve `pyprojectkit==0.2.0a1` sur la branche, sans publication. La présence des capacités M2-B ne prouve ni une version PyPI `0.3.0a0` ni une release.

## Contrôles majeurs

- **Corrélation** : brief non enregistré refusé ; payload contenant autre cible/révision/mandat, scope ou Task refusé ; issuer actuellement autorisé.
- **Autorité** : `REPORT_RECEIVE` distinct de `BRIEF_BUILD`; permissions M1 de lecture/écriture conservées ; mandats révoqués/expirés refusés même sur replay.
- **Confidentialité** : filtrage scope, owner et classification INTERNAL ; PRIVATE exclu ; URI signées et payloads manifestement sensibles interdits dans le pilote.
- **Idempotence** : deux contraintes SQL d'unicité, empreinte canonique, pas de nouveau history/handoff sur replay, collision conflictuelle sans remplacement.
- **Atomicité** : un seul `SqliteUnitOfWork` pour inbox, liens et records M1 ; crash avant commit = rollback complet. `CommitOutcomeUnknown` exige la réconciliation.
- **Reprise** : processus Python distinct sur le même fichier SQLite, reprovisionnement *host-side* du mandat et même reçu initial, sans double report.
- **Non-promotion** : `QUALIFIED` déclaré ne transforme jamais une Task en DONE, un Project en COMPLETED, ni en `Approval`.
- **Précaution supplémentaire M1** : un PASS de vérificateur synthétique demeure dans `m2_verifications` mais n'écrit pas de record `assessment PASS` exploitable par `RegistryService.verify_status` ; le record historique M1 est une **observation**.

## Traçabilité d'acceptation

| Critère | État M2-B | Limite |
|---|---|---|
| AC-028 | VERIFIED_SYNTHETIC_PILOT | Pas d'agent distant réel |
| AC-029 | VERIFIED_SYNTHETIC_PILOT | Pas de preuve CI réelle |
| AC-030 | PARTIAL (AUDIT read-only local) | Pilotes M2-C requis |
| AC-033 | VERIFIED_SQLITE_LOCAL | Pas de `exactly-once` distribué |
| AC-034 | VERIFIED_SEPARATION_OF_COMMANDS | Approbation de gate réelle réservée à l'humain |
| AC-032 | REGRESSION_PASS | Tests hostiles M2-C à compléter |
| AC-035 | REGRESSION_PASS (get/list + scope) | Pas d'API universelle count/export |
| AC-036 | PARTIAL (restart subprocess) | Reprise de projet complète à qualifier M2-C |

## Décisions et limites

- `ADR-M2-03` (SQLite/inbox/idempotence) et `ADR-M2-04` (verification/human review) : **PROPOSED**.
- `ADR-M2-01/02/05` M2-A : toujours soumis à revue.
- `InMemoryMandateStore` demeure volatile; le processus hôte doit reprovisionner son mandat après restart.
- Aucun chiffrement SQLite, IAM autonome, système de rétention/purge de données réelles ou sandbox de processus hostile.
- Les faux adapters ne qualifient pas GitHub, la CI ou un livrable externe réel.
- Aucun service d'exécution Pythos distant, pas de LLM, de réseau ou de secrets réels.
- Les méthodes M2-B composent les transactions à travers `SqliteUnitOfWork` et les lecteurs M1 sous le périmètre local testé, sans annoncer une transaction distribuée.
- Les métriques agrégées et connecteurs externes restent hors scope de M2-B.
- Aucun gate humain ou revue sécurité indépendante n'a été émis au seul motif de CI verte.

## Handoff vers M2-C

```yaml
handoff_m2b_to_m2c:
  date: "2026-11-04"
  tranche: M2-B
  implementation_status: IMPLEMENTED_SYNTHETIC_LOCAL
  technical_status: CI_PASS
  code_sha: 50c972d134b3a94c2a5df050acd2fc1a3d76822a
  ci_run_id: 41887626111
  pr: https://github.com/tawounfouet/pyprojectkit/pull/17
  verified_contracts:
    - OperatingBriefDTO_v1
    - ExecutionReportDTO_v1
    - IssuedBriefReceipt_SQLite_0003
    - Atomic_Inbox_M1_Links
    - Replay_Reconcile_Local
    - Independent_Verification_Pilot
    - Human_Decision_Separation
  limits:
    - SYNTHETIC_DATA_ONLY
    - NO_REMOTE_PYTHOS
    - NO_PRIVATE_SCOPE_DELEGATION
    - NO_PRODUCTION_IAM_OR_ENCRYPTION
    - NO_M1_VERIFIED_PASS_FROM_SYNTHETIC_VERIFIER
  human_gate: PENDING
  global_q_m2: NOT_ASSESSED
  next_work_items:
    - M2-08
    - M2-09
    - M2-10
    - M2-11
    - M2-12
```

**Conclusion** : préparation technique de M2-C démontrée dans un pilote local synthétique, sans verdict humain GO, sans merge et sans publication. Pour démarrer des pilotes au-delà des fixtures, une décision explicite de périmètre et des ADR approuvés restent nécessaires.

## Navigation

- [PR M2-B #17](https://github.com/tawounfouet/pyprojectkit/pull/17)
- [CI #160](https://github.com/tawounfouet/pyprojectkit/actions/runs/41887626111)
- `docs/m2/M2B_IMPLEMENTATION_GUIDE.md`
- `docs/adr/ADR-M2-03-sqlite-inbox-idempotence.md`
- `docs/adr/ADR-M2-04-independent-verification-human-review.md`
