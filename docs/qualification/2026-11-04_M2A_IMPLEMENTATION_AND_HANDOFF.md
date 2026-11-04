# PyProjectKit - Rapport d'implémentation, qualification et handoff M2-A

> Date : 2026-11-04
>
> Tranche : M2-A / VS-M2-01 / M2-01..M2-03
>
> Baseline de `main` : `26487b61f54a49fa1d5eec6bd2d36eda01524ac8`
>
> **SHA de code soumis aux vérifications citées** : `c3a04e9a5fe35687e8270022a7a0d3b69abe88b2`
>
> Branche : `feat/m2a-authorized-brief` ; PR #16, draft
>
> **Statut : IMPLEMENTED_SYNTHETIC_LOCAL_PILOT / TECHNICAL_CI_PASS / M2A_HUMAN_GATE_PENDING**
>
> **Q-M2 : NOT_ASSESSED. Aucune autorisation de fusion, publication ni usage de données réelles.**

## 1. Résultat livré

`VS-M2-01` construit un `OperatingBriefDTO` versionné depuis une `Task` persistée M0/M1, après résolution d'un mandat host-side et contrôle de la visibilité M1. Le DTO est une projection en lecture, jamais un jeton de capacité, une décision, une preuve autonome ou un changement d'état métier. Pythos n'est pas invoqué.

| WorkItem | Réalisation | État |
|---|---|---|
| M2-01 | DTO v1, refs typées, validation forte, sérialisation JSON déterministe, fixture | IMPLEMENTED / TESTED_PILOT |
| M2-02 | `BuildAuthorizedOperatingBrief`, lecteurs M1, minimisation, double lecture et watermark tâche | IMPLEMENTED / TESTED_PILOT |
| M2-03 | `DelegationMandate`, `MandateVerifier`, store hôte synthétique, révocation/expiration/permissions | IMPLEMENTED / TESTED_PILOT |

Composants : `src/pyprojectkit/m2/{__init__,contracts,mandates,application}.py`, `tests/test_m2a.py`, `tests/test_m2a_contract_fixture.py`, `tests/fixtures/m2a_operating_brief_v1.json`, `examples/m2_authorized_brief_demo.py`.

## 2. Preuves d'exécution au SHA exact

CI : [GitHub Actions run #116](https://github.com/tawounfouet/pyprojectkit/actions/runs/41846997515), déclenché sur le commit `c3a04e9a5fe35687e8270022a7a0d3b69abe88b2` (la PR peut générer un commit de merge synthétique pour la vérification).

| Contrôle | Python 3.12 (job 126633009966) | Python 3.13 (job 126633009119) |
|---|---|---|
| pytest complet | **68 PASS** | **68 PASS** |
| Différence M2-A vs baseline 41 | 27 tests M2-A | 27 tests M2-A |
| `mypy --strict` | **PASS, 17 fichiers** | **PASS, 17 fichiers** |
| Exemple `VS-M2-01` | **PASS** | **PASS** |
| Build `pyprojectkit-0.2.0a1-py3-none-any.whl` | **PASS** | **PASS** |
| Installation et import wheel isolée (sans Pythos) | **PASS** | **PASS** |
| Statut des jobs | **SUCCESS** | **SUCCESS** |

Le numéro `0.2.0a1` reste la version du package M0/M1 dans la configuration; l'ajout M2-A à une branche de travail ne vaut pas une release `0.3.0a0`.

## 3. Contrôles de sécurité démontrés

- Credentials/acteurs : `TrustedHost` M1, identité `VerifiedActor` vérifiée, aucune identité issue d'un payload Pythos.
- Opération : permission supplémentaire `BRIEF_BUILD`, puis `PROJECT_VIEW` et `TASK_VIEW`.
- Mandat : `actor_id`, `delegate_id`, `scope_id`, `project_id`, `WorkItemRef`, `mode` et `ExactTargetReference` contrôlés.
- Temporalité : refus d'un mandat expiré, suspendu ou révoqué, y compris changement de validité durant la projection.
- Confidentialité : refus cross-scope et inter-owner même avec un mandat host-side trop permissif ; accès autorisé uniquement sur partage explicite du projet.
- `PRIVATE` : les scopes PRIVATE sont exclus de M2-A, même si l'acteur possède READ_PRIVATE. Un droit de lecture humain n'est pas un droit de divulgation à Pythos.
- Références : les identifiants opaques sont exigés, les URI signées, credentials et query strings sont refusés.
- TTL : refus si une projection lente dépasse la durée de validité de son propre brief.
- `AUDIT/A0` : lecture seule ; A2 ne permet pas de publier, fusionner ou supprimer ; A4/A5 non pris en charge dans M2-A.
- Anti-TOCTOU : revalidation de mandat et relecture du contexte ; refus en cas de variation observée de tâche.
- Absence de mutation : comparaison des versions/statuts Project/Task et des enregistrements de history avant/après.
- Contrat : version inconnue, JSON avec clé dupliquée, champ inconnu, date naïve, payload surdimensionné, révision Git non exacte refusés.

## 4. Traçabilité AC

| Critère | Résultat M2-A | Ce qui reste hors tranche |
|---|---|---|
| AC-027 | VERIFIED_SYNTHETIC_PILOT | Revue humaine du contrat et ADR |
| AC-035 | PARTIAL_READ_PATH_VERIFIED | Vérifier les chemins M2-B/C |
| AC-031 | PARTIAL_POLICY_VERIFIED | Vérifier les intégrations à outils/exécution |
| AC-032 | PARTIAL_REQUEST_VALIDATION_VERIFIED | Vérifier les commands/reportings |
| AC-030 | PARTIAL_QUERY_READ_ONLY_VERIFIED | Pilote AUDIT complet en M2-C |

Aucun `PASS` global de Q-M2 n'est déduit du présent rapport.

## 5. Décisions documentées et réserves

ADR produits en statut **PROPOSED** : `ADR-M2-01` (DTO), `ADR-M2-02` (mandats) et `ADR-M2-05` (WorkItemRef). L'autorité humaine doit décider de leur adoption pour le pilote.

Limites importantes :
- SQLite local non chiffré et session `TrustedHost` M1 supposée de confiance.
- `InMemoryMandateStore` ne constitue pas un service IAM de production, ni une source persistée de mandats interprocessus.
- Absence d'isolation face à du Python hostile dans le même processus.
- Les scopes PRIVATE ne sont pas délégués dans le pilote M2-A ; une future délégation explicite exigera un ADR et des tests.
- Les titres de tâches M1 sont des champs du domaine : pas de scanner générique de secrets ni de garantie de nettoyage s'ils contiennent des informations sensibles.
- SHA Git syntaxiquement exact, mais disponibilité du commit non contrôlée chez GitHub.
- Revalidation avant restitution, sans transaction distribuée ni garantie sur des actions futures du consommateur.
- Ni inbox M2, ni `ExecutionReportDTO`, ni idempotence des reports, ni migration `0003`, ni exécution LLM.
- Aucun audit de sécurité tiers ou autorisation de production effectué.

## 6. Handoff explicite vers M2-B

```yaml
handoff_m2a_to_m2b:
  implemented: true
  pilot_scope: SYNTHETIC_LOCAL
  code_sha: c3a04e9a5fe35687e8270022a7a0d3b69abe88b2
  ci_run_id: 41846997515
  python_312: SUCCESS_68_PASS
  python_313: SUCCESS_68_PASS
  mypy_strict: SUCCESS
  authorized_brief_schema: "1.0"
  mandate_store: IN_MEMORY_HOST_TRUSTED_ONLY
  report_ingestion: NOT_IMPLEMENTED
  human_gate: PENDING
  q_m2: NOT_ASSESSED
  next_work_items: [M2-04, M2-05, M2-06, M2-07]
```

**Recommandation technique** : code M2-A prêt pour revue de gate, puis ouverture de M2-B dans le même périmètre synthétique après accord humain. Aucune fusion ou publication n'est autorisée par ce rapport.

## 7. Points de revue humaine avant `GO_M2B`

1. Accepter ou amender ADR-M2-01, ADR-M2-02 et ADR-M2-05.
2. Confirmer la frontière `TrustedHost` et le fait qu'un mandat en mémoire ne survit pas au redémarrage.
3. Valider les limites de confidentialité et la non-divulgation des projets/owners.
4. Décider `GO_M2B`, `CONDITIONAL_GO_M2B` ou `NO_GO_M2B` avec références de preuves et risques résiduels.
5. Conserver la PR non fusionnée et la release non publiée tant qu'un gate autorisé ne les approuve.

## 8. Liens

- [PR #16](https://github.com/tawounfouet/pyprojectkit/pull/16)
- [CI #116](https://github.com/tawounfouet/pyprojectkit/actions/runs/41846997515)
- `docs/m2/M2A_IMPLEMENTATION_GUIDE.md`
- `docs/adr/ADR-M2-01-operating-brief-v1.md`
- `docs/adr/ADR-M2-02-delegated-authority.md`
- `docs/adr/ADR-M2-05-workitem-reference.md`
