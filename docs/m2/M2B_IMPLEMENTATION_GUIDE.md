# M2-B - Guide d'exécution local et handoff vers M2-C

> 4 novembre 2026 - M2-04 à M2-07
>
> Périmètre : pilote exclusivement synthétique, SQLite local, aucun accès à Pythos réel ni à une CI réelle.
>
> Source : `19_PYPROJECTKIT_M2B_IMPLEMENTATION_PLAN.md`.
>
> Statut : implémentation candidate, approbation humaine et ADR en attente.

## 1. Usage et préconditions

Cette tranche se base sur M2-A PR #16, encore non fusionnée au début du chantier. Sa PR est empilée sur la branche M2-A pour ne pas modifier `main` directement.

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/m2_report_inbox_demo.py
python -m mypy --strict --python-version 3.12 src/pyprojectkit examples/first_project.py
python -m pip wheel --no-deps -w dist .
```

Le script `m2_report_inbox_demo.py` constitue une fixture synthétique locale, sans appel externe, sans informations personnelles ni secrets.

## 2. Contrats et services

| Module | Interface | Usage |
|---|---|---|
| `m2.reports` | `ExecutionReportDTO` / `ReportEvidenceRefDTO` | déclaration versionnée, JSON strict, empreinte SHA-256 |
| `m2.inbox` | `ReportInboxService.issue_brief` | passage de Query M2-A à reçu d'émission SQLite |
| `m2.inbox` | `ReportInboxService.receive` | corrélation, autorisation, inbox + historique M1 atomiques |
| `m2.inbox` | `ReportInboxService.reconcile` | résolution de résultat de commit inconnu, sans re-write |
| `m2.inbox` | `get_report/list_reports` | lectures filtrées par scope, owner et permissions |
| `m2.governance` | `ReportGovernanceService.request_verification` | résultat M2 séparé ; observation M1 mais jamais PASS M1 synthétique |
| `m2.governance` | `request_human_decision` | demande `PENDING`, sans approbation automatique |
| `m2.governance` | `decide_human_request` | décision habilitée avec séparation des fonctions, sans transition de Task |
| `m2.fake` | `FakePythosAdapter` | producteur déterministe, sans runtime agent |

## 3. Garanties locales

- Schéma SQLite migration 0003 additive avec empreinte checksum, triggers append-only et contraintes uniques par scope/mandat.
- Un `brief_id` seul ne permet jamais l'ingestion. `issue_brief` écrit d'abord un reçu autoritatif avant de retourner le DTO ; un simple `BuildAuthorizedOperatingBrief` M2-A n'émet aucun reçu.
- `REPORT_RECEIVE` est distinct de `BRIEF_BUILD`. Une session `TrustedHost` vérifiée et un mandat courant sont indispensables.
- Tous les writes acceptés (`m2_report_inbox`, `m2_report_links`, `history` M1) utilisent une même transaction `SqliteUnitOfWork`.
- Les retries identiques renvoient le même `ingestion_id` avec `ALREADY_ACCEPTED`; un conflit de clé ou de contenu n'est jamais écrasé.
- En cas de `CommitOutcomeUnknown`, utiliser `reconcile(actor, report)` avant toute tentative supplémentaire ; absence ne prouve pas l'absence si la base est inaccessible.
- Les rapports restent `DECLARED`; `QUALIFIED` dans le DTO n'a aucun effet sur `Project.status`, `Task.status`, `VerificationAssessment` M1 ou `Approval`.
- Les vérifications synthétiques sont confinées à `m2_verifications`. Un PASS synthétique ne peut pas contaminer `RegistryService.verify_status`.
- L'évaluation et la revue humaine utilisent des commandes distinctes, un principal authentifié et un enregistrement horodaté.
- `PRIVATE` demeure hors M2-A/M2-B ; aucun secret ou URI signée dans l'inbox non chiffrée. Le filtrage lexical est défensif, pas un scanner de secrets complet.

## 4. Reprise après interruption

Le mandat M2-A reste un enregistrement en mémoire du processus de confiance, non un IAM durable. Pour reprendre après redémarrage d'un autre processus :
1. Réouvrir le fichier SQLite avec `SqliteDatabase(path)`.
2. Authentifier le nouveau processus auprès du `TrustedHost` approprié.
3. **Reprovisionner le même mandat à partir de la source de confiance de l'hôte**, jamais depuis le JSON agent.
4. Réconcilier le report via `reconcile()`.
5. Si le reçu original est retrouvé et identique, retourner son `ingestion_id` ; sinon, distinguer absence probante, collision et indisponibilité.

Le test `test_m2b_30_restart_in_another_python_process` exécute ce parcours dans un nouvel interpréteur Python.

## 5. Exceptions et matrice de repli

| Situation | Résultat et prochain geste |
|---|---|
| Version DTO inconnue | `UnsupportedContractVersion`; mise à jour de contrat explicite |
| Mandat expiré, suspendu, révoqué | Refus `AccessDenied`, sans lecture du reçu |
| Brief non émis | `NotFound`, sans divulgation de projet |
| Fingerprint divergent | `IdempotencyConflict`, sans nouvel effet |
| Crash avant commit | Rollback local ; replay sous mandat courant |
| Commit inconnu | `CommitOutcomeUnknown` et `reconcile` |
| Source de vérification indisponible | `UNKNOWN`, jamais PASS M1 |
| Demande de revue sans décideur | `PENDING`, aucune approval |
| Auto-approbation | Refus de séparation des fonctions |

## 6. Exclusions et critères de passage M2-C

Cette tranche n'exécute pas Pythos, un LLM, un agent distribué, une vraie plateforme CI ou une publication. Le stockage SQLite n'est pas chiffré. Les contrôles ne remplacent pas une revue de sécurité indépendante. Les ADR-M2-03/04 restent **PROPOSED** jusqu'à leur approbation humaine.

M2-C devra tester deux pilotes hétérogènes, les contextes réels autorisés et des contrôles adversariaux supplémentaires. L'intégration d'un vrai vérificateur source est une décision séparée ; aucun résultat synthétique M2-B ne peut servir à faire passer un gate de release.

**Handoff cible** : le chemin de report est techniquement préparé ; sa revue humaine et ses validations de périmètre restent des gates avant usage non synthétique.
