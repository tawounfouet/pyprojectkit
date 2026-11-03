# R0-02 - Audit direct des sources V1 et V2

> Date : 2026-11-03
>
> Statut : DIRECT_SOURCE_REVIEW / DECISIONS_PENDING
>
> Scope : sources originales V1 retrouvées, documents de proposition V2 du 2 novembre et roadmap/plan bootstrap.
>
> Aucune source V1 n'est automatiquement promue en baseline de code ou d'API. Aucun ADR n'est accepté par cet audit.

## 1. Corpus retrouvé et provenance

Les **12 documents V1 originaux** suivants ont été retrouvés dans la Library du projet et leurs textes ont été inspectés. Les V2 sont les documents remis pour le chantier R0.

| Famille | Original V1 consulté | Proposition V2 consultée |
|---|---|---|
| Besoin | `00_PYPROJECTKIT_DEFINITION_DU_BESOIN.md` | `00_PYPROJECTKIT_DEFINITION_DU_BESOIN_V2.md` |
| Requirements | `00_PYPROJECTKIT_REQUIREMENTS_ANALYSIS.md` | `00_PYPROJECTKIT_REQUIREMENTS_ANALYSIS_V2.md` |
| Vision | `00_PYPROJECTKIT_PROJECT_VISION_AND_ARCHITECTURE.md` | `00_PYPROJECTKIT_PROJECT_VISION_AND_ARCHITECTURE_V2.md` |
| Objets | `04_PYPROJECTKIT_OBJETS_METIERS.md` | `04_PYPROJECTKIT_OBJETS_METIERS_V2.md` |
| DDD | `05_PYPROJECTKIT_ENTITIES_AND_VALUE_OBJECTS.md` | `05_PYPROJECTKIT_ENTITIES_AND_VALUE_OBJECTS_V2.md` |
| ERD | `06_PYPROJECTKIT_DOMAIN_RELATIONSHIPS_AND_ERD.md` | `06_PYPROJECTKIT_DOMAIN_RELATIONSHIPS_AND_ERD_V2.md` |
| Règles | `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md` | `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md` |
| Application | `08_PYPROJECTKIT_COMMANDS_QUERIES_AND_USE_CASES.md` | `08_PYPROJECTKIT_COMMANDS_QUERIES_AND_USE_CASES_V2.md` |
| Events | `09_PYPROJECTKIT_DOMAIN_EVENTS_CATALOG.md` | `09_PYPROJECTKIT_DOMAIN_EVENTS_CATALOG_V2.md` |
| Persistence | `10_PYPROJECTKIT_REPOSITORIES_UNIT_OF_WORK_AND_PORTS.md` | `10_PYPROJECTKIT_REPOSITORIES_UNIT_OF_WORK_AND_PORTS_V2.md` |
| Errors | `11_PYPROJECTKIT_ERROR_MODEL_AND_FAILURE_SEMANTICS.md` | `11_PYPROJECTKIT_ERROR_MODEL_AND_FAILURE_SEMANTICS_V2.md` |
| Security | `12_PYPROJECTKIT_APPLICATION_SECURITY_AND_AUTHORIZATION.md` | `12_PYPROJECTKIT_APPLICATION_SECURITY_AND_AUTHORIZATION_V2.md` |

**Méthode** : comparaison des sections MVP, classifications, identifiants métier, catalogues et annexes V1/V2. Pour `07`, 144 identifiants V1 de règle/invariant ont été repérés dans les titres `##`, et 183 identifiants ont été repérés comme définitions inline dans le corps V2 ; ces nombres ne constituent pas une preuve d'équivalence sémantique et les références historiques en annexe ne remplacent pas les définitions actives.

Ce dossier ne publie pas les textes historiques complets dans le dépôt public. Les numéros de lignes ci-dessous sont ceux des fichiers sources consultés, pas des liens vers des fichiers actuellement présents sur GitHub.

## 2. Compatibilités établies par comparaison directe

| ID | Observation V1 (source) | Observation V2 (source) | Verdict documentaire |
|---|---|---|---|
| V1C-01 | 05 V1 §103 : `Project` et `Task` Aggregate Roots, `Milestone` Entity | 05 V2 §§8-11, 06 V2 §3.2 conservent ces frontières | CONSISTENT / DECISION STILL PROPOSED |
| V1C-02 | 06 V1 §95 : `Project 1 -> 0..N Task`, `Project 1 -> 0..N Milestone` | 06 V2 §11 : mêmes cardinalités | CONSISTENT ; le visuel bootstrap `1..*` est erroné |
| V1C-03 | 08 V1 : `PutProjectOnHold`, `MarkTaskReady` | 08 V2 reprend ces Commands mais mentionne `PauseProject` comme variante | COMPATIBLE IF V1 NAMES RETAINED |
| V1C-04 | 09 V1 §122 : `ProjectPutOnHold`, `TaskMarkedReady` | 09 V2 conserve ces noms dans le catalogue M0 ; `ProjectPaused` est une variante non arbitrée | COMPATIBLE IF V1 NAMES RETAINED |
| V1C-05 | 10 V1 §155 : `ProjectRepository`, `TaskRepository`, Readers, `UnitOfWork`, InMemory et EventBus ; Outbox ensuite | 10 V2 §§3,5,17 garde UoW explicite et Outbox conditionnelle | CONSISTENT STAGING |
| V1C-06 | 11 V1 §85 : refus métier, rollback, codes stables et absence d'événement de succès sur refus | 11 V2 ajoute issue inconnue de commit et sépare les axes de défaillance | ADDITIVE SEMANTICS, API UNAPPROVED |
| V1C-07 | 12 V1 §98 : `ActorContext`, `DefaultDeny`, rôles, scope, Command/Query authorization | 12 V2 §4 : identité fiable et contrôle fail-closed dès M0, IAM avancé différé | CONSISTENT SECURITY INTENT |
| V1C-08 | 07 V1 §77 : règles de cycle, graphe, jalons, affectation de base, dates, événements | 07 V2 §§8-16 reprend l'essentiel avec priorisation M0/M1/C3 | CAPABILITY PRESERVED, ID DRIFT BELOW |

## 3. Collisions d'identifiants confirmées : risque BLOCKING avant baseline 07 V2

Ces divergences sont **établies par lecture des deux textes**, même si l'annexe A du document 07 V2 rappelle les définitions historiques. Un identifiant réutilisé avec deux significations rendrait ambigu un test, un ADR, un rapport de conformité ou une migration.

| ID historique | Sens dans 07 V1 | Sens dans le corps 07 V2 | Remédiation PROPOSED |
|---|---|---|---|
| `BR-ASSIGN-001` | V1 §23, ligne 765 : assigner uniquement un membre admissible | V2 §12, ligne 318 : référence Task et acteur/membre résolubles dans le scope | Conserver le critère d'admissibilité et ajouter scope comme précondition, pas comme remplacement |
| `BR-ASSIGN-002` | V1 §23, ligne 771 : admissibilité déterminable par policy | V2 §12, ligne 319 : au plus un assigné actif M0 | **Conserver V1** sous `BR-ASSIGN-002` ; donner un **nouvel identifiant** à la limite d'assignés |
| `BR-ASSIGN-003` | V1 §23, ligne 783 : conserver `unassigned_at` après fin d'affectation | V2 §12, ligne 320 : ne pas contourner les états terminaux | **Conserver V1** ; introduire une nouvelle règle pour les états terminaux |
| `BR-DELIV-001` | V1 §20, ligne 713 : accepter uniquement si critères obligatoires satisfaits | V2 §11, ligne 309 : livrable rattaché à projet ou jalon identifiable | **Conserver V1** ; donner un ID distinct à l'appartenance du livrable |
| `BR-DELIV-002` | V1 ligne 719 : validation finale peut exiger `Approval` | V2 §11, ligne 310 : accepter si critères obligatoires satisfaits | **Conserver V1**, déplacer la règle de critères vers `BR-DELIV-001` |
| `INV-DATE-002` | V1 §56, ligne 1480 : période vide permise seulement si modèle l'autorise | V2 §12, ligne 327 : compatibilité sémantique des bornes temporelles | **Conserver V1** sous cet ID et créer un nouvel ID pour compatibilité des types de bornes |

**Important :** `BR-DELIV-001/002` et `BR-ASSIGN-001/002/003` dans **l'annexe A de 07 V2** restituent les anciennes significations. La contradiction est interne au document 07 V2 lui-même (corps vs annexe) et donc plus forte qu'un simple renommage interversions.

## 4. Drift des critères d'acceptation historiques

La V1 Requirements §34 et la V2 Requirements §34 utilisent `AC-001..AC-012`, mais certaines formulations évoluent :

| AC | V1 | V2 | Traitement candidat |
|---|---|---|---|
| `AC-001` | installer **et** créer un projet sans infrastructure optionnelle | importer et créer sans web/réseau | **Préserver un test d'installation isolée** en plus du smoke import |
| `AC-005` | cycles rejetés **ou** explicitement détectés | cycles détectés **et** rejetés | Renforcement souhaitable, à faire approuver et tester |
| `AC-010` | Core sans FastAPI/Django/SQLAlchemy **ni driver DB** | Core sans FastAPI/Django/SQLAlchemy/Pythos/PyAgentsKit | Conserver le test `no_db_driver_import` explicitement |
| `AC-012` | tests unitaires et de contrat passent **en CI** | tests reproductibles en environnement isolé | **Tester les deux** : environnement isolé et CI verte sur SHA exact |

Les capacités V1 ne doivent pas être retirées par une modification de phrase dans la V2. La roadmap 13 et le bootstrap 14 prévoient eux-mêmes package installable et CI, ce qui soutient leur maintien.

## 5. Catégories additionnelles et limites

- `M1` ajoute `ProjectRegistryEntry`, contexte, preuves, observations, snapshots et handoffs ; ces objets ne requalifient pas rétroactivement les Domain Events V1.
- `M2` ajoute les DTO Pythos en adapter optionnel, pas comme Aggregate métier.
- `C3` maintient les domaines historiques Agile, ressources, budget, risques, PMO sans les mettre de force dans M0.
- Les exceptions V1 et signatures de ports n'ont **aucune API déjà publiée vérifiée** dans le dépôt ; la compatibilité actuelle est documentaire, pas binaire.
- Les choix de licence, version Python supportée, contrôle des branches et matrice CI demeurent à décider/vérifier.

## 6. Plan correctif proposé

1. Émettre une **proposition de patch du document 07 V2**, conservant les codes V1 et ajoutant des codes V2 non conflictuels pour les nouveaux comportements. Aucun renumérotage d'historique sans crosswalk.
2. Conserver les noms V1 de Commands et Domain Events comme **candidats canoniques** jusqu'à ADR explicite. Ne pas créer d'alias publics non requis.
3. Renforcer `R0-07_M0_ACCEPTANCE_TRACEABILITY.md` avec installation isolée, absence de drivers et CI sur SHA.
4. Relire l'impact des collisions dans 08 (Commands), 09 (Events), 10 (repositories), 11 (errors), 12 (security) et les futures signatures des tests.
5. Faire approuver les changements de contrat/identifiant et classer les décisions avant `Q-R0`.

## 7. Critères de clôture de cette revue

- [x] Retrouver et lire les 12 documents V1 originaux.
- [x] Confronter le MVP de V1 aux principales clauses M0 de V2.
- [x] Identifier et tracer des collisions concrètes d'identifiants, sans les masquer par une annexe.
- [ ] Statuer sur les six collisions et le renforcement des AC avec décisions humaines.
- [ ] Mettre à jour la V2 normative après arbitrage et relire toutes les références impactées.
- [ ] Vérifier que le corpus accepté est versionné dans une baseline Git.

**Verdict : REVIEW REQUIRED, pas GO.** La recherche et la comparaison des sources ont progressé ; elles ne se substituent pas à l'approbation ou aux tests.

## Actualisation du 3 novembre 2026 : décision obtenue

Les recommandations de préservation des codes historiques ont été approuvées par le propriétaire sous [D-SEM-01](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md) ([trace](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491)). Les constats et réserves initiaux de ce rapport restent conservés comme **historique de l'audit**, tandis que la copie corrigée de 07 V2 se trouve dans `docs/specifications/review/` sur la PR #4. L'acceptation du choix de compatibilité ne termine ni l'audit de toutes les règles ni le gate `Q-R0`.
