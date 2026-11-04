# 16 - PYPROJECTKIT - PLAN D'IMPLÉMENTATION M2 : INTÉGRATION OPTIONNELLE AVEC PYTHOS

> **Projet** : PyProjectKit  
> **Document** : `16_PYPROJECTKIT_M2_IMPLEMENTATION_PLAN.md`  
> **Version documentaire** : `0.1.0` - proposition de mise en œuvre  
> **Date de préparation** : 2026-11-03  
> **Langue** : français, identifiants techniques Python/DDD conservés en anglais  
> **Statut** : `REVIEW / IMPLEMENTATION_NOT_STARTED / Q-M2_NOT_ASSESSED`  
> **Périmètre** : M2, *Pythos Integration* optionnelle, jalon C2  
> **Référence du code intégré** : `main` au SHA `26487b61f54a49fa1d5eec6bd2d36eda01524ac8` (état constaté au lancement de la rédaction)  
> **Principe d'autorité** : mandat humain, permissions et version exacte sont des contraintes d'exécution, jamais des propriétés déduites du seul nom « Pythos ».

---

# 0. Résumé exécutif

M2 ajoute à PyProjectKit une **boucle de collaboration optionnelle avec Pythos**, au-dessus du registre durable M1. Une action autorisée produit un `OperatingBrief` filtré ; Pythos prépare un travail sous mandat ; il retourne un `ExecutionReport` attaché à la **même unité de travail et à une référence exacte** ; PyProjectKit conserve ce retour comme déclaration et source potentielle de preuves, sans l'assimiler à une mutation métier, à un résultat `PASS`, à une approbation humaine ou à une qualification autonome. Une nouvelle session peut reconstruire le dossier depuis le registre M1.

**Contrat de résultat** :

```text
Project / Task / Registry M1 (source durable et scoped)
  -> BuildAuthorizedOperatingBrief (projection filtrée + mandat vérifié)
  -> OptionalPythosAdapter / FakePythosAdapter (externe, non autoritatif)
  -> ReceiveExecutionReport (schema + scope + target_revision + idempotence)
  -> Append declaration / evidence refs / handoff to M1 (transaction locale)
  -> IndependentVerification / HumanApproval (commands distinctes)
  -> ResumeSameWorkItem (nouvelle session, historique sourcé)
```

**Volume contractuel repris de la roadmap V2** : `M2-01..M2-12` (12 WorkItems), `AC-027..AC-037` (11 critères), répartis entre **M2-A**, **M2-B** et **M2-C**. Aucune dépendance obligatoire du domaine `pyprojectkit.domain` vers Pythos, PyAgentsKit, PyAgentRuntime ou un fournisseur LLM.

**Préconditions** : la fusion R0/M0/M1 sur `main` est réalisée, mais les gates précédents ont un **GO conditionnel limité au prototype local avec données synthétiques**, sans licence ni autorisation de production. M2 ne peut donc commencer qu'en **mode expérimental local et synthétique** sous mandat de développement séparé ; son intégration sur `main` et son propre gate exigent des preuves et un accord ultérieurs. Ce plan n'exécute aucun test M2 et ne donne aucune permission de merge, de publication ou d'opération destructive.

# 1. Sources et état observé

## 1.1 Sources normatives / historiques

| Source | Sections de référence | Apport au plan |
|---|---|---|
| `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP_V2` (source locale fournie sous le suffixe `(1)`) | §10, §11, §12, §15, annexes des AC | Les 12 WorkItems, tranches et gate Q-M2 |
| `00_PYPROJECTKIT_REQUIREMENTS_ANALYSIS_V2` | C2, `AC-027..037` | Scénarios de recette détaillés et exclusions |
| `2026-11-02_PYPROJECTKIT_PYTHOS_PLAN_INTEGRATION_ET_ALIGNEMENT` | §3 à §7, §9 à §11 | Propriété des faits, contrats read/write et cas pilotes |
| `00_PYTHOS_VISION_AND_OPERATING_MODEL` | §9, §15 à §23, annexes A/B | Modes, niveaux A0-A5, brief, report, gates G0-G7 |
| `PYPROJECTKIT_SOFTWARE_DESIGN_LEARNING_OVERLAY` | §17, §20, §24 | Découplage, alternatives et fitness functions |
| `08/09/10/11/12_PYPROJECTKIT_*_V2` | Commands, événements, ports, erreurs, autorisation | Garanties d'intégration, non-divulgation et échecs |
| `15_PYPROJECTKIT_M1_IMPLEMENTATION_PLAN` et ADR-M1-01/02/03 | Architecture, contrat scoped, SQLite et handoff | Socle de persistance réutilisable |
| `docs/qualification/2026-11-03_POST_MERGE_MAIN_AUDIT.md` sur `main` | Audit et réserves | Qualification conditionnelle R0/M0/M1 |

Les documents proposent un modèle d'intégration ; **aucune source ne démontre un adapter PyProjectKit/Pythos déjà opérationnel**. Les noms d'API décrits ci-dessous sont donc des **candidats**, pas des signatures existantes.

## 1.2 État réel du logiciel de départ

À la revue du code M1 intégré sur `main` :

- `RegistryService` expose notamment `get_registry`, `list_tasks`, `list_history`, `observe`, `attach_evidence`, `assess`, `record_decision`, `approve_decision`, `record_handoff`, `capture_snapshot`, `resume` et `export_project`.
- `SqliteDatabase` et `SqliteUnitOfWork` s'appuient sur les migrations SQLite 0001 et 0002, avec historique append-only dans `history`.
- `TrustedHost` fournit un `VerifiedActor` et des permissions par scope ; le correctif M1 impose aussi propriété ou partage explicite pour lire un projet d'un autre propriétaire du même scope.
- Les 41 tests M0/M1, le typage strict et la wheel installée isolément ont été vérifiés sur Python 3.12 et 3.13 lors de l'intégration du 3 novembre 2026.
- La garantie de sécurité **ne couvre pas** du code Python hostile dans le même processus ni une identité de production. SQLite est local et non chiffré. Le core n'a ni registre de mandats Pythos, ni DTO M2, ni protocole de transport Pythos, ni ingestion idempotente d'`ExecutionReport`.

**Point de vigilance `WorkItem`** : dans les sources, le `Work Item` est une unité opératoire de Pythos. Le code M0/M1 dispose de `Task`, `RegistryEntry`, `NextAction` et `Handoff`, pas d'un Aggregate Root universel `WorkItem`. M2 introduit une **référence d'intégration** `WorkItemRef` liée à un `ProjectId` et, si applicable, un `TaskId` existant. Créer un nouvel Aggregate Root ne se justifierait que par une pression métier et un ADR distincts.

# 2. Résultats attendus, non-objectifs et contraintes

## 2.1 Résultats observables

1. Générer un `OperatingBriefDTO` **versionné**, contextualisé, filtré par la visibilité réelle de l'acteur, attaché à un mandat vérifié et une référence exacte.
2. Recevoir un `ExecutionReportDTO` versionné, le contrôler (identité de la mission, scope, mode, mandat, dates, cible et révision), puis l'enregistrer sans mutation métier implicite.
3. Conserver les déclarations, limitations, sources et preuves comme enregistrements **non probants par défaut** ; produire un résultat de vérification indépendant seulement après contrôle de source et action autorisée.
4. Démontrer l'idempotence : un retry identique ne crée ni double rapport, ni nouvelle action, ni double transition.
5. Exécuter un audit en mode `AUDIT` sans modifier le projet audité, même en présence d'une demande de mutation dans le report.
6. Reprendre la **même unité de travail** dans un nouveau processus et retrouver mandat, brief, reports, décisions, preuves et handoff sourcés.
7. Démontrer que le core reste utilisable sans Pythos et que les projets non logiciels ne reçoivent ni gates G0-G7 ni taxonomie probante Py*Kit par défaut.

## 2.2 Hors périmètre M2

- Construction ou remplacement de l'agent Pythos, de PyAgentsKit, PyAgentRuntime, PyAuthKit ou d'un LLM provider.
- Orchestration multi-agents distribuée, durable execution inter-hôtes, pipelines de release ou shell arbitraire.
- Autorisation pour Pythos de fusionner GitHub, publier PyPI, supprimer un dépôt, accepter un risque, modifier une priorité réservée ou approuver un gate.
- Import d'informations personnelles, client ou employeur réelles sans mandat séparé et garanties de confidentialité qualifiées.
- Externalisation obligatoire du registre vers PostgreSQL, SaaS, queue ou Event Store.
- Refactor global du noyau M0/M1 et création d'une seconde source de vérité de `ProjectStatus` ou `TaskStatus`.

## 2.3 Règles non négociables

- **Une capacité d'outil ne crée pas une permission** : le `authority_level=A2` d'un brief ne remplace jamais `AuthorizationPolicy` ou les droits de l'hôte.
- **A4 et A5 restent réservés aux décisions/permissions appropriées de l'autorité humaine** selon le modèle Pythos ; pas de promotion via simple étiquette de report.
- **Aucun `ExecutionReport.status=QUALIFIED` ne produit `TaskCompleted`, `ProjectCompleted`, `PASS` ou `APPROVED` par transitivité.**
- **`AUDIT` est read-only sur l'objet audité**. Le système peut enregistrer le rapport d'audit dans son propre journal d'intégration si mandaté, sans altérer l'état métier de l'objet.
- **État et preuve appartiennent à leurs systèmes sources** ; SHA d'un commit, résultat CI et approbation humaine sont vérifiés auprès des autorités compétentes.
- **Sécurité par refus par défaut** à l'entrée, à la construction du brief, à l'ingestion et aux Queries (pagination, comptes, exports, erreurs, logs inclus).

# 3. Architecture candidate, frontières et contrats

## 3.1 Architecture logique

```text
TrustedHost / VerifiedActor / ScopeRule / policy M1
             |
             v
M2 Application use cases (mandate checks + DTO validation + idempotency)
  |          |                 |                    |
  v          v                 v                    v
M1 Readers   MandateStorePort  ReportInboxPort      EvidenceVerificationPort
(project,    (scope, actor,    (dedupe, payload,    (source authority,
 task,       targets, expiry,   state, linkage,      exact revision,
 evidence)   actions)          append-only)         decision)
  |                               |
  v                               v
OperatingBriefDTO             ExecutionReportDTO -> M1 history/handoff
  |                               ^
  v                               |
PythosPort (optional) -> FakePythosAdapter / external host adapter

CORE M0 DOMAIN : aucune dépendance Pythos / A0-A5 / G0-G7.
```

La distinction **Ports / Adapters / Application / Domain** découle de la convention Software Design & Learning. Il faut éviter une couche de ports fictifs : une interface n'est ajoutée que si elle protège un use case ou autorise un test de contrat concret.

## 3.2 Découpage Python proposé (non encore créé)

```text
src/pyprojectkit/
  domain.py                         # M0 inchangé, indépendant de Pythos
  m1/                               # registre durable et continuité
  m2/
    __init__.py                     # opt-in, aucun import Pythos direct
    contracts.py                    # DTOs versionnés + validation
    mandates.py                     # Capability / Mandate / expiry / restrictions
    application.py                  # BuildBrief, ReceiveReport, Verify, Resume
    ports.py                        # ports ciblés
    sqlite.py                       # persistence M2, migration 0003 candidate
    adapters/
      fake_pythos.py                # tests déterministes, aucun appel LLM
      pythos_host.py                # facultatif, à condition de disposer d'un contrat réel
    security.py                     # projection/redaction et gardes M2

tests/
  m2/test_contracts.py
  m2/test_mandates.py
  m2/test_integration_sqlite.py
  m2/test_idempotency.py
  m2/test_security.py
  m2/test_e2e_pilots.py
examples/
  m2_audit_handoff.py               # uniquement fixtures synthétiques
```

**Arbitrage d'import** : l'usage de `pyprojectkit` et de M0/M1 sans importer `pyprojectkit.m2` reste possible ; ne pas ajouter une dépendance Pythos dans `pyproject.toml` par défaut. L'adapter externe ne doit pas être promis fonctionnel tant que son API réelle n'est pas contractualisée et testée.

## 3.3 DTO `OperatingBriefDTO` v1 candidat

Le contrat Pythos source possède `project`, `mode`, `problem`, `expected_outcome`, `in_scope`, `out_of_scope`, `authority_level`, `target_reference`, `acceptance_criteria`, `required_evidence`, `human_decisions`, `risks` et `next_safe_action`. Proposition de traduction **sans exporter une copie de Project** :

| Champs | Provenance et contrainte |
|---|---|
| `schema_version`, `brief_id`, `created_at`, `expires_at` | Format versionné, horloge injectée, TTL borné |
| `project_id`, `work_item_ref`, `scope_id` | Références existantes, opaques et scoped |
| `mode` | `LEARNING/PRODUCTION/AUDIT/PORTFOLIO`, métadonnée Pythos uniquement |
| `mandate_id`, `authority_level`, `allowed_actions` | Mandat effectivement vérifié dans l'hôte, jamais saisi librement comme permission |
| `problem`, `expected_outcome`, `in_scope`, `out_of_scope` | Projection métier autorisée ; champs obligatoires non vides |
| `target_reference` | Référence exacte, SHA/revision si le sujet est du code ; pas de simple `main` pour la qualification |
| `acceptance_criteria`, `required_evidence` | Contrats de vérification, sans autoriser l'auto-qualification |
| `human_decisions`, `risks`, `limitations`, `next_safe_action` | Synthèse explicitant ce qui reste réservé ou incertain |
| `source_watermark`, `projection_created_at` | Date/état de référence : la projection peut devenir périmée |

**Règles de validation** : rejeter champ inconnu critique ou version non supportée ; taille maximale du payload ; identifiants typés ; horloge timezone-aware ; aucun secret, credential, chemin privé ou contenu de preuve brut dans un brief de démonstration. Les valeurs par défaut n'étendent jamais un mandat.

## 3.4 Mandat M2 candidat

`ExecutionMandate` proposé : `mandate_id`, `issuer_ref`, `subject_actor_id`, `scope_id`, `project_id`, `work_item_ref`, `mode`, `authority_level`, `allowed_actions`, `denied_actions`, `target_reference`, `issued_at`, `expires_at`, `revocation_state`, `human_approval_ref?` et `policy_version`.

- Le mandat est **émis ou attesté par le TrustedHost**, lié au principal vérifié et à un scope/projet précis. Un objet JSON remis par Pythos ne constitue pas une preuve de mandat.
- Vérification au **moment de chaque opération** : signature/méthode de confiance si choisie, date de validité, révocation, acteur, scope, cible, version, mode et action demandée.
- L'autorisation effective est **l'intersection** des permissions hôte, des restrictions du mandat, du mode et des invariants métier. Une autorité A0-A5 supérieure ne contourne pas cette intersection.
- Mandat expiré, invalide, révoqué, inconnu, réutilisé hors scope, au mauvais SHA ou sans approbation nécessaire : **DENY** et aucune mutation métier.
- Une intervention `AUDIT` ne peut demander qu'une lecture du projet ciblé, puis l'enregistrement externalisé de son compte rendu autorisé.
- Le principe de moindre privilège s'applique au payload du brief comme aux données que le report pourrait révéler.

## 3.5 DTO `ExecutionReportDTO` v1 candidat

Champs issus des sources Pythos : `outcome`, `mode_and_scope`, `exact_reference`, `changes_made`, `verification_performed`, `evidence`, `acceptance_criteria`, `limitations`, `residual_risks`, `human_decisions_required`, `status`, `next_action`. Champs de corrélation M2 nécessaires, **proposés** : `schema_version`, `report_id`, `brief_id`, `mandate_id`, `work_item_ref`, `project_id`, `scope_id`, `received_at`, `produced_at`, `operation_id`, `idempotency_key`, `source_watermark`.

**Règle de provenance** : `status=QUALIFIED` reste **une déclaration Pythos**. Pour devenir un `VerificationAssessment` du registre M1, il faut une source accessible, un sujet, une révision exacte, une permission `ASSESS` et une vérification réellement opérée. Le report ne remplace ni cette étape ni l'approbation humaine d'une décision.

## 3.6 Réutilisation des capacités M1 et stockage candidat

Réutiliser les ports et méthodes existants de M1 (`list_history`, `observe`, `attach_evidence`, `record_handoff`, `resume`, etc.) lorsque leurs permissions et garanties sont suffisantes. **Ne pas** stocker un `ExecutionReport` complet comme une `Task` ou comme un `Project`.

**Migration SQLite `0003` envisagée, non approuvée** :

- `m2_mandates` ou journal de références de mandats (scoped, sans enregistrer de secrets en clair) ;
- `m2_briefs` (workitem/project, version, watermark, mandate_ref, payload minimal/redacted) ;
- `m2_report_inbox` (report_id, idempotency_key, source_fingerprint, refs, reçu/parsé/rejeté/enregistré, classifications, horodatages) ;
- `m2_report_links` (report -> observation/evidence/handoff/decision-request, sans FK implicite cross-scope) ;
- contraintes uniques sur le **couple scope/mandat/report_id** et sur l'identifiant d'opération, après décision de l'algorithme d'idempotence.

Les données historisées restent append-only ou versionnées ; ne pas modifier rétroactivement un rapport accepté. Le stockage de secrets, tokens ou contenu privé brut est proscrit par défaut. Les changements doivent être testés avec les migrations 0001 et 0002 existantes, ainsi qu'avec sauvegarde/restauration, checksums, transactions et crash avant commit.

**Idempotence** : un second report avec mêmes `mandate_id`, `report_id`, `idempotency_key` **et** empreinte de payload retourne le résultat persistant initial ; un identifiant identique avec contenu différent produit `IdempotencyConflict`. Le `commit()` de l'inbox et du handoff local utilise une même UoW lorsque la garantie d'atomicité est revendiquée ; tout effet externe reste explicitement non atomique avec SQLite.

# 4. Plan opérationnel M2-A à M2-C : 12 WorkItems

## 4.1 M2-A - Contrats et contexte autorisé

| ID | Livraison attendue | Dépendances | Test/critère bloquant |
|---|---|---|---|
| `M2-01` | `OperatingBriefDTO v1`, sérialisation canonique, parseur/validateur, erreur de version, fixture | M1 Reader ; ADR-M2-01 | `AC-027` : brief complet, borné et sans champ interdit |
| `M2-02` | `BuildAuthorizedOperatingBrief` et sélection du contexte (scope/owner/WorkItem/mode) ; redaction + watermark | M2-01, security M1 | Aucune Task/Observation/Evidence non visible dans brief, même via count |
| `M2-03` | `MandateVerifier` / port TrustedHost, TTL, révocation, actions, cible exacte, A0-A5 et permissions effectives | M2-01/02 ; ADR-M2-02 | `AC-031/032/035` : refus A2 merge/publish, cross-scope, mandat expiré |

**DoD M2-A** : le premier vertical slice construit un brief **sans exécuter Pythos**, vérifie 2 acteurs / 2 scopes / 2 owners dans un scope, et démontre qu'une mutation n'est pas déduite du document d'entrée.

## 4.2 M2-B - Réception, déclaration et vérification du report

| ID | Livraison attendue | Dépendances | Test/critère bloquant |
|---|---|---|---|
| `M2-04` | `ExecutionReportDTO v1` + validations de schema, mode, source, taille, dates et liaison WorkItem | M2-A ; ADR-M2-01 | `AC-028` : report lié à la bonne unité de travail, payload erroné rejeté |
| `M2-05` | `ReceiveExecutionReport` + inbox SQLite append-only + Observation/EvidenceRef/Handoff sous permission | M2-04, SQLite M1 ; ADR-M2-03 | `AC-029/030` : aucune promotion ou mutation métier implicite |
| `M2-06` | `RequestIndependentVerification` + `RequestHumanDecision`, sans auto-approbation ; réutilisation des capacités M1 | M2-05 ; ADR-M2-04 | `AC-034` : gate G5 exige décision humaine traçable distincte |
| `M2-07` | Stratégie d'idempotence d'ingestion et de handoff, rejouage et récupération de commit incertain | M2-05/06 ; ADR-M2-03 | `AC-033` : retries sans double report/action/transition |

**DoD M2-B** : un faux report `QUALIFIED` n'obtient aucun `PASS` ; aucune transition `TaskStatus.DONE` ou `ProjectStatus.COMPLETED` ne se produit à l'ingestion ; rejets atomiques ; idempotence prouvée sur redémarrage d'un **nouveau processus**.

## 4.3 M2-C - Deux pilotes et décision d'adoption

| ID | Livraison attendue | Dépendances | Test/critère bloquant |
|---|---|---|---|
| `M2-08` | Pilote **PySRMKit**, audit d'une référence exacte, lecture seule de l'objet audité | M2-A/B ; scope synthétique explicitement autorisé | `AC-030/031/034` : aucune mutation de source / merge / promotion |
| `M2-09` | Pilote hors logiciel (ex. activité pédagogique ou événement fictif) en fixtures synthétiques | M2-B ; policy distincte | `AC-037` : pas de gates G0-G7 ni de statut `QUALIFIED` imposés |
| `M2-10` | Nouveau processus/session, lecture du même WorkItem, reports, décisions, sources et handoff | M2-07/08 | `AC-036` : reprise sans dépendance à la mémoire conversationnelle |
| `M2-11` | Banc de tests hostiles : mandat expiré, cross-owner/cross-scope, A2 publish/merge, A4/A5 non autorisés, spoof, replay, payload divergent | M2-03 à 10 | `AC-029..035` et absence d'événement de succès |
| `M2-12` | Rapport Q-M2, tableau comparé des pilotes, risques et preuves SHA, recommandation d'adoption | Tous précédents | `AC-027..037`, GO/CONDITIONAL GO/NO-GO humain |

**DoD M2-C** : deux pilotes volontairement hétérogènes, même core, policies distinctes ; Pythos externe facultatif ; reproductibilité sans accès à un service LLM ; absence de permission implicite et de fuite inter-scopes.

# 5. Vertical slices, dépendances et branchement

| Tranche verticale | Parcours démontré | WorkItems | Résultat de revue |
|---|---|---|---|
| **VS-M2-01 : Authorized Brief** | `VerifiedActor -> M1 Reader -> Mandate -> Filter -> Brief v1` | 01-03 | API contractuelle et redaction reproductibles |
| **VS-M2-02 : Report Without Authority** | `FakePythos -> Report v1 -> Inbox -> declaration/evidence/handoff` | 04-06 | État M0/M1 inchangé, qualification séparée |
| **VS-M2-03 : Idempotent Handoff & Restart** | `Receive twice -> same record -> stop -> restart -> resume` | 07, 10 | Une seule observation/report/handoff logique |
| **VS-M2-04 : Scoped Audit Pilots** | `PySRMKit AUDIT -> second nonsoftware project -> adversarial tests` | 08/09/11 | Deux policies, refus des actions réservées |
| **VS-M2-05 : Q-M2** | `Exact SHA -> test suite -> evidence -> independent human decision` | 12 | Qualification M2 bornée et traçable |

Ordre recommandé : d'abord **VS-M2-01**, ensuite VS-M2-02, puis VS-M2-03 ; ne lancer les pilotes que lorsque sécurité, idempotence et non-promotion sont testées. Un pilot Pythos réel n'est **pas obligatoire** pour le premier contrat : le `FakePythosAdapter` est indispensable aux tests de sûreté et de reproductibilité. En revanche, **une adoption d'intégration réelle** exigerait une preuve de bout en bout avec le fournisseur Pythos effectivement utilisé.

### Stratégie GitHub proposée

- Base de travail : `main` à vérifier au lancement ; branche dédiée `feat/m2-pythos-adapter` **après mandat de développement M2**.
- PR 1 : M2-A contracts/mandate, sans changer le domaine ; PR 2 : M2-B inbox/handoff ; PR 3 : M2-C tests/pilotes/qualification. Si la taille du changement le nécessite, utiliser des PR empilées en conservant les SHA de base.
- Les documents d'architecture ont une PR indépendante ; **fusionner un plan documentaire ne lance pas automatiquement M2**.
- Tests `mypy --strict` et pytest sous Python 3.12/3.13, build wheel installable dans une venv isolée, contrats M0/M1 non régressifs.
- Tout nom de nouvelle méthode Python est proposé sous réserve d'ADR. Des tickets M2 individuels peuvent être créés au démarrage de chaque tranche plutôt que tous simultanément.

# 6. Matrice d'acceptation AC-027 à AC-037

| AC | Source / WorkItem | Scénario probant attendu | Preuve minimale et statut initial |
|---|---|---|---|
| `AC-027` | M2-01/02 | Brief complet, cible exacte, mandat et contexte filtré | Fixture JSON et assertions de redaction ; `NOT_EXECUTED` |
| `AC-028` | M2-04/05 | Report lié au **même** WorkItem, mandat et SHA, avec contrôles/limites/actions | Réception persistée, lien stable, réouverture ; `NOT_EXECUTED` |
| `AC-029` | M2-05/06 | `QUALIFIED` auto-déclaré sans preuve indépendante reste déclaration | Aucune transition / aucun PASS ; `NOT_EXECUTED` |
| `AC-030` | M2-05/08 | Audit Pythos en lecture seule | Hash/versions de l'objet audité identiques avant/après ; `NOT_EXECUTED` |
| `AC-031` | M2-03/11 | A2 tente merge, publish, delete ou priorité réservée | DENY et aucun effet externe ; `NOT_EXECUTED` |
| `AC-032` | M2-03/11 | Commande hors scope / wrong owner / mauvaise version | Refus sans événement métier de succès ; `NOT_EXECUTED` |
| `AC-033` | M2-07/11 | Même report/handoff reçu plusieurs fois, y compris après restart | Une seule opération logique ; contenu divergent = conflit ; `NOT_EXECUTED` |
| `AC-034` | M2-06/12 | G5 et approval nécessitent décision humaine séparée | Sans décision humaine, statut reste en attente ; `NOT_EXECUTED` |
| `AC-035` | M2-02/03/11 | Brief, list, export ou nouveau projet client/employeur hors mandat | Aucun identifiant, compte ou donnée privé divulgué ; `NOT_EXECUTED` |
| `AC-036` | M2-07/10 | Nouvelle session ouvre même WorkItem avec observations/brief/report/decision | Snapshot et handoff sourcés par base durable ; `NOT_EXECUTED` |
| `AC-037` | M2-09 | Projet non logiciel utilise même core sans gates G0-G7 | Projet créé et repris sans taxonomie Py*Kit forcée ; `NOT_EXECUTED` |

**Important** : la numérotation et le sens de ces critères proviennent de la V2. Les scénarios de tests et types de preuves de la colonne de droite sont des **propositions de mise en œuvre** et ne constituent pas des résultats d'exécution.

# 7. Stratégie de tests, sécurité et traitement des échecs

## 7.1 Tests contractuels / composants

- DTOs : round-trip versionné, champs obligatoires, types invalides, payload inconnu, dépassement taille, timezone, référence insuffisante, serialization stable.
- Mandat : droits hôte et mandat croisés, TTL/expiration, scope/owner, A2 interdit aux actions A4/A5, changement de policy entre émission et réception, usurpation de principal.
- Redaction : 2 scopes / 2 propriétaires dans le même scope / ressources enfants PRIVATE ; les counts, facettes, listes, exports et logs ne révèlent rien.
- Report : bon `brief_id`, `mandate_id`, `work_item_ref`, `target_reference` et empreinte ; mauvaise cible, mauvais scope et mauvaise révision rejetés ; pas de parsing d'une instruction contenue dans le report comme instruction exécutable.
- Idempotence : N retries même payload -> 1 report ; payload différent à même clé -> conflit ; crash avant commit -> 0 ; commit confirmé puis réponse perdue -> relecture/retour même id.
- Human gate : rapport annonçant `QUALIFIED` / `APPROVED` / `PUBLISHED` sans source ni décision humaine -> état métier et probant inchangés.
- Non-régression : 41 tests M0/M1 (baseline historique) restent exécutables et leurs invariants valides, même si le compte exact des tests évolue.

## 7.2 Tests E2E pilote / transport

Pour commencer : driver déterministe local `FakePythosAdapter`, sans requête réseau. La seconde étape peut utiliser un adapter Pythos réel **uniquement si une API stable et des autorisations sont disponibles**. Établir alors une matrice explicite des responsabilités : génération du report, identité du rapporteur, signature ou authentification du transport, retry, timeout, quota et confidentialité des données.

Un timeout d'appel à l'agent **ne prouve pas qu'il n'a rien exécuté**. Traiter les résultats distants comme potentiellement incertains et les effets externes comme non transactionnels avec SQLite. Une action distante sensible nécessite un mécanisme de confirmation et un mandat approprié.

## 7.3 Erreurs M2 candidates

| Famille | Sémantique | Comportement sûreté |
|---|---|---|
| `UnsupportedContractVersion` | DTO/report version non gérée | Refus sans effet ; version supportée explicitée sans secret |
| `MandateInvalid` / `MandateExpired` / `MandateRevoked` | Autorité absente ou non courante | Refus ; ne jamais fallback vers allow-all |
| `ScopeDenied` / `ResourceNotVisible` | Ressource interdite ou hors scope | Erreur publique non-divulgante, pas de compte/identifiant |
| `ReportCorrelationConflict` | Cible/WorkItem/mandat/révision ne correspondent pas | Rejet atomique et trace d'audit protégée |
| `IdempotencyConflict` | Même identifiant de report, payload divergent | Conflit, sans overwrite |
| `ExternalExecutionUnknown` | Timeout/erreur de transport ambiguë | Ne pas réexécuter une action sensible à l'aveugle |
| `EvidenceUnverified` | Source indisponible, obsolète ou non contrôlée | Évaluation `UNKNOWN/DECLARED` ; jamais PASS automatique |
| `ApprovalRequired` | Transition, publication ou gate réservés | Proposition/attente d'une décision humaine réelle |

Ces noms sont proposés et doivent être rapprochés du modèle d'erreur M0/M1, sans créer de doubles exceptions inutiles.

# 8. ADR M2 à préparer avant le premier code

| ADR candidat | Décision à prendre | Orientation recommandée |
|---|---|---|
| `ADR-M2-01` | Structure/versions `OperatingBriefDTO` et `ExecutionReportDTO` | DTOs externes, pas d'entity Pythos dans le core |
| `ADR-M2-02` | Mandat A0-A5, scope, expiration, révocation et translation vers permissions | Autorité vérifiée au runtime via TrustedHost, deny-default |
| `ADR-M2-03` | Journal de report, idempotence et migration SQLite 0003 | Inbox append-only scoped, contraintes uniques et fingerprint |
| `ADR-M2-04` | Vérification indépendante et promotion d'état | Deux commands distinctes : soumettre puis vérifier / faire approuver |
| `ADR-M2-05` | `WorkItemRef` / frontière `Task` et `RegistryEntry` | Stable ref adapter, pas de nouvel Aggregate Root M2 |
| `ADR-M2-06` | Transport Pythos / contrat d'exécution externe | FakeAdapter d'abord, réel optionnel derrière port |
| `ADR-M2-07` | Politique read-only `AUDIT` et effets collatéraux externes | Aucun write source audité ; journal séparé autorisé |
| `ADR-M2-08` | Classification/rétention des reports et suppression sous mandat | Données synthétiques, metadata minimale, privacy by design |

**Statut de tous ces ADR : `PROPOSED`**. Leur présence dans ce plan n'est pas leur adoption. Revoir les choix d'architecture M1 déjà approuvés **pour le pilote local seulement** avant d'élargir les autorisations.

# 9. Premier vertical slice détaillé : VS-M2-01

**But** : générer un brief réellement autorisé, sans dépendance Pythos, sans muter une Task, et avec un `mandate_id` vérifiable. C'est le point d'entrée concret recommandé.

### Préconditions

- Disposer d'un `Project` et d'une `Task` synthétiques sous SQLite avec un `VerifiedActor` M1.
- Le propriétaire de la ressource et/ou un partage explicite a été autorisé, et un mandat limité `AUDIT/A0` ou `A1` est émis par le TrustedHost.
- La cible identifie une référence exacte ; pour un audit de code, un SHA réel sur une fixture est préférable à un nom de branche mouvant.

### Given / When / Then

```gherkin
Scenario: un brief autorisé conserve le moindre privilège
  Given deux projets P1 et P2 dans le même scope, propriétaires différents
  And un acteur habilité à lire P1 sans partage sur P2
  And un mandat AUDIT A0 limité à la Task T1 de P1 et au SHA X
  When BuildAuthorizedOperatingBrief est exécuté pour T1
  Then le brief contient son WorkItemRef, son mandat, le SHA X et ses critères
  And il ne contient ni P2 ni ses observations ou preuves privées
  And la création du brief ne modifie aucun ProjectStatus ni TaskStatus

Scenario: mandat expiré ou scope non autorisé
  Given un mandat expiré ou visant un autre scope
  When BuildAuthorizedOperatingBrief est appelé
  Then l'opération est refusée sans révélation de ressource
  And aucun rapport, décision ni événement métier de succès n'est créé
```

### DoD VS-M2-01

- [ ] DTO versionné avec tests de sérialisation/validation et schéma documenté.
- [ ] Protocole de mandat et contrôle d'expiration vérifiés avec horloge injectée.
- [ ] Projection scope/owner/PRIVATE testée avant agrégation et sérialisation.
- [ ] Aucun import Pythos dans `domain.py`, et le package M1 fonctionne sans M2.
- [ ] 41 tests hérités M0/M1 passent ; tests M2 positifs et négatifs ajoutés.
- [ ] Typage strict et build Python 3.12/3.13 sur SHA exact, aucune donnée privée réelle.
- [ ] Revue de sécurité et décision de passer à VS-M2-02, avec réserves explicites.

# 10. Deux pilotes M2 et critères de comparaison

## 10.1 Pilote P1 - Audit PySRMKit, référence exacte

- **Nature** : exercice de vérification de code/documentation **synthétique ou sur source explicitement publique et autorisée**.
- **Mode Pythos** : `AUDIT`, A0/A1 ; lecture de la référence exacte, aucun commit, merge, publication ou mutation de la source auditée.
- **Entrée** : brief v1 `target_reference=SHA`, permission scoped, liste d'AC et exclusions.
- **Sortie** : report v1 (observations, preuves vérifiables, incertitudes, risques, prochaine action recommandée) ; enregistrement dans le journal M2 du projet de pilotage.
- **Succès** : aucun effet métier implicite, aucun `QUALIFIED` indépendant non démontré, handoff persistant, SHA et scope corrects.

## 10.2 Pilote P2 - Projet non logiciel et politique distincte

- **Nature** : projet pédagogique ou organisation d'événement fictif, sans données de personnes réelles.
- **Mode** : `LEARNING` ou `AUDIT` selon mandat ; critères propres au projet, sans statuts de release logiciels.
- **Entrée** : brief lié à une tâche de planification et à une validation autorisée.
- **Sortie** : report, handoff et prochaine action reprenables ; aucun gate G0-G7 imposé.
- **Succès** : démontrer `AC-037`, scopes/policies différents, aucun pouvoir d'approbation déduit du mode.

## 10.3 Tableau comparatif attendu

| Dimension | Pilote P1 | Pilote P2 |
|---|---|---|
| Source de vérité | Repo/commit et registre M1 | Projet et décision métier M1 |
| Cible exacte | SHA d'une fixture autorisée | ID stable de tâche / version du projet |
| Mandat | AUDIT A0/A1 read-only | LEARNING/AUDIT avec restrictions propres |
| Type de preuve | Référence commit, CI ou test reproduit | Critères et observations du scénario synthétique |
| Gate | G5 réservé, non auto-accordé | Critère du projet, sans G0-G7 obligatoire |
| Risque majeur | Confondre report et qualification | Imposer une taxonomie logicielle universelle |

# 11. Gate Q-M2, rapport et décision humaine

## 11.1 Préconditions d'entrée

- [ ] Une référence SHA `main` gelée et une base de code M1 identifiée.
- [ ] Le périmètre expérimental M2 et les ressources autorisées sont formellement mandatés.
- [ ] ADR-M2-01 à 04 arbitrés avant code critique ; autres ADR avant pilote concerné.
- [ ] Le TrustedHost et les contrôles owner/scope/PRIVATE sont conservés et testés.
- [ ] Politique de traitement des données et des exports, sans secrets dans les reports.
- [ ] Absence de licence toujours traitée comme limite de publication, pas comme autorisation implicite.

## 11.2 Critères du GO expérimental proposé

- [ ] **11/11 critères AC-027..037** évalués explicitement sur SHA, environnement et date, avec preuves visibles et réserves précises.
- [ ] Mode `AUDIT` sans mutation métier de l'objet audité et pas d'effet externe interdit.
- [ ] Deux scopes / deux owners dans un scope / permissions plus restrictives pour enfants ; aucune fuite dans brief, report, historique, counts et export.
- [ ] Mandats expirés, A2/A4/A5 hors autorité, mauvaises révisions et payloads malformés refusés.
- [ ] Idempotence démontrée sous retry, redémarrage et conflit de payload.
- [ ] Distinction prouvée entre déclaration Pythos, Observation M1, EvidenceRef, Assessment et Approval humaine.
- [ ] Reprise nouvelle session sans mémoire de conversation et avec provenance complète.
- [ ] Deux pilotes hétérogènes démontrés, dont un non logiciel sans gates G0-G7.
- [ ] Aucun import Pythos obligatoire par le core ; M0/M1 et wheel fonctionnels sans adapter externe.
- [ ] Revue de sécurité indépendante du rapport Pythos et décision humaine enregistrée.

## 11.3 Cas de NO-GO immédiat

- Un report élève automatiquement le statut métier/probant, ou délivre un `PASS` sans preuve source.
- Un agent utilise A0-A5 pour contourner la policy M1 ou une permission externe.
- Une fusion, publication, suppression ou approbation A4/A5 non autorisée se produit.
- Un brief/report/handoff divulgue un projet hors scope, un autre owner sans partage ou une preuve privée.
- Un retry du report produit une deuxième transition ou des actions dupliquées.
- Une reprise dépend de la mémoire conversationnelle plutôt que de références durables M1.

## 11.4 Verdicts distincts

| Décision | Ce qu'elle autorise | Ce qu'elle n'autorise pas |
|---|---|---|
| `Q-M2 = GO (local pilot)` | Utiliser le contrat M2 optionnel sur fixtures synthétiques et scopes autorisés | PyPI, production, données réelles sensibles |
| `Q-M2 = CONDITIONAL GO` | Poursuivre avec conditions écrites, owners et date de levée | Fermer automatiquement les risques |
| `Q-M2 = NO-GO` | Uniquement la remédiation documentée | Intégration automatique ou promotion du statut |

**Statut au 2026-11-03 : `NOT_ASSESSED`**. Ce document ne constitue ni un mandat de développement M2 ni une évaluation des critères AC-027..037.

# 12. Risks, mitigations et owners de travail

| Risque | Conséquence | Mitigation et preuve attendue | Responsable proposé |
|---|---|---|---|
| Confusion Pythos / core | Statuts métier mutés à tort | Adapter optionnel, tests sans Pythos, pas d'import domain | Maintainer architecture |
| Usurpation de mandat / expiration | Escalade d'autorité | Principal vérifié, TTL, révocation, intersection permissions | Maintainer sécurité |
| Injection par report | Appel de tool, commande ou promotion non voulue | Report traité comme donnée non fiable ; allowlist de Commands, validation stricte | Maintainer sécurité |
| Fuite cross-owner et cross-scope | Divulgation du registre | Rejouer régression M1, redaction avant sérialisation | Maintainer sécurité |
| Preuve périmée | Faux `QUALIFIED` | Pin SHA, vérification source et `UNKNOWN` si indisponible | Reviewer indépendant |
| Retries et commit incertain | Double action et double handoff | Unique indexes, fingerprint et relecture après incertitude | Maintainer persistance |
| Coûts / données envoyées à LLM | Secret ou budget hors contrôle | FakeAdapter par défaut, aucun envoi réel sans mandat d'export et budget | Responsable de projet |
| Érosion de la neutralité non logicielle | Gates G0-G7 imposés | Pilote non logiciel, non-régression AC-037 | Reviewer métier |
| Licence non décidée | Distribution prématurée | Aucune publication ni tag sans décision propriétaire | Propriétaire humain |
| Transport Pythos non contractualisé | Intégration prétendue fonctionnelle | Marquer adapter réel `UNVERIFIED` tant qu'une API exacte n'existe pas | Maintainer intégration |

# 13. Livrables M2 et handoff attendu

1. `OperatingBriefDTO v1` et `ExecutionReportDTO v1` : JSON schema ou validation Python, champs obligatoires et exemple sûr.
2. Registre/port de mandats avec tests d'autorité et journal d'audit.
3. Service d'ingestion idempotent et persistance append-only/migration SQLite (si ADR validé).
4. Projection filtrée des données M1 et couche de lecture du `WorkItemRef`.
5. Workflows de vérification indépendante et demande d'approbation humaine.
6. FakeAdapter déterministe et, facultativement, adapter Pythos réel distinct avec test de contrat.
7. Deux pilotes synthétiques et suite de tests hostiles, concurrence/idempotence/restart.
8. Rapport `Q-M2` et matrice `AC-027..037`, SHA/CI, limites, risques et owner du prochain pas.
9. Documentation d'apprentissage : DDD vs Agent Workflow, Port/Adapter, DTO/ACL, CQRS, idempotence, authority vs capability, contract testing, avec alternatives et trade-offs.

Le handoff final conserve **la prochaine action sûre**, même si celle-ci est `NONE_WITH_REASON`, et garde visibles les informations absentes, périmées ou invérifiables.

# 14. Actions proposées à la suite de ce document

1. Revue humaine du plan et confirmation du **périmètre d'expérimentation** : PySRMKit synthétique + projet non logiciel synthétique, sans données réelles.
2. ADR-M2-01/02/03/04 : trancher DTO, mandat, idempotence, vérification humaine ; enregistrer les alternatives et les risques.
3. Vérifier la compatibilité effective des ports M1 avec la représentation de `WorkItemRef`, sans introduire un nouvel AR arbitraire.
4. Ouvrir la tranche M2-A et son premier vertical slice **uniquement après mandat explicite de développement**.
5. Établir les fixtures, tests négatifs et la baseline 41 tests M0/M1 sur SHA.
6. Construire M2-A, puis M2-B, puis M2-C, en démontrant chaque gate et en conservant l'optionnalité de Pythos.
7. Soumettre le rapport de qualification `Q-M2` avec décision humaine et risques résiduels, sans fusion ni publication automatiques.

---

# Annexe A - Registre des WorkItems M2

| ID | Tranche | Livrable | Référence de recette |
|---|---|---|---|
| `M2-01` | M2-A | OperatingBriefDTO versionné | AC-027 |
| `M2-02` | M2-A | Contexte autorisé et filtré | AC-027, AC-035 |
| `M2-03` | M2-A | Mandat, expirations et permissions | AC-031, AC-032, AC-035 |
| `M2-04` | M2-B | ExecutionReportDTO versionné | AC-028 |
| `M2-05` | M2-B | Réception et historisation sans mutation | AC-029, AC-030 |
| `M2-06` | M2-B | Workflow de vérification/approval | AC-034 |
| `M2-07` | M2-B | Idempotence ingestion/handoff | AC-033 |
| `M2-08` | M2-C | Audit PySRMKit limité | AC-030, AC-031 |
| `M2-09` | M2-C | Projet non logiciel | AC-037 |
| `M2-10` | M2-C | Reprise nouveau processus | AC-036 |
| `M2-11` | M2-C | Tests négatifs de mandat/scope/merge | AC-029 à AC-035 |
| `M2-12` | M2-C | Qualification AC et gate | AC-027 à AC-037 |

# Annexe B - Checklist de revue du plan

- [ ] Les frontières M0/M1/Pythos sont explicites et aucun statut probant n'est promu par un report.
- [ ] Les 12 WorkItems et 11 AC sont présents sans extrapolation du statut d'exécution.
- [ ] Les conditions de sécurité reflètent le correctif M1 owner/partage et les règles du mandat Pythos.
- [ ] Le pilote `AUDIT` reste en lecture seule sur l'objet audité.
- [ ] L'API Pythos réelle est traitée comme optionnelle/non vérifiée, non inventée.
- [ ] L'absence de licence et de sécurité de production reste une restriction explicite.
- [ ] La première tranche VS-M2-01 dispose d'un DoD testable et d'un refus par défaut.
- [ ] Tous les résultats proposés restent `NOT_EXECUTED` jusqu'aux tests sur SHA exact.
- [ ] Le gate Q-M2 n'est pas confondu avec celui de M1 ni avec une release PyPI.

# Annexe C - Convention Software Design & Learning pour M2

Chaque changement M2 doit contenir dans sa PR ou son dossier de décision : **problème réel**, **termes métier**, **invariant ou contrat**, **option simple retenue**, **alternatives**, **dette/risque**, **tests positifs et négatifs**, **preuve sur SHA** et **prochaine décision humaine**. Patterns pertinents : DDD/Bounded Context, Anti-Corruption Layer, Ports & Adapters, DTO, CQRS, Idempotent Consumer, Policy Object, UoW et Contract Testing. Ne pas introduire ces patterns si une simple fonction suffit et protège déjà le contrat.

**Dernier contrôle d'honnêteté** : ce plan a été rédigé à partir des spécifications sources et du code M1 observé. Aucune capacité d'intégration Pythos, aucun ADR M2 et aucun AC-027..037 n'a été implémenté ou exécuté dans le cadre de sa création.
