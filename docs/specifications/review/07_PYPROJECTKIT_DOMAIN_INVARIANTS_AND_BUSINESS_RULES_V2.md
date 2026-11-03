# 07 - Invariants du domaine et règles métier - PyProjectKit - V2

> **Document canonique ciblé** : `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md`  
> **Livrable de révision** : `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md`  
> **Projet** : PyProjectKit  
> **Type** : Spécification métier normative proposée, à consolider avec les documents 08 à 12  
> **Version documentaire** : `2.0.0` (proposée)  
> **Date** : 2 novembre 2026  
> **Langue** : français, termes DDD et Python conservés lorsque utiles  
> **Statut** : `REVIEW` - **COPIE CANDIDATE R0 / CORRECTION PROPOSÉE, NON APPROUVÉE**
> **Origine** : spécification V2 fournie le 3 novembre 2026 ; correction locale ciblée de six identifiants historiques V1/V2.
> **Décision liée** : `D-SEM-01` - `PENDING HUMAN APPROVAL` ; aucune modification de la baseline canonique.  
> **Portée** : noyau M0, registre et continuité M1, contrats d'intégration Pythos M2, domaines avancés C3  
> **Convention transversale** : `PYKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md`  
> **Règle d'interprétation** : spécifier une règle ne prouve ni son implémentation, ni sa qualification, ni son adoption en production.

---

## Guide de lecture

| Partie | Objectif | Statut de livraison ciblé |
|---|---|---|
| 1 à 7 | Définitions, principes, responsabilités, représentation des erreurs | Commun |
| 8 à 16 | Projet, tâche, dépendance, jalon, dates, transaction | M0 |
| 17 à 25 | Scope, registre, provenance, preuves, snapshots et reprise | M1 |
| 26 à 29 | Décisions, approbations, gouvernance et confidentialité | M1 / C3 |
| 30 à 32 | Collaboration optionnelle avec Pythos, cohérence et événements | M2 / Commun |
| 33 à 40 | Catalogue historique avancé, tests, scénarios, traçabilité et décisions | C3 / Qualité |
| Annexes | Conservation des identifiants V1, correspondance document 06, cas de tests | Migration documentaire |

**Important** : les préfixes `INV-*` désignent des invariants non contournables dans leur périmètre ; `BR-*` désigne une règle métier ou une politique potentiellement configurable ; `APP-*` une précondition applicative ou transactionnelle ; `SEC-*` une protection à faire respecter par l'application et ses adapters. Ces catégories ne sont **pas interchangeables**.

---

# 1. Objet et objectif de la révision

Le présent document répond à la question : **quelles propriétés doivent rester vraies, quelles opérations sont autorisées et comment échouer sans produire d'états trompeurs ?**

La V1 définissait un socle de règles substantiel : identité, cycles de vie Project et Task, dépendances acycliques, jalons, ressources, Agile, RAID, gouvernance, finances, portefeuille, idempotence, événements et transactions. La V2 **conserve ces responsabilités**, tout en précisant ce qui est universel, ce qui est optionnel et ce qui est spécifique à notre manufacture Py*Kit.

Cette révision prend en compte les nouveaux objets proposés dans les documents 04, 05 et 06 V2 : `ContextScope`, `ProjectRegistryEntry`, `SubjectReference`, `Claim`, `Observation`, `EvidenceRef`, `VerificationAssessment`, `ProjectSnapshot`, `NextAction`, `HandoffRecord`, `PortfolioDecision` et `ReconciliationCase`.

Elle ne doit pas :

- déduire une architecture SQL des seuls invariants métier ;
- créer artificiellement un Aggregate Root par objet du catalogue ;
- rendre Pythos obligatoire pour utiliser PyProjectKit ;
- imposer des gates de release logicielle à tous les projets personnels ou clients ;
- inventer des preuves, des niveaux de maturité ou des décisions humaines ;
- transformer une règle d'autorisation en simple validation d'Entity ;
- considérer ce document comme une attestation de tests exécutés.

# 2. Sources de référence, priorité et statut

| Source | Ce qu'elle établit | Limite |
|---|---|---|
| `00_PYPROJECTKIT_DEFINITION_DU_BESOIN_V2.md` | Problème et valeur recherchée | Ne décide pas les transitions |
| `00_PYPROJECTKIT_REQUIREMENTS_ANALYSIS_V2.md` | Exigences, niveaux de priorité, cas d'usage | N'est pas une preuve d'exécution |
| `00_PYPROJECTKIT_PROJECT_VISION_AND_ARCHITECTURE_V2.md` | Frontières cibles, couches, intégration Pythos | Architecture encore proposée |
| `04_PYPROJECTKIT_OBJETS_METIERS_V2.md` | Vocabulaire et familles d'objets | N'impose pas de classes |
| `05_PYPROJECTKIT_ENTITIES_AND_VALUE_OBJECTS_V2.md` | Classification DDD candidate et ownership | Décisions non approuvées |
| `06_PYPROJECTKIT_DOMAIN_RELATIONSHIPS_AND_ERD_V2.md` | Relations, cardinalités, contraintes candidates | Ne fixe pas une migration SQL |
| `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md` (V1) | Identifiants et règles historiquement proposés | Certaines options sont désormais différées |
| `00_PYTHOS_VISION_AND_OPERATING_MODEL_.md` | Mandat, modes, niveaux A0-A5 et gates du compagnon | S'applique à Pythos, pas universellement aux projets |
| `PYKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md` | Principes DDD, Evidence Before Status, choix progressifs | N'atteste pas les dépôts |
| `PYSRMKIT_SOFTWARE_DESIGN_LEARNING_OVERLAY.md` | Exemple de spécialisation et de qualification sur référence exacte | Ne transfère pas ses invariants fournisseur à ce domaine |

**Règle documentaire** : à identifiant égal, la V2 détaille ou spécialise le sens de la V1. Une incompatibilité matérielle nécessite une décision explicitement documentée avant implémentation. Les identifiants provisoires `INV-REL-*` du document 06 sont rapprochés en annexe B ; on ne crée pas deux obligations concurrentes pour le même invariant.

# 3. Vocabulaire normatif et sémantique des règles

| Terme | Définition | Exemple |
|---|---|---|
| `Invariant` | Propriété obligatoire de l'état valide dans une frontière déterminée | Une tâche ne s'auto-référence pas |
| `Précondition` | Condition exigée avant d'accepter une commande | Projet actif pour démarrer une tâche |
| `Postcondition` | Résultat garanti après réussite de l'opération | Date réelle du démarrage renseignée |
| `Guard` | Contrôle empêchant une transition non autorisée | DONE ne revient pas à IN_PROGRESS sans use case |
| `Policy` | Règle variable sur un axe de personnalisation explicite | Critères de clôture selon le type de projet |
| `Authorization` | Décision d'accès pour un sujet, une action et une portée | Qui peut accepter un livrable ? |
| `Evidence` | Référence ou matériau permettant d'évaluer une affirmation | Test exécuté à un commit donné |
| `Observation` | Constat daté, avec source, portée et limites | CI signalée verte à une date |
| `VerificationAssessment` | Résultat explicite d'une méthode de vérification | PASS sur une suite déterminée |
| `Approval` | Acte habilité d'acceptation, distinct des résultats techniques | Validation de release |
| `Snapshot` | Vue historisée d'un état connu à un instant | Reprise après interruption |
| `Read Model` | Projection calculée, éventuellement conservée | Registre, prochaine action |

**Portée** : une règle peut être `LOCAL` (entité/VO/agrégat), `CROSS_AGGREGATE`, `APPLICATION`, `SECURITY` ou `EXTERNAL`. La responsabilité de son enforcement dépend de cette portée ; aucune règle inter-agrégats n'exige par principe de charger tout le graphe dans `Project`.

**Priorités** : `MUST M0`, `MUST M1`, `MUST M2` (quand le module optionnel est activé), `SHOULD`, `DEFERRED C3`. Une politique avancée ne devient pas obligatoire par sa seule présence dans le document.

# 4. Principes directeurs

1. **Problem Before Pattern** : la pression métier précède l'abstraction.
2. **Domain Before Framework** : les invariants vivent dans le domaine, pas uniquement dans Pydantic, Django ou une contrainte SQL.
3. **One truth, one owner** : le propriétaire d'une vérité est identifié par type d'information et périmètre.
4. **Evidence Before Status** : aucune promotion probante sans références et critères adéquats.
5. **Exact Reference Before Qualification** : un état de CI observé ne qualifie pas implicitement tous les commits.
6. **Unknown is not success** : source inaccessible, preuve manquante et résultat partiel restent explicites.
7. **Reversible and explainable change** : les mutations significatives disposent d'une raison, d'un auteur et d'une référence.
8. **Security Before Aggregation** : toute consolidation inter-projets est filtrée selon les droits effectifs.
9. **Agent is not an authority** : Pythos conseille ou exécute sous mandat, sans s'attribuer une approbation.
10. **Simple Before General** : WorkItem, Workspace, Portfolio et Gate ne deviennent pas tous des agrégats obligatoires.

# 5. Structure des identifiants et matrice d'enforcement

| Famille | Préfixes | Enforced by | Niveau |
|---|---|---|---|
| Primitives | `BR-GEN`, `INV-DATE`, `INV-MONEY`, `INV-VERSION` | VO / Aggregate / application | M0 + C3 |
| Projet | `INV-PROJ`, `BR-PROJ`, `BR-PROJ-CLOSE` | Project + ProjectClosurePolicy | M0 |
| Travail | `INV-TASK`, `BR-TASK`, `INV-SUBTASK` | Task + TaskStartPolicy | M0 |
| Dépendances | `INV-DEP`, `BR-DEP` | Graphe + service applicatif transactionnel | M0 |
| Jalon/livraison | `INV-MILE`, `BR-DELIV` | Project/Milestone + policy | M0 / C3 |
| Contexte et registre | `INV-CTX`, `INV-REG`, `BR-REG` | Application + projection | M1 |
| Sources et assertions | `INV-SRC`, `INV-CLAIM`, `INV-OBS`, `INV-EVID` | VO / store historique + ingestion | M1 |
| Vérification | `INV-VER`, `BR-VER`, `INV-REC` | vérificateur + historique | M1 |
| Continuité | `INV-SNAP`, `INV-NEXT`, `INV-HAND` | projection + stores historiques | M1 |
| Gouvernance | `INV-DEC`, `BR-APPROVAL`, `BR-PORT` | gouvernance / policy / autorisation | M1 / C3 |
| Collaboration Pythos | `BR-PYTHOS`, `APP-PYTHOS` | adapter + use case autorisé | M2 |
| Sécurité et événements | `SEC-*`, `BR-EVT`, `BR-IDEMP` | application / adapters / UoW | Selon module |

Le *nom des exceptions Python* n'est pas imposé ici. Le document 11 devra consolider un catalogue d'erreurs publiques stable, distinct des exceptions internes des frameworks.

# 6. Invariants fondamentaux réutilisés de la V1

| ID | Règle conservée | Portée | Priorité |
|---|---|---|---|
| `BR-GEN-001` | Toute modification significative passe par une opération métier contrôlée, jamais par mutation libre des attributs | Domain | M0 |
| `BR-GEN-002` | Une Entity conserve une identité stable pendant son cycle de vie | Domain | M0 |
| `BR-GEN-003` | Les VO sont immuables et comparés par valeur | Domain | M0 |
| `BR-GEN-004` | Une référence inter-Aggregate emploie un ID typé et non un objet interne mutable | Domain | M0 |
| `BR-GEN-005` | Les périodes requièrent `start <= end` lorsque les deux bornes existent | VO | M0 |
| `BR-GEN-006` | Les instants absolus comportent un timezone/offset explicite | VO | M0 |
| `BR-GEN-007` | Un montant financier ne vaut qu'avec une devise explicite | VO | C3 |

## 6.1 Identités et temporalité

- `INV-GEN-001` (nouveau) : les identités internes ne sont pas déduites automatiquement des identifiants d'une source externe ; les mappings requièrent leur contexte.
- `INV-GEN-002` (nouveau) : les identifiants sérialisés et clés de corrélation ne peuvent pas changer de sujet ou de portée lors d'un rejeu.
- `INV-GEN-003` (nouveau) : `occurred_at`, `observed_at`, `recorded_at`, `verified_at`, `captured_at` et `effective_at` désignent des notions différentes, non substituables silencieusement.
- `BR-GEN-008` (nouveau) : les opérations testables reçoivent une horloge injectée ou un instant explicite, et ne cachent pas un `now()` non maîtrisé dans les règles.
- `APP-GEN-001` (nouveau) : tout import ou mutation inter-systèmes doit expliciter source, cible, périmètre et version ou date de référence.

### Tests candidats

```text
test_entity_identity_is_stable_after_rename
test_utc_offset_is_required_for_absolute_timestamp
test_source_identifier_cannot_silently_replace_project_id
test_observation_time_cannot_replace_business_effective_time
```

# 7. Modèle d'échec, invariants et absence d'effet

Un échec de guard ou de précondition garantit **l'absence de mutation métier réussie**. Une commande peut produire un journal technique de refus sans produire d'événement métier de succès.

| Type de rejet | Sens métier | Traduction cible indicatrice |
|---|---|---|
| Transition illégale | Statut source incompatible | `InvalidStateTransition` |
| Référence inconnue | Projet/tâche/jalon non résolu dans le scope | `NotFound` ou refus non révélateur |
| Dépendance illégale | Cycle, auto-dépendance ou prérequis insatisfait | `DependencyViolation` |
| Version obsolète | Concurrence optimistic lock | `Conflict` |
| Politique non satisfaite | Clôture, acceptation, gate | `PolicyRejected` spécialisé |
| Données probantes insuffisantes | Qualification non établie | `UNKNOWN` / refus d'élévation |
| Accès interdit | Mandat ou permission absent | `AccessDenied` côté application |
| Source indisponible | Référence non consultable | `UNAVAILABLE` ou erreur d'intégration |
| Ambiguïté non résolue | Plusieurs mappings, versions, candidats | `AmbiguousReference` / réconciliation |

`NOT_FOUND`, `FORBIDDEN`, `STALE`, `UNKNOWN`, `FAILED`, `BLOCKED` et `REJECTED` ne sont pas synonymes. La traduction publique dépend des obligations de non-divulgation et sera contractualisée dans `11` et `12`.

# 8. Aggregate `Project` : invariants et cycle M0

## 8.1 Invariants hérités

| ID | Règle stricte | Test attendu |
|---|---|---|
| `INV-PROJ-001` | Un `Project` possède un `ProjectId` valide et stable | Création invalide refusée |
| `INV-PROJ-002` | Son nom métier ne peut pas être vide après normalisation de validation | Chaîne blanche refusée |
| `INV-PROJ-003` | Un responsable métier identifié est requis pour un projet géré | Absence d'owner refusée |
| `INV-PROJ-004` | `planned_start_date <= planned_end_date` si les deux existent | Dates inversées refusées |
| `INV-PROJ-005` | `actual_start_date <= actual_end_date` si les deux existent | Dates inversées refusées |
| `INV-PROJ-006` | `ACTIVE` implique une date réelle de début | État impossible refusé |
| `INV-PROJ-007` | `COMPLETED` implique une date réelle de fin | État impossible refusé |
| `INV-PROJ-008` | `CANCELLED` interdit le démarrage ordinaire | Start refusé après annulation |

La V1 proposait `DRAFT -> PLANNED -> ACTIVE -> ON_HOLD -> ACTIVE`, puis `ACTIVE -> COMPLETED` ou annulation des statuts non terminaux. La V2 **ne modifie pas cette matrice sans ADR**.

## 8.2 Matrice des transitions M0 proposées

| Source | Commande | Cible | Condition impérative |
|---|---|---|---|
| `DRAFT` | `PlanProject` | `PLANNED` | Définition planifiée valide |
| `PLANNED` | `StartProject` | `ACTIVE` | Date réelle de démarrage |
| `ACTIVE` | `PauseProject` | `ON_HOLD` | Transition autorisée |
| `ON_HOLD` | `ResumeProject` | `ACTIVE` | Pas de second démarrage initial |
| `ACTIVE` | `CompleteProject` | `COMPLETED` | ClosurePolicy validée, fin réelle |
| `DRAFT / PLANNED / ACTIVE / ON_HOLD` | `CancelProject` | `CANCELLED` | Motif et contexte requis selon policy |
| `COMPLETED / CANCELLED` | `StartProject` | Refus | Réouverture non implémentée par défaut |

- `BR-PROJ-001` : planifier n'est possible qu'à partir de `DRAFT` dans le scénario M0.
- `BR-PROJ-002` : démarrer requiert `PLANNED` ; produit `ACTIVE` et une date réelle.
- `BR-PROJ-003` : suspendre requiert `ACTIVE`.
- `BR-PROJ-004` : reprendre requiert `ON_HOLD`, sans écraser `actual_start_date`.
- `BR-PROJ-005` : annuler un projet non terminé produit un état terminal et une justification auditable si la policy l'exige.
- `INV-PROJ-009` (nouveau) : un `ProjectStatus` ne représente ni une priorité, ni une maturité de package, ni une qualification de preuve.
- `BR-PROJ-006` (nouveau) : l'archivage ou la décision `PARK` ne change pas automatiquement le cycle métier `Project`.

## 8.3 Clôture sous politique explicite

`ProjectClosurePolicy` doit évaluer les critères applicables au **type de projet et à sa portée**, non une checklist universelle de publication PyPI.

Exemples de critères configurables : jalons obligatoires, tâches requises, acceptation des livrables, risques critiques, approbations, recette client, clôture budgétaire, conformité d'un gate spécialisé.

- `BR-PROJ-CLOSE-001` : un projet ne peut devenir `COMPLETED` lorsque sa `ProjectClosurePolicy` échoue.
- `BR-PROJ-CLOSE-002` : la transition locale `ACTIVE -> COMPLETED`, la date réelle et les événements mis en tampon constituent une modification métier cohérente.
- `APP-PROJ-CLOSE-001` (nouveau) : la vérification portant sur plusieurs agrégats utilise des références actuelles, non un `ProjectSnapshot` périmé.
- `APP-PROJ-CLOSE-002` (nouveau) : si les critères requièrent l'absence de tâches ouvertes, la concurrence entre clôture et modification de tâches est maîtrisée (verrou, version, sérialisation ou autre mécanisme prouvé).
- `BR-PROJ-CLOSE-003` (nouveau) : un résultat de test peut satisfaire un critère technique, mais ne remplace pas une approbation humaine explicitement requise.

**Exemple** : un site client peut être techniquement livré mais non accepté. Un package peut être qualifié mais non publié. Dans les deux cas, la politique peut refuser la clôture si l'acceptation ou la publication faisait partie des obligations du projet.

# 9. Aggregate `Task` : règles M0

## 9.1 Invariants hérités

| ID | Contrat |
|---|---|
| `INV-TASK-001` | La tâche possède un `TaskId` stable |
| `INV-TASK-002` | Elle porte un `ProjectId` obligatoire |
| `INV-TASK-003` | Son titre est non vide |
| `INV-TASK-004` | `parent_task_id != id` |
| `INV-TASK-005` | Les dates planifiées et réelles respectent l'ordre lorsqu'elles existent |
| `INV-TASK-006` | La valeur numérique de progression est entre 0 et 100 |

## 9.2 Cycle de vie et exécution

Matrice M0 historique : `TODO -> READY -> IN_PROGRESS -> [BLOCKED -> IN_PROGRESS] / IN_REVIEW -> DONE`, avec annulation explicite depuis les statuts non terminaux. Les transitions exactes dépendent des options de revue ; une clôture directe `IN_PROGRESS -> DONE` reste permise dans le cas simple.

| ID | Règle |
|---|---|
| `BR-TASK-START-001` | Démarrer exige un statut autorisé, `READY` par défaut |
| `BR-TASK-START-002` | Démarrer est interdit si un prérequis bloquant est insatisfait |
| `BR-TASK-START-003` | Démarrer est interdit si le projet est `COMPLETED` ou `CANCELLED` |
| `BR-TASK-START-004` | Une policy peut restreindre le démarrage si le projet est `ON_HOLD` ; le défaut recommandé est de refuser le travail normal |
| `BR-TASK-BLOCK-001` | Le blocage n'est possible que depuis un état compatible |
| `BR-TASK-BLOCK-002` | Un blocage conserve sa cause et une référence de déblocage quand disponible |
| `BR-TASK-BLOCK-003` | La clôture directe d'une tâche bloquée est interdite sans déblocage ou policy explicite |
| `BR-TASK-DONE-001` | `CompleteTask` exige `IN_PROGRESS` ou `IN_REVIEW` en M0 |
| `BR-TASK-DONE-002` | Une tâche terminée a un `actual_end_at` explicite |
| `BR-TASK-DONE-003` | Si un pourcentage est maintenu et qualifié, la fin peut le fixer à 100 ; ne pas déduire par là la qualification d'une release |
| `BR-TASK-DONE-004` | Un second `CompleteTask` ne crée pas de seconde clôture ni d'événement de succès supplémentaire |

### Compléments V2

- `INV-TASK-007` : une tâche de projet géré possède une référence vers un projet réellement résolu dans le scope courant ; contrôle inter-AR par use case (`INV-REL-001` du 06).
- `INV-TASK-008` : une relation tâche-jalon ne traverse jamais un autre `ProjectId` (`INV-REL-002`).
- `INV-TASK-009` : une tâche `DONE` n'est pas équivalente à une preuve `VERIFIED` ou une capacité `QUALIFIED`.
- `BR-TASK-REOPEN-001` : la réouverture d'une tâche `DONE` est différée et ne doit pas être implicitement permise par une simple écriture de statut.
- `APP-TASK-001` : l'affectation d'un membre ne suffit pas à lui donner la permission de lire ou de muter la tâche.
- `APP-TASK-002` : démarrage, affectation et clôture sont contrôlés contre une version appropriée de Project/Task et les politiques applicables.

## 9.3 `WorkItem`, `Task`, `ActionItem`, `NextAction`

`WorkItem` désigne un langage commun de travail ; `Task` est l'Aggregate Root opérationnel M0. `ActionItem` peut désigner une obligation issue d'une revue ; `NextAction` est une **projection recommandée**, non une Task supplémentaire. Une tâche projet ne doit pas être automatiquement créée en ingérant un `ExecutionReport` Pythos.

# 10. Sous-tâches, dépendances et intégrité du graphe

- `INV-SUBTASK-001` : la parenté des tâches est acyclique.
- `BR-SUBTASK-001` : enfant et parent appartiennent au même `ProjectId`, et au même périmètre de visibilité.
- `BR-SUBTASK-002` : une policy peut borner la profondeur ; par défaut, ne pas promettre des hiérarchies illimitées.
- `INV-DEP-001` : une dépendance ne peut relier une tâche à elle-même.
- `INV-DEP-002` : même `predecessor`, `successor` et `type` dans le même scope ne créent pas deux liens logiques distincts.
- `INV-DEP-003` : le graphe de dépendances ordonnant l'exécution reste acyclique.
- `BR-DEP-001` : l'ajout de lien passe par une validation du graphe.
- `BR-DEP-002` (nouveau) : pour M0, le type `BLOCKING`/`FINISH_TO_START` signifie « successeur ne démarre pas tant que le prédécesseur n'est pas `DONE` ».
- `BR-DEP-003` (nouveau) : les dépendances inter-projets et les types avancés sont différés, sauf contrat de domaine et politique de contrôle explicites.
- `APP-DEP-001` (nouveau) : une vérification de graphe suivie d'une écriture doit résister aux insertions concurrentes incompatibles ; une validation isolée en mémoire ne garantit pas l'acyclicité persistée.
- `APP-DEP-002` (nouveau) : la création d'une dépendance non autorisée, d'un doublon ou d'un cycle ne laisse aucun lien partiellement engagé.

## 10.1 Sens canonique de la dépendance

```text
predecessor_id -> tâche qui doit satisfaire le prérequis
successor_id   -> tâche dont le démarrage dépend du prérequis

BLOCKING(A,B) ET A.status != DONE  => StartTask(B) rejeté
BLOCKING(A,B) ET A.status == DONE  => cette dépendance ne bloque plus B
```

Pour une chaîne A -> B -> C, l'ajout C -> A est rejeté. Pour la parenté, le cycle A parent de B, B parent de C, C parent de A est également rejeté, mais **ce sont deux graphes métier distincts**.

## 10.2 Tests obligatoires M0

```text
test_dependency_rejects_self_reference
test_dependency_rejects_cycle_across_three_tasks
test_task_cannot_start_until_predecessor_done
test_parent_hierarchy_rejects_cycle
test_two_concurrent_dependency_insertions_cannot_create_cycle
```

Le dernier test dépend du backend et devient obligatoire pour revendiquer des écritures concurrentes sûres, pas nécessairement pour la première implémentation mono-processus InMemory.

# 11. Jalons, livrables et critères d'acceptation

- `INV-MILE-001` : un jalon appartient à un projet identifié.
- `INV-MILE-002` : un jalon possède une date cible définie dans le modèle M0 historique ; un modèle sans date exige une décision de changement de contrat.
- `INV-MILE-003` : un jalon atteint a une date `reached_at`.
- `INV-MILE-004` : un jalon non atteint n'a pas de `reached_at`.
- `BR-MILE-001` (nouveau) : l'indicateur `MISSED` se calcule de préférence à partir de `today > target_date` et du statut réel, sans écrire un nouveau statut historique sur chaque lecture.
- `BR-MILE-002` (nouveau) : l'atteinte d'un jalon ne vaut pas acceptation de ses livrables si une approbation séparée est requise.
- `BR-DELIV-001` : un livrable ne peut être accepté que si ses critères obligatoires sont satisfaits.
- `BR-DELIV-002` : une validation finale peut exiger une `Approval` selon la politique applicable.
- `APP-MILE-001` (nouveau) : un `Task.milestone_id` doit cibler un jalon du même projet ; si `Milestone` est interne à `Project`, la mutation passe par son owner.
- `BR-ACCEPT-001` (nouveau) : un critère évalué `PASS` et une décision humaine `APPROVED` restent des objets et actes différents.

- `INV-DELIV-V2-001` (nouveau, proposé) : un livrable référence un projet ou un jalon identifiable, dans une portée autorisée.

**Option C3** : les objets riches `Deliverable` et `AcceptanceCriterion` sont documentés mais différés s'ils n'apportent aucun comportement nécessaire au premier parcours M0.

# 12. Affectations, progression, santé et dates

- `BR-ASSIGN-001` : une tâche ne peut être affectée qu'à un membre admissible, résolu dans le contexte de projet autorisé.
- `BR-ASSIGN-002` : l'admissibilité d'un membre peut être déterminée par une `Policy` explicite (par exemple, son appartenance au projet).
- `BR-ASSIGN-003` : une affectation terminée doit conserver sa date `unassigned_at` lorsqu'un historique d'affectation est géré ; toute simplification du stockage M0 requiert une décision de portée explicite.
- `BR-ASSIGN-V2-001` (nouveau, proposé) : le premier modèle M0 admet au plus un assigné actif par tâche ; la multi-affectation est différée.
- `BR-ASSIGN-V2-002` (nouveau, proposé) : aucune affectation ne contourne les transitions interdites d'un statut terminal.
- `BR-PROGRESS-001` : le progrès global ne se déduit pas universellement du seul nombre de tâches terminées.
- `BR-PROGRESS-002` : la méthode de progression est explicite (`MANUAL`, `WEIGHTED`, par jalons, etc.) ; l'affichage d'une valeur ne constitue pas une preuve de qualification.
- `BR-HEALTH-001` : la santé d'un projet provient d'une `ProjectHealthPolicy` ou d'une formule explicite, avec dimensions observables.
- `BR-HEALTH-002` : une projection `GREEN` n'est pas une vérité mutationnelle et peut être périmée.
- `BR-HEALTH-003` : `RED` si une dimension critique est rouge, etc., est une policy illustrative, non un invariant imposé.
- `INV-DATE-001` : un `DateRange` conserve une borne de début inférieure ou égale à la borne de fin lorsque les deux existent.
- `INV-DATE-002` : une période vide n'est acceptable que si le modèle métier l'autorise explicitement.
- `INV-DATE-V2-001` (nouveau, proposé) : les bornes d'une période utilisent des types et granularités temporelles compatibles.
- `INV-DUR-001` : une `Duration` est non négative lorsqu'elle décrit un effort ou délai de travail normal.
- `INV-PERCENT-001` : un `Percentage` métier par défaut appartient à `[0,100]`.

# 13. Versionnement, idempotence et invariants temporels

- `INV-VERSION-001` : la version logique d'une Entity est monotone et n'est pas réutilisée pour représenter un état plus ancien.
- `BR-VERSION-001` : une mutation fondée sur une version obsolète doit être refusée avec conflit explicite, lorsque le contrat de concurrence est activé.
- `BR-IDEMP-001` : la répétition de la même demande externe dans un scope et sous une clé d'idempotence équivalente ne crée pas plusieurs mutations métier ou actes d'approbation.
- `APP-TIME-001` (nouveau) : distinguer date de réalisation, d'observation, d'enregistrement, de vérification, de capture et d'effet dans les transactions et les lectures.
- `APP-IDEMP-001` (nouveau) : la clé d'idempotence inclut l'identité du consommateur, le scope et le type d'effet ; une clé appartenant à un autre projet ne donne pas accès à son résultat.
- `APP-IDEMP-002` (nouveau) : rejouer une commande avec la même clé mais un payload contradictoire est un conflit, pas une nouvelle approbation.

**Aucune promesse universelle** d'exactly-once, event replay, optimistic concurrency ou Outbox n'est faite sans mécanisme implémenté et qualification démontrée.

# 14. Séparation des frontières transactionnelles M0

`Project` et `Task` sont des Aggregate Roots distincts. Une mise à jour de `Task` ne doit pas toucher silencieusement la version de `Project` ; une politique dépendant de deux agrégats relève du use case applicatif et éventuellement d'une transaction coordonnée.

- `APP-UOW-001` : les mutations d'un Aggregate protègent tous ses invariants dans la même unité de cohérence.
- `APP-UOW-002` : aucune mise à jour directe des tables d'un autre bounded context n'est autorisée par le domaine.
- `APP-UOW-003` : le rollback d'une commande échouée n'émet pas de Domain Event de succès.
- `APP-UOW-004` : si des modifications multi-agrégats ne partagent pas une transaction, la stratégie de reprise/compensation est explicitée ; ne pas revendiquer une atomicité distribuée imaginaire.

# 15. Modèle de preuve avant statut : invariant conceptuel transversal

Les états suivants décrivent des questions différentes :

| Dimension | Question | Exemples |
|---|---|---|
| `ProjectStatus` | Où en est le cycle d'un projet ? | `ACTIVE`, `COMPLETED` |
| `TaskStatus` | Où en est une unité de travail ? | `IN_PROGRESS`, `DONE` |
| `KnowledgeStatus` | Que savons-nous d'une affirmation ? | `UNKNOWN`, `PARTIAL`, `SUPPORTED` selon contrat |
| `SourceFreshness` | L'observation est-elle encore actuelle ? | `CURRENT`, `STALE`, `UNAVAILABLE` |
| `VerificationResult` | Le contrôle défini a-t-il réussi ? | `PASS`, `FAIL`, `PARTIAL`, `UNKNOWN` |
| `ApprovalStatus` | Une autorité habilitée a-t-elle accepté ? | `PENDING`, `APPROVED`, `REJECTED` |
| `ProjectMaturity` spécialisé | Quel état de livraison logiciel est prouvé ? | `SPECIFIED`, `QUALIFIED`, `PUBLISHED` |
| `PortfolioDecisionKind` | Quel arbitrage est adopté ? | `KEEP`, `PARK` pour l'overlay Py*Kit |

- `INV-STAT-001` : `TaskStatus.DONE` n'implique pas `VerificationResult.PASS`.
- `INV-STAT-002` : `VerificationResult.PASS` n'implique pas `ApprovalStatus.APPROVED`.
- `INV-STAT-003` : `ProjectMaturity.QUALIFIED` n'implique pas `PUBLISHED`.
- `INV-STAT-004` : `PUBLISHED` n'implique pas `OPERATED`.
- `INV-STAT-005` : `PortfolioDecisionKind.KEEP` n'implique pas `ProjectStatus.ACTIVE`.
- `INV-STAT-006` : `SourceFreshness.STALE` n'est pas un verdict technique `FAIL`.
- `BR-STAT-001` : toute projection de statut probant doit exposer le périmètre, la référence exacte, les réserves et le statut maximal démontré.

Cette section constitue une **séparation sémantique** : elle n'impose pas une classe `ProjectMaturity` ni l'échelle logicielle à tous les projets. L'overlay spécifique Py*Kit peut fournir la policy correspondante.

# 16. Contrats de clôture et de qualification différenciés

| Cas | État métier | Vérification | Décision |
|---|---|---|---|
| Une tâche de rédaction est achevée | `DONE` | Contenu éventuellement à relire | Pas nécessairement approuvé |
| Tests sur commit identifié | Tâche test exécutée | `PASS` sur ce commit | Aucun accord de release implicite |
| Livrable client prêt | Livrable soumis | Critères contrôlés | Acceptation client éventuellement en attente |
| Snapshot écrit | Vue historisée disponible | Provenance parfois partielle | Ne crée aucune clôture |
| Rapport Pythos reçu | Observation reçue | Doit être validée selon politique | Ne décide rien à lui seul |

- `BR-QUAL-001` : lorsqu'une qualification exige une référence de source exacte, une preuve issue d'une autre révision ne qualifie pas silencieusement la référence courante.
- `BR-QUAL-002` : le statut `UNKNOWN` ou `PARTIAL` demeure possible lorsque la vérification n'a pas pu être conduite.
- `BR-QUAL-003` : la politique de gate d'un produit logiciel est une extension optionnelle ; elle ne commande pas la clôture universelle d'un projet non logiciel.

# 17. `ContextScope` : isolation de projet M1

Le `ContextScope` est une frontière logique de données et de gouvernance, **pas** une permission IAM ni automatiquement un tenant. Sa taxonomie peut inclure `PERSONAL`, `CLIENT`, `PROFESSIONAL`, `R_AND_D`, `EDUCATION`, selon les besoins réels.

- `INV-CTX-001` : chaque projet géré dans le registre M1 possède un `ContextScope` unique et résolu.
- `INV-CTX-002` : une tâche, décision, observation, snapshot ou preuve attachée à un sujet ne peut pas être réaffectée silencieusement à un autre scope.
- `INV-CTX-003` : un identifiant égal dans deux sources/scopes différents ne suffit pas à conclure à un même objet métier.
- `SEC-CTX-001` : toute lecture, projection ou export vérifie les autorisations **avant** l'agrégation des données, et non seulement après construction d'une vue commune.
- `SEC-CTX-002` : les liens vers des preuves ou documents restent protégés par les droits de la source, même si la référence est visible dans PyProjectKit.
- `SEC-CTX-003` : un accès transversal doit être accordé explicitement pour les sujets concernés, avec portée, durée et finalité appropriées.
- `APP-CTX-001` : un import sans scope fiable est mis en quarantaine ou rejeté ; il n'est pas ajouté par défaut au portefeuille personnel.

**M0 mono-contexte** peut utiliser une portée implicite si l'adapter le garantit ; l'exigence explicite devient normative pour M1 multi-contexte.

# 18. Registre de projet transversal M1

`ProjectRegistryEntry` est une **projection**, pas un deuxième Project Aggregate Root.

- `INV-REG-001` : une entrée de registre fait référence à un projet et à un scope déterminés.
- `INV-REG-002` : le registre ne modifie pas l'état de l'Aggregate en recalculant une projection.
- `INV-REG-003` : une ligne de registre garde l'information de fraîcheur/provenance nécessaire à l'interprétation de ses champs.
- `INV-REG-004` : la collision entre une source externe et une identité interne n'entraîne aucune fusion automatique non vérifiée.
- `BR-REG-001` : une entrée peut être recalculée depuis les faits gérés et leurs références ; une projection cache ne constitue pas la source d'autorité.
- `BR-REG-002` : un projet sans activité observable peut rester visible comme `UNKNOWN` ou `PARK` selon son classement, sans être déclaré `COMPLETED`.
- `APP-REG-001` : une importation crée ou met à jour un mapping dans son périmètre et conserve son origine, sa révision et son horodatage.

Le mécanisme de regroupement en portefeuille reste léger à M1 ; `Portfolio` comme Aggregate Root autonome est différé tant que ses invariants transactionnels ne sont pas observés.

# 19. Références externes et provenance

Une `ExternalReference` indique un objet externe ; une `SourceReference` décrit la référence identifiante à la source de connaissance. Les deux ne prouvent pas que le fait affirmé est vrai.

- `INV-SRC-001` : une référence externe porte le système source, un identifiant canonique ou URI admissible, et un scope explicite.
- `INV-SRC-002` : une référence n'est pas réécrite silencieusement pour pointer vers une autre ressource ; correction par version/supersession explicite.
- `INV-SRC-003` : un mapping `source, external_id, scope` ne correspond pas simultanément à plusieurs projets internes actifs, sauf contrat explicite d'ambiguïté/réconciliation.
- `INV-SRC-004` : un lien externe n'implique ni disponibilité ni permission d'accès.
- `BR-SRC-001` : une source indisponible est signalée `UNAVAILABLE`, sans effacer l'observation historique précédente.
- `BR-SRC-002` : lorsqu'une référence exige un commit exact, une branche mutable comme `main` ne constitue pas une révision immuable.
- `APP-SRC-001` : l'ingestion contrôle la normalisation, le type de source, les collisions et la portée avant de muter un mapping interne.
- `APP-SRC-002` : la réconciliation explicite est nécessaire pour relier plusieurs comptes, dépôts ou projets supposés identiques sans preuve suffisante.

# 20. Assertions et observations

`Claim` est une affirmation sur un sujet dans une portée déterminée. `Observation` est un constat enregistré avec sa provenance et ses limites ; il ne devient pas une décision à son seul enregistrement.

- `INV-CLAIM-001` : une affirmation enregistrée porte un `SubjectReference`, une proposition interprétable et un scope.
- `INV-CLAIM-002` : une affirmation doit être attribuée à sa source ou auteur ; « rapporté par un agent » ne signifie pas « vérifié par la source primaire ».
- `INV-OBS-001` : une observation porte un sujet, une source, un instant `observed_at` ou une absence explicitement marquée, et la méthode d'acquisition connue.
- `INV-OBS-002` : la provenance `ORIGINAL`, `RECONSTRUCTED`, `PARTIAL`, `UNKNOWN` reste distinguable dans les historiques.
- `INV-OBS-003` : un constat historique ne se réécrit pas après un changement de source ; on ajoute correction ou observation ultérieure liée.
- `INV-OBS-004` : une observation ne promeut pas automatiquement le statut métier de son sujet.
- `BR-OBS-001` : un constat périmé est marqué `STALE` au moment de la consultation selon une politique de fraîcheur explicite ; l'ancien constat n'est pas rétroactivement déclaré mensonger.
- `BR-OBS-002` : si une source retourne un état incohérent avec un autre, conserver les observations et ouvrir une réconciliation plutôt que choisir silencieusement la plus favorable.

## 20.1 Exemple de provenance

```yaml
observation:
  subject: "Task:task-42"
  scope: "CLIENT:example"        # valeurs illustratives
  claim: "La PR associée possède une CI verte"
  source_kind: "github_actions"
  source_reference: "run:12345"
  source_revision: "commit-sha-exact"
  observed_at: "2026-11-02T17:00:00+01:00"
  provenance: "ORIGINAL"
  limitations:
    - "ne prouve pas une recette client"
```

Cet exemple est un **contrat documentaire illustratif** : il ne prouve aucun run CI réel.

# 21. Preuves, validité et limitations

`EvidenceRef` est un Value Object portant une référence contrôlable, sa source et ses limites. Il n'est ni l'artefact complet, ni l'évaluation, ni l'approbation.

- `INV-EVID-001` : une preuve référencée possède un identifiant ou URI exploitable, un type, un scope et une origine identifiables.
- `INV-EVID-002` : une preuve portant sur une version donnée ne qualifie pas une autre version sans contrat de compatibilité/équivalence prouvé.
- `INV-EVID-003` : une preuve doit conserver son champ de validité (`scope`) et ses exclusions connues quand elles sont pertinentes.
- `INV-EVID-004` : une preuve associée à un sujet n'autorise pas l'accès au contenu d'une source protégée.
- `INV-EVID-005` : une preuve inaccessible reste référencée avec un statut explicite, mais ne peut être présentée comme vérifiée aujourd'hui.
- `BR-EVID-001` : les affirmations de qualification logiciel requièrent les éléments obligatoires prévus par la policy : version, commit exact, tests, environnement et date.
- `BR-EVID-002` : les copies de fichiers sensibles ne sont pas imposées ; le registre favorise les références minimales et les empreintes lorsque justifiées.

# 22. Évaluation et réconciliation

Une `VerificationAssessment` exprime un verdict sur **une affirmation**, avec méthode, références et limites. Elle ne transforme pas un résultat technique en décision métier.

- `INV-VER-001` : l'évaluation porte un sujet/claim identifiable et une portée précise.
- `INV-VER-002` : un verdict `PASS` exige une méthode de vérification, un résultat et une source corrélés au sujet déclaré.
- `INV-VER-003` : `UNKNOWN` est distinct de `FAIL`, et `PARTIAL` ne peut être promu en `PASS` par défaut.
- `INV-VER-004` : le temps `verified_at` décrit la vérification, distinct de la date du fait et de la capture du snapshot.
- `INV-VER-005` : une évaluation finale sur une référence exacte ne se transforme pas rétroactivement si la cible `main` évolue ; un nouveau contrôle est nécessaire.
- `BR-VER-001` : la valeur maximale de maturité affichée est limitée par les preuves effectivement établies dans son scope.
- `BR-VER-002` : un résultat d'agent est traité comme entrée à vérifier, non comme assessment privilégié sans contrôle.
- `INV-REC-001` : un conflit possède des références à ses observations incompatibles et à un sujet/scope identifiés.
- `INV-REC-002` : une résolution de conflit conserve la décision, le motif et les références ; ne supprime pas silencieusement le constat écarté.
- `BR-REC-001` : aucune sélection arbitraire (`first`, `latest`) lorsque la résolution est matériellement ambiguë.

# 23. `ProjectSnapshot` : continuité historisée

`ProjectSnapshot` est une **lecture historique**, immuable après sa capture, et non un substitut à `Project`, `Task` ou aux sources primaires.

- `INV-SNAP-001` : chaque snapshot comporte `ProjectId`, `ContextScope`, `captured_at` et sa propre identité ou version stable.
- `INV-SNAP-002` : le contenu déjà capturé n'est pas modifié silencieusement ; une correction crée une nouvelle version/supersession référencée.
- `INV-SNAP-003` : le snapshot identifie les versions/références utilisées et ses manques connus, selon les éléments disponibles.
- `INV-SNAP-004` : un snapshot `RECONSTRUCTED` ne peut être annoncé comme capture originale de la date passée.
- `INV-SNAP-005` : un snapshot n'accorde pas des droits d'accès aux sources référencées.
- `INV-SNAP-006` : un snapshot historisé peut être consulté après redémarrage lorsque la persistance durable M1 est activée.
- `BR-SNAP-001` : une capture significative peut inclure décisions, prochaines actions, blocages et source de fraîcheur, sans recopier tous les documents liés.
- `BR-SNAP-002` : un changement du projet courant n'altère pas le snapshot passé ; une lecture actuelle indique si la capture est périmée.
- `APP-SNAP-001` : la capture multi-objet fournit une cohérence définie (point temporel, révisions, limites), et ne revendique pas un instantané transactionnel global si ce n'est pas garanti.

# 24. `NextAction` : recommandation, pas commande

`NextAction` est un Read Model : une suggestion de travail contextualisée, dérivée de faits et de décisions visibles.

- `INV-NEXT-001` : toute action proposée pointe vers un projet et, lorsque pertinent, un `WorkItemRef` ou motif qui permet sa justification.
- `INV-NEXT-002` : une projection `NextAction` ne crée ni nouvelle tâche, ni autorisation, ni approbation.
- `INV-NEXT-003` : une recommandation calculée doit afficher ou retrouver ses critères de priorité, son scope et sa fraîcheur.
- `BR-NEXT-001` : des actions contradictoires ne doivent pas être consolidées silencieusement comme une même obligation.
- `BR-NEXT-002` : une action `PARK`/`RETIRE` dans le portefeuille spécialisé n'est pas proposée comme chantier actif sans nouvel arbitrage habilité.
- `BR-NEXT-003` : aucune métrique de progression ne doit être améliorée artificiellement par multiplication de recommandations non exécutées.

# 25. `HandoffRecord` : passage de relais et reprise

`HandoffRecord` représente ce qui a été livré, ce qui reste, sur quelle référence et avec quelles limites. Il appartient au contexte du travail, non à la mémoire infaillible de l'agent.

- `INV-HAND-001` : le handoff porte sujet/projet, instant, auteur ou producteur et statut de clôture ou de reprise explicite.
- `INV-HAND-002` : il sépare résultat, références, contrôles réalisés, limites, risques et prochaine action si applicable.
- `INV-HAND-003` : un handoff est un historique ; une nouvelle reprise ne réécrit pas silencieusement le rapport précédent.
- `INV-HAND-004` : `ExecutionReport` provenant de Pythos ne clôture pas automatiquement un `Task` ou un projet.
- `BR-HAND-001` : une reprise doit distinguer ce qui est établi depuis le snapshot précédent de ce qui doit être revérifié.
- `BR-HAND-002` : les informations sensibles et les capacités d'exécution ne traversent pas les frontières de scope sans autorisation active.

# 26. Gouvernance : décisions, approbations, portefeuille

## 26.1 Décision, revue et approbation

- `INV-DEC-001` : une décision comporte sujet, contenu, date, décideur ou source responsable identifiée.
- `BR-DEC-001` : une décision appliquée n'est pas supprimée ou modifiée silencieusement ; correction, révocation et supersession ont une trace.
- `INV-DEC-002` (nouveau) : une décision humaine est distincte d'un constat, d'une recommandation agentique et d'un résultat CI.
- `INV-DEC-003` (nouveau) : une décision extérieure à PyProjectKit possède une référence d'autorité externe ; PyProjectKit ne s'en déclare pas l'auteur.
- `BR-APPROVAL-001` : l'approbation comprend approbateur, objet, verdict, date et scope.
- `BR-APPROVAL-002` : une politique de séparation des responsabilités peut empêcher l'auto-approbation.
- `BR-APPROVAL-003` : une demande de changement ne passe à `APPROVED` que lorsque la `ApprovalPolicy` applicable est satisfaite.
- `INV-APPROVAL-001` (nouveau) : l'identité de l'approbateur est vérifiée par un système habilité ; un champ `approved=true` envoyé par un agent n'a aucune autorité.
- `INV-APPROVAL-002` (nouveau) : une approbation porte sur une action et une version/périmètre déterminés ; elle ne se transfère pas sans règle à une autre action.
- `BR-GATE-001` : un gate applicable ne passe pas lorsque ses critères obligatoires échouent.
- `BR-GATE-002` : un gate peut exiger une ou plusieurs approbations.
- `INV-REVIEW-001` : une review possède une cible identifiée.
- `BR-REVIEW-001` : une review terminée peut créer des `ActionItem` sans que ceux-ci deviennent de nouvelles tâches automatiquement.

## 26.2 `PortfolioDecision` et politiques spécialisées

- `INV-PORT-DEC-001` : toute décision portefeuille cible un sujet, une portée, une date et un décideur habilité.
- `INV-PORT-DEC-002` : une décision `KEEP/MERGE/PARK/RETIRE` ne modifie pas silencieusement `ProjectStatus` ni la maturité logicielle.
- `BR-PORT-DEC-001` : `KEEP/MERGE/PARK/RETIRE` est un vocabulaire de la policy **Py*Kit**, non une enum universelle imposée aux clients externes.
- `BR-PORT-DEC-002` : l'ouverture d'un nouveau dépôt est une opération hors du core PyProjectKit et exige, pour notre fabrique, les validations Pythos/humaines applicables.
- `BR-PORT-DEC-003` : la limitation du travail en cours (`WIP`) dépend de la policy du portefeuille ; deux P1 majeurs simultanés est un paramètre de notre manufacture, pas un invariant universel.

# 27. Gestion des changements, risques et événements de décision

- `INV-CR-001` : une `ChangeRequest` référence un projet.
- `INV-CR-002` : son objet doit être explicite.
- `INV-CR-003` : son impact est documenté lorsque la policy l'exige.
- `BR-CR-001` : le cycle `DRAFT -> SUBMITTED -> APPROVED/REJECTED -> IMPLEMENTED` interdit `REJECTED -> IMPLEMENTED` et `DRAFT -> IMPLEMENTED` sans workflow de dérogation explicite.
- `BR-CR-002` : une demande déjà soumise n'est pas modifiée silencieusement ; retour en brouillon ou nouvelle version selon policy.
- `INV-RISK-EXT-001` : la réalisation d'un risque et la déclaration d'un `Issue` doivent conserver leur causalité si la fonctionnalité RAID est activée.
- `BR-ISSUE-001` : un blocage déclaré ne devient pas automatiquement un échec définitif du projet ; santé et priorisation restent des calculs contextualisés.

# 28. Sécurité : frontière application, pas identité implicite du domaine

Ces règles complètent le document 12 sans lui retirer la responsabilité de la matrice détaillée RBAC/ABAC.

- `SEC-001` : toute Command sensible est évaluée avec l'acteur, l'action, le sujet, le scope et la politique d'autorisation applicables.
- `SEC-002` : les Queries et exports appliquent la même politique de confidentialité que les Commands sur les données concernées.
- `SEC-003` : par défaut, absence de permission, mandat ou contexte fiable conduit au refus (`default deny` et `fail-closed`).
- `SEC-004` : les identifiants de projets invisibles ne sont pas divulgués par des messages d'erreur, volumes agrégés ou liens de preuve.
- `SEC-005` : le producteur d'une observation, d'une CI ou d'un snapshot ne reçoit aucune permission supplémentaire de mutation.
- `SEC-006` : les événements, logs et handoffs sont minimisés et ne contiennent pas de secrets, tokens ni pièces brutes sans autorisation appropriée.
- `SEC-007` : l'autorisation est revalidée au moment où une action à effet est appliquée, même si une consultation initiale était autorisée.
- `SEC-008` : une exécution déléguée ne peut acquérir davantage d'autorité que son mandant et le contexte explicitement autorisé.
- `SEC-009` : un objet ou rapport venant d'un scope externe ne devient pas lisible parce qu'un lien est agrégé dans un portefeuille.
- `SEC-010` : la suppression, rétention et anonymisation respectent les politiques de conservation applicables, sans promesse « jamais supprimer » absolue lorsque la loi ou l'autorité impose un traitement contraire.

# 29. Gouvernance des sources de vérité

| Question | Source faisant autorité | Ce que PyProjectKit peut conserver |
|---|---|---|
| Statut d'un projet interne | Aggregate Project / application qui le possède | Statut, version, historique |
| État d'une tâche interne | Task / application qui le possède | Statut, références, événements |
| Existence d'un commit | Dépôt Git / fournisseur correspondant | SHA, URI, observation |
| Résultat CI | Système CI | Run exact, conclusion, date |
| Publication package | Registry ou système de release | Version, artefact vérifié |
| Décision humaine | Registre et autorité habilités | Decision/Approval local autorisé ou référence |
| État du portefeuille spécialisé | Registre opérationnel validé | Décision, priorité, source |
| Rapport de Pythos | Agent et système de mandat | Représentation, référence, limites |
| Vue consolidée | Projection locale PyProjectKit | Snapshot/RegistryEntry datés |

- `INV-TRUTH-001` : une projection n'écrit pas la vérité qu'elle projette.
- `INV-TRUTH-002` : la source primaire reste identifiable pour toute affirmation importante.
- `INV-TRUTH-003` : une source d'intention ne prouve pas une exécution.
- `INV-TRUTH-004` : une source d'exécution ne prouve pas une autorisation ou une acceptation humaine qui n'y figure pas.

# 30. Boucle PyProjectKit / Pythos : règles optionnelles M2

Le mode opératoire Pythos définit quatre modes (`LEARNING`, `PRODUCTION`, `AUDIT`, `PORTFOLIO`), une chaîne `Orient -> Frame -> Plan -> Execute -> Verify -> Explain -> Record -> Close`, les niveaux A0 à A5 et les gates G0 à G7 pour la manufacture logicielle. Ces éléments sont **des politiques et contrats d'un consommateur**, et non des propriétés de base de tous les projets.

## 30.1 Contrat d'entrée : Operating Brief

- `APP-PYTHOS-001` : la lecture d'un contexte de travail est filtrée selon le projet, le scope et le mandat courant.
- `APP-PYTHOS-002` : l'Operating Brief inclut la cible, l'objectif, la portée, les critères d'acceptation, les sources et les décisions humaines requises selon le type de chantier.
- `APP-PYTHOS-003` : un mandat ne peut pas étendre ses propres permissions par mutation d'un DTO.
- `APP-PYTHOS-004` : un Brief absent, expiré, mal ciblé ou d'autorité insuffisante bloque les mutations correspondantes, sans masquer les capacités de lecture éventuellement autorisées.

## 30.2 Contrat de sortie : Execution Report

- `BR-PYTHOS-001` : le rapport sépare résultat, changements, contrôles, références exactes, limites, risques et prochaines actions.
- `BR-PYTHOS-002` : une affirmation de succès agentique n'est pas un événement métier `TaskCompleted` tant qu'une Command explicite autorisée n'a pas satisfait ses guards.
- `BR-PYTHOS-003` : un rapport importé peut créer des observations/handoffs selon la policy, mais ne crée pas un `Approval` humain.
- `BR-PYTHOS-004` : l'import idempotent d'un rapport vérifie son identité, producteur, mandat, cible et version du schéma ; un replay contradictoire est rejeté.
- `BR-PYTHOS-005` : une absence de preuve exacte est enregistrée comme limite, pas complétée par inférence d'un précédent échange.

## 30.3 Sécurité et gouvernance des niveaux A0-A5

| Niveau Pythos | Nature | Traitement dans PyProjectKit |
|---|---|---|
| `A0` | Observer | Query autorisée seulement |
| `A1` | Proposer | Brouillon ou proposition, aucune mutation autoritative |
| `A2` | Préparer | Changements locaux dans le périmètre autorisé ; statut métier inchangé sans Command |
| `A3` | Soumettre | Effet externe explicite sous mandat, audit et contrôles |
| `A4` | Décider | Décisions humaines réservées, non auto-accordées |
| `A5` | Détruire | Opérations destructives à autoriser séparément et avec cible vérifiée |

- `APP-PYTHOS-005` : une policy de Pythos peut exiger un gate G0-G7 ou un mode `AUDIT` sans rendre ce gate obligatoire pour les projets sans rapport avec le logiciel.
- `SEC-PYTHOS-001` : une donnée extraite d'un environnement professionnel ne rejoint pas automatiquement un contexte personnel au motif que le compagnon orchestre les deux.
- `SEC-PYTHOS-002` : l'agent ne signe pas une approbation humaine par délégation implicite ; les opérations réservées exigent la décision de l'autorité.
- `SEC-PYTHOS-003` : un `ExecutionReport` ne peut ni réécrire un snapshot historique, ni contourner une politique de clôture, ni réattribuer des droits.

# 31. Événements métier, historique et audit

Les événements décrivent des faits passés **après transition valide** ; l'audit de sécurité et les observations externes constituent des flux distincts.

- `BR-EVT-001` : nom d'événement au passé : `TaskCompleted` oui, `SendTaskEmail` non.
- `BR-EVT-002` : émission seulement pour une mutation métier réussie.
- `BR-EVT-003` : payload et date déterministes à entrées/horloge égales, hors identifiants de séquence explicitement injectés.
- `BR-EVT-004` (nouveau) : un `ObservationRecorded` peut être événement métier si l'enregistrement constitue un fait métier significatif ; il n'atteste pas que l'observation est vraie.
- `BR-EVT-005` (nouveau) : un `VerificationAssessmentRecorded` décrit l'enregistrement d'un verdict, pas une approbation de release.
- `BR-EVT-006` (nouveau) : pas de secret ni payload sensible complet dans un événement d'intégration par défaut.
- `APP-EVT-001` : en mode transactionnel, l'émission publique dépend du succès de commit ; la durabilité de livraison doit être qualifiée séparément.

**Nommages candidats** : `ProjectPlanned`, `ProjectStarted`, `ProjectPaused`, `ProjectCompleted`, `TaskStarted`, `TaskBlocked`, `TaskCompleted`, `MilestoneReached`, `DecisionRecorded`, `ObservationRecorded`, `ProjectSnapshotCaptured`, `HandoffRecorded`. Le catalogue définitif et la compatibilité relèvent du document 09.

# 32. Archivage, rectification et suppression

- `BR-ARCH-001` : un objet archivé reste consultable par les acteurs autorisés tant que sa politique de conservation le permet.
- `BR-ARCH-002` : l'archivage n'efface pas silencieusement le journal métier.
- `APP-ARCH-001` : rectifier une observation ou décision historisée se fait par nouvelle référence de correction/supersession, avec motif.
- `APP-ARCH-002` : l'effacement d'une donnée personnelle soumis à une politique légale ne doit pas être interdit par un invariant absolu de conservation ; les traces résiduelles sont minimisées selon les obligations applicables.
- `APP-ARCH-003` : un effacement en cascade d'un projet ne doit pas supprimer par inadvertance les preuves nécessaires et autorisées à la conservation.

# 33. Domaines historiques avancés V1 : règles conservées et périmètre

Les familles suivantes faisaient partie de la V1 et restent utiles pour des cas d'usage PMO, Agile, entreprise ou financiers. Elles sont **maintenues comme règles candidates C3** plutôt que promises dès le MVP M0. Les ID historiques sont conservés dans l'annexe A.

## 33.1 Collaboration, capacité et ressources

- `INV-MEMBER-001`, `INV-MEMBER-002` : membre avec identité stable et informations minimales exigées ; pas d'équivalence automatique à l'Actor IAM.
- `INV-MEMBERSHIP-001` à `003` : participation liée au projet et au membre, rôles et périodes cohérents, absence de doublon actif selon périmètre.
- `INV-CAP-001` : une capacité exprimée en unités comparables doit être non négative.
- `BR-CAP-001` : allocation contrôlée selon politique de sur-allocation explicite.
- `BR-CAP-002` : une limite de capacité peut produire un avertissement ou un refus selon la policy, pas toujours un invariant universel.

## 33.2 Agile, Sprint et Backlog

- `INV-SPRINT-001` à `003` : sprint rattaché au projet, plage temporelle cohérente, état valide.
- `BR-SPRINT-001` à `004` : transitions de Sprint, engagement, clôture et modifications après clôture selon policies explicites.
- `BR-BACKLOG-001` et `002` : items identifiés et ordonnancement déterminé dans le périmètre du backlog.
- `BR-AGILE-001` (nouveau) : un projet personnel ou client non Agile n'a pas à créer Sprint, StoryPoints ou KanbanBoard pour satisfaire son cycle métier.

## 33.3 RAID

- `INV-RISK-001` à `004` : risque avec identifiant, lien projet, description et état ; dimensions de probabilité/impact valides selon échelle déclarée.
- `BR-RISK-001` à `005` : score, priorisation, escalade et matérialisation déterminés par policy ; un risque devenu problème suit un `Issue` sans effacer l'historique de risque.
- `INV-ISSUE-001` à `004` : Issue identifiable, scoped, avec état et raison de résolution lorsque clôturé.
- `INV-ASSUMP-001`, `BR-ASSUMP-001` : hypothèse attribuée, validité ou revalidation prévue si nécessaire.

## 33.4 Budgets, temps et coûts

- `INV-WORKLOG-001` à `003` : durée, auteur, travail lié et dates cohérents ; un worklog n'est pas une preuve universelle d'avancement.
- `INV-TIME-001` à `003` : feuilles de temps identifiées, période cohérente et validations selon contrat.
- `INV-BUDGET-001` à `004` : budget scoped, montants et devise cohérents ; pas de mélange de devises non converties.
- `BR-BUDGET-001` à `002` : baseline budgétaire versionnée, modification après gel explicite.
- `INV-BUDGETLINE-001` à `002` : ligne de budget rattachée, montants admissibles.
- `INV-COST-001` à `002` : coût relié et monétisé explicitement.
- `INV-MONEY-001` à `004` : montant et devise validés, opérations arithmétiques compatibles ou conversion sourcée.
- `BR-FINANCE-001` (nouveau) : `EarnedValueSnapshot`, `CPI`, `SPI` et prévisions avancées restent optionnels et interprétables selon la méthode choisie.

## 33.5 Programmes, portefeuilles et performance

- `INV-PROGRAM-001` à `002` : identité et rattachement par référence, pas absorption des projets dans Program.
- `INV-PORT-001` à `002` : identité stable du portefeuille et regroupement explicite.
- `BR-PORT-001` à `002` : priorisation par policy transparente et dimensions d'arbitrage explicites.
- `BR-HEALTH-001` à `003` : santé calculée/derivée sous policy et sources identifiables.
- `BR-PROGRESS-001` à `002` : progression calculée selon méthode déclarée, non présumée linéaire.

# 34. Matrice de conformité par jalon

| Famille | M0 | M1 | M2 | C3 |
|---|---|---|---|---|
| Identity, dates, Project et Task | MUST | Maintenir | Maintenir | Maintenir |
| Graphes et Milestone | MUST | Maintenir | Maintenir | Étendre si besoin |
| Assignee simple | MUST ciblé | Maintenir | Maintenir | Multi-assignation optionnelle |
| ContextScope explicite | Mono-contexte possible | MUST | MUST | Extensions IAM |
| Registry/NextAction projections | Non | MUST | Consommées | Portfolios riches possibles |
| Source/Observation/Evidence/Verification | Non | MUST ciblé | Consommées et alimentées sous contrôle | Preuves spécialisées |
| Snapshot/Handoff | Non | MUST ciblé | MUST handoff intersession | Archivage avancé |
| Gouvernance et décisions minimales | Clôture sous policy | MUST | Mandat/approbation | Workflow multi-approbateurs |
| Gates Py*Kit A0-A5/G0-G7 | Non | Non universels | Policy optionnelle | Selon cas |
| Agile, RAID riches, finances, EVM | Non | Pas imposé | Pas imposé | Différé |

M0/M1/M2 sont des **jalons de livraison ciblés**. Les exigences non implémentées restent `SPECIFIED` ou `CONCEPTUAL`, jamais `TESTED` par simple présence dans cette matrice.

# 35. Scénarios de validation normatifs proposés

## 35.1 Scénario M0 : cycle Project et Task

**Given** un projet `PLANNED` et une tâche `READY` rattachée au projet.  
**When** le projet est démarré puis la tâche est démarrée.  
**Then** `Project` est `ACTIVE`, la tâche est `IN_PROGRESS` et les dates sont présentes ; un second démarrage invalide ne produit pas d'événement de succès.

## 35.2 Scénario M0 : dépendance non satisfaite

**Given** A `IN_PROGRESS` et B `READY`, avec A prédécesseur bloquant de B.  
**When** `StartTask(B)` est demandé.  
**Then** l'opération échoue sans changement de B. Quand A passe à `DONE`, B peut démarrer si les autres guards sont satisfaits.

## 35.3 Scénario M0 : cycle de dépendances

**Given** A -> B et B -> C.  
**When** C -> A est demandé.  
**Then** la dépendance est refusée et le graphe est inchangé.

## 35.4 Scénario M1 : collision de contexte

**Given** une tâche client avec `TaskId` et un autre projet personnel.  
**When** une association au jalon personnel ou un export non autorisé est tenté.  
**Then** l'opération est refusée sans révéler de données interdites.

## 35.5 Scénario M1 : preuve périmée

**Given** une CI verte observée sur commit A et une branche `main` désormais sur commit B.  
**When** un statut de qualification de B est demandé.  
**Then** la réponse est `UNKNOWN` ou non qualifiée pour B, sauf preuve applicable à B ; A conserve son historique.

## 35.6 Scénario M1 : deux sources contradictoires

**Given** un rapport de conversation affirmant « publié » et une source primaire consultée sans artefact vérifiable.  
**When** l'état de publication est évalué.  
**Then** le résultat ne devient pas `PUBLISHED`, les limites sont explicites et une réconciliation est possible.

## 35.7 Scénario M1 : reprise après redémarrage

**Given** un projet avec décision, snapshot, next action et handoff persistés.  
**When** le processus est redémarré et la reprise demandée.  
**Then** le contexte récupérable distingue sources historiques, état courant vérifié et éléments à revalider.

## 35.8 Scénario M2 : rapport Pythos trop ambitieux

**Given** un Operating Brief autorisant la lecture et la préparation, mais pas l'approbation.  
**When** un Execution Report dit « tâche terminée, release validée » avec `approved=true`.  
**Then** le rapport est conservé sous contrôle comme observation ou rejeté selon policy ; aucune approval ni clôture n'est créée sans commande et autorité distinctes.

## 35.9 Scénario M2 : refus d'accès inter-scope

**Given** un mandat limité au projet R&D A.  
**When** un agent demande une preuve contenue dans un projet professionnel B.  
**Then** la lecture est refusée et aucun lien direct exploitable, existence ou secret n'est divulgué.

## 35.10 Scénario C3 : projet non Agile

**Given** un projet de formation avec livrables et échéances sans Sprint.  
**When** il est terminé selon sa policy.  
**Then** aucun `Sprint` ni `StoryPoint` n'est requis pour accepter sa clôture.

# 36. Stratégie de tests et critères d'acceptation

## 36.1 Familles de tests

| Famille | Règles principales | Exemple |
|---|---|---|
| Value Objects | IDs, date, duration, percent, money | bornes et immutabilité |
| Aggregate | transitions Project/Task | guards et postconditions |
| Graph | parenté et dépendances | auto-lien, cycle, doublon |
| Application | références, clôture, concurrence | projet existant, UoW |
| Projection | registre, next action, health | non-mutabilité et provenance |
| Historical records | Observation, snapshot, handoff | immutabilité, correction, restart |
| Evidence contract | versions, méthodes, scope | zéro preuve, partial, mismatch |
| Security | multi-contextes, permission, mandat | cross-scope deny |
| Adapter Pythos | briefs et reports versionnés | report sans autorisation, replay |
| Architecture | direction des dépendances | Domain sans import de Pythos/ORM |

## 36.2 Conservation des critères d'acceptation V1

| ID V1 | Test V2 conservé |
|---|---|
| `AC-RULE-001` | Transition Project invalide -> refus |
| `AC-RULE-002` | Transition Task invalide -> refus |
| `AC-RULE-003` | Auto-dépendance -> refus |
| `AC-RULE-004` | Cycle de dépendance -> refus |
| `AC-RULE-005` | Prédécesseur bloquant ouvert -> démarrage refusé |
| `AC-RULE-006` | `DateRange` invalide -> construction impossible |
| `AC-RULE-007` | `Progress` hors bornes -> construction impossible |
| `AC-RULE-008` | `Project.COMPLETED` possède une date réelle de fin |
| `AC-RULE-009` | `TaskCompleted` est enregistré après transition réussie |
| `AC-RULE-010` | `Milestone.REACHED` possède `reached_at` |

## 36.3 Nouveaux critères d'acceptation

| ID | Condition observable | Jalon |
|---|---|---|
| `AC-RULE-V2-001` | Aucune collision de mapping externe entre scopes | M1 |
| `AC-RULE-V2-002` | Une observation ne change pas TaskStatus | M1 |
| `AC-RULE-V2-003` | Un statut PASS possède source et méthode vérifiables | M1 |
| `AC-RULE-V2-004` | Un snapshot historique ne change pas après mutation du projet | M1 |
| `AC-RULE-V2-005` | La reprise après restart restitue des données persistées | M1 |
| `AC-RULE-V2-006` | Un `NextAction` ne crée aucune Task | M1 |
| `AC-RULE-V2-007` | Une preuve périmée ne qualifie pas une référence courante différente | M1 |
| `AC-RULE-V2-008` | Une lecture inter-scope non autorisée ne fuit aucun détail sensible | M1 |
| `AC-RULE-V2-009` | Un rapport Pythos A1/A2 ne clôture ni n'approuve | M2 |
| `AC-RULE-V2-010` | Rejeu identique du rapport ne duplique pas les effets ; payload divergent est refusé | M2 |
| `AC-RULE-V2-011` | Une approbation est liée à une autorité, un scope et un objet précis | M1/M2 |
| `AC-RULE-V2-012` | Les gates G0-G7 sont optionnels pour les projets non logiciels | M2 |
| `AC-RULE-V2-013` | Un refus de commande n'émet aucun Domain Event de succès | M0 |
| `AC-RULE-V2-014` | Une clôture inter-agrégats ne s'appuie pas sur un snapshot obsolète | M0/M1 |
| `AC-RULE-V2-015` | Un import de source ambiguë conserve l'incertitude et réclame réconciliation | M1 |
| `AC-RULE-V2-016` | Une révision `RECONSTRUCTED` ne se présente jamais comme `ORIGINAL` | M1 |

## 36.4 Convention de nommage des tests

```text
test_<subject>_<observable_outcome>_when_<condition>
```

Exemples :

```python
def test_project_cannot_close_when_required_milestone_is_open(): ...
def test_task_cannot_start_when_blocking_dependency_is_not_done(): ...
def test_verification_cannot_pass_without_exact_source_reference(): ...
def test_pythos_report_cannot_approve_without_human_authority(): ...
def test_snapshot_remains_unchanged_after_project_update(): ...
```

**Ces noms sont des tests à écrire**, pas des tests déjà exécutés.

# 37. Matrice de traçabilité vers exigences et documents

| Famille de règles | Documents fondateurs | Documents de sortie à aligner |
|---|---|---|
| `INV-PROJ`, `INV-TASK`, `INV-DEP`, `INV-MILE` | Requirements V2, 04/05/06 V2 | `08` commandes, `09` events, `10` ports |
| `INV-CTX`, `INV-REG` | Définition V2, 04/05/06 V2 | `08`, `10`, `12` |
| `INV-SRC`, `INV-OBS`, `INV-EVID` | Requirements `FR-EVID`, 05/06 V2 | `08`, `09`, `10`, `11` |
| `INV-VER`, `INV-REC` | Architecture 39-41, 05/06 V2 | `08`, `11`, `12` |
| `INV-SNAP`, `INV-NEXT`, `INV-HAND` | Requirements `FR-CONT`, 05/06 V2 | `08`, `10` |
| `INV-DEC`, `INV-APPROVAL`, `BR-PORT` | 04/05/06 V2 et Pythos | `08`, `09`, `12` |
| `BR-PYTHOS`, `APP-PYTHOS` | Operating Model Pythos | `08`, `10`, `11`, `12` |
| `SEC-*`, `APP-UOW` | Architecture V2, 06 V2, sécurité V1 | `10`, `11`, `12` |
| Familles C3 | 07 V1, 04 V2 | Documents spécialisés futurs |

Le document `08` devra mettre à jour les commandes et queries, `09` les noms d'événements, `10` les boundaries des transactions et ports, `11` les erreurs, `12` l'autorisation. Aucune règle de ce document ne suffit à déclarer ces documents V1 déjà réconciliés.

# 38. Décisions de conception ouvertes et ADR candidats

| ADR candidat | Sujet | Proposition à examiner | Statut |
|---|---|---|---|
| `ADR-07-001` | Milestone | Entity interne à Project M0 | `PROPOSED` |
| `ADR-07-002` | Task | AR indépendant de Project | `PROPOSED` |
| `ADR-07-003` | DependencyGraph | Validation atomique selon backend | `PROPOSED` |
| `ADR-07-004` | State lifecycle | Enum + guards avant GoF State | `PROPOSED` |
| `ADR-07-005` | ClosurePolicy | Policy personnalisable par contexte | `PROPOSED` |
| `ADR-07-006` | ContextScope | VO + enforcement applicatif | `PROPOSED` |
| `ADR-07-007` | EvidenceRef | VO référencé, pas copie systématique | `PROPOSED` |
| `ADR-07-008` | Observation | Record historisé / append-only | `PROPOSED` |
| `ADR-07-009` | VerificationAssessment | Verdict scoped + provenance | `PROPOSED` |
| `ADR-07-010` | Snapshot | Read Model historique, pas Event Sourcing obligatoire | `PROPOSED` |
| `ADR-07-011` | NextAction | Projection avant nouvelle Task | `PROPOSED` |
| `ADR-07-012` | Reconciliation | Issue spécialisé avant aggregate dédié | `PROPOSED` |
| `ADR-07-013` | Portfolio | Policy Py*Kit optionnelle, pas universelle | `PROPOSED` |
| `ADR-07-014` | Pythos | DTO/adapters optionnels, sans import Domain | `PROPOSED` |
| `ADR-07-015` | Security | Vérification pré-agrégation + mandat | `PROPOSED` |
| `ADR-07-016` | Handoff | Historique immuable, non autoritatif | `PROPOSED` |

Ce tableau propose des décisions, ne les approuve pas. La coordination avec les ADR candidats du document 06 évitera les doublons ; le registre d'ADR final devra être unique.

# 39. Risques, anti-patterns et décisions de simplicité

| Risque | Symptôme | Réponse attendue |
|---|---|---|
| `God Project Aggregate` | Project charge toutes les tâches et preuves | AR séparés et references typées |
| `Schema-first domain` | Invariants dérivés uniquement d'un ORM | Domaine explicite, DB en renfort |
| `Documentation theater` | « V2 » interprété comme fonctionnalité livrée | Statuts probants et exact references |
| `Snapshot as truth` | Copie obsolète utilisée pour clôture | Relecture autoritative |
| `Evidence as approval` | CI verte produit release approuvée | Acte d'approbation distinct |
| `Agent as decision maker` | Pythos signe un gate réservé | Mandat et décision humaine |
| `Portfolio sprawl` | Every idea becomes an active repo | KEEP/MERGE/PARK/RETIRE sous policy |
| `Scope leakage` | Projection multi-projets révèle données client | Filtrage avant agrégation |
| `False historical replay` | Snapshot reconstruit appelé original | Indicateur de provenance |
| `Unbounded patterns` | Outbox/Saga/Event Sourcing imposés au M0 | KISS, livraison par tranches |
| `Derived NextAction mutates Task` | Recommandation considérée comme commande | Séparer Read Model et Commands |
| `Confused deputy` | L'agent agit via un connecteur plus privilégié | Contrôle d'autorité à la mutation |

# 40. Définition de prêt pour l'implémentation et prochain document

## 40.1 Critères documentaires de qualité

- [x] Identifiants V1 fondamentaux conservés.
- [x] Différence invariant / policy / précondition / sécurité explicitée.
- [x] Project, Task, dépendances et jalons couverts en M0.
- [x] Scope, registre, observations, preuves, vérifications, snapshots et handoffs couverts en M1.
- [x] Contrats Pythos M2 et limites A0-A5/G0-G7 explicités comme optionnels.
- [x] Règles avancées V1 conservées en C3.
- [x] Scénarios de tests positifs/négatifs et critères d'acceptation définis.
- [x] Sources de vérité, concurrence, échecs et sécurité traités.
- [ ] Validation humaine des propositions d'invariants nouvelles.
- [ ] ADR structurants acceptés.
- [ ] Tests d'implémentation M0 exécutés et référencés.
- [ ] Conformité réelle des adapters M1 et Pythos M2 qualifiée.

## 40.2 Prochaine étape documentaire

`08_PYPROJECTKIT_COMMANDS_QUERIES_AND_USE_CASES.md` doit traduire chaque règle en intention, préconditions, postconditions, erreur, transaction et événement éventuellement produit. Les décisions ouvertes des documents 05 à 07 devront être réconciliées **avant de figer** l'API publique et les migrations.

---

# Annexe A - Conservation des familles historiques V1

Le registre ci-dessous recense les identifiants historiques repérés dans le document 07 V1, sans prétendre que tous sont requis dans M0. Les lignes détaillées de la V1 continuent de faire référence pour les règles C3 tant que leurs contrats spécialisés n'ont pas été révisés. Une section regroupée n'abroge pas une règle : les changements de sens nécessitent un ADR.

| Identifiant conservé | Intitulé ou formulation d'origine (abrégé) | Traitement cible |
|---|---|---|
| `BR-GEN-001` | Aucune mutation métier arbitraire | M0 |
| `BR-GEN-002` | Toute Entity possède une identité stable | M0 |
| `BR-GEN-003` | Les Value Objects sont immuables | M0 |
| `BR-GEN-004` | Les références inter-aggregates utilisent des IDs typés | M0 |
| `BR-GEN-005` | Les dates métier doivent être cohérentes | M0 |
| `BR-GEN-006` | Les timestamps métier doivent être timezone-aware | M0 |
| `BR-GEN-007` | Les montants financiers incluent toujours une devise | M0 |
| `INV-PROJ-001` | Identité obligatoire | M0 |
| `INV-PROJ-002` | Nom obligatoire | M0 |
| `INV-PROJ-003` | Responsable obligatoire | M0 |
| `INV-PROJ-004` | Cohérence des dates planifiées | M0 |
| `INV-PROJ-005` | Cohérence des dates réelles | M0 |
| `INV-PROJ-006` | Projet actif démarré | M0 |
| `INV-PROJ-007` | Projet terminé clôturé | M0 |
| `INV-PROJ-008` | Projet annulé non actif | M0 |
| `BR-PROJ-001` | Planification | M0 |
| `BR-PROJ-002` | Démarrage | M0 |
| `BR-PROJ-003` | Mise en pause | M0 |
| `BR-PROJ-004` | Reprise | M0 |
| `BR-PROJ-005` | Annulation | M0 |
| `BR-PROJ-CLOSE-001` | Clôture refusée si policy échoue | M0 |
| `BR-PROJ-CLOSE-002` | Clôture atomique | M0 |
| `INV-TASK-001` | Identité obligatoire | M0 |
| `INV-TASK-002` | Projet obligatoire | M0 |
| `INV-TASK-003` | Titre obligatoire | M0 |
| `INV-TASK-004` | Pas d’auto-parent | M0 |
| `INV-TASK-005` | Dates cohérentes | M0 |
| `INV-TASK-006` | Progression bornée | M0 |
| `BR-TASK-START-001` | Une tâche ne peut démarrer que si son statut autorise la transition | M0 |
| `BR-TASK-START-002` | Une tâche ne peut pas démarrer si une dépendance bloquante n’est pas satisfaite | M0 |
| `BR-TASK-START-003` | Une tâche ne peut pas démarrer si le projet est : | M0 |
| `BR-TASK-START-004` | Une policy peut également interdire le démarrage si le projet est ON_HOLD | M0 |
| `BR-TASK-BLOCK-001` | Une tâche peut être bloquée uniquement depuis un état actif compatible | M0 |
| `BR-TASK-BLOCK-002` | Un blocage doit conserver une raison | M0 |
| `BR-TASK-BLOCK-003` | Une tâche bloquée ne peut pas être complétée sans déblocage explicite, sauf policy spécifique | M0 |
| `BR-TASK-DONE-001` | Une tâche ne peut être complétée que depuis : | M0 |
| `BR-TASK-DONE-002` | Une tâche terminée doit avoir : | M0 |
| `BR-TASK-DONE-003` | Une tâche terminée peut forcer : | M0 |
| `BR-TASK-DONE-004` | Une tâche déjà terminée ne doit pas être mutée une seconde fois par complete() | M0 |
| `INV-SUBTASK-001` | Pas de cycle hiérarchique | M0 |
| `BR-SUBTASK-001` | Parent même projet | M0 |
| `BR-SUBTASK-002` | Profondeur | M0 |
| `INV-DEP-001` | Pas d’auto-dépendance | M0 |
| `INV-DEP-002` | Pas de doublon logique | M0 |
| `INV-DEP-003` | Pas de cycle | M0 |
| `BR-DEP-001` | Validation du graphe | M0 |
| `INV-MILE-001` | Un jalon appartient à un projet | M0 |
| `INV-MILE-002` | Un jalon possède une date cible | M0 |
| `INV-MILE-003` | Un jalon atteint possède une date reached_at | M0 |
| `INV-MILE-004` | Un jalon non atteint ne doit pas avoir reached_at | M0 |
| `BR-DELIV-001` | Un livrable ne peut être accepté que si ses critères obligatoires sont satisfaits | M0 |
| `BR-DELIV-002` | Une validation finale peut exiger une Approval | M0 |
| `INV-MEMBER-001` | Un membre possède une identité métier propre | C3 ou M1 gouvernance |
| `INV-MEMBER-002` | Un membre PyProjectKit ne doit pas contenir de secrets d’authentification | C3 ou M1 gouvernance |
| `INV-MEMBERSHIP-001` | Le projet et le membre doivent être identifiés | C3 ou M1 gouvernance |
| `INV-MEMBERSHIP-002` | Si left_at existe : | C3 ou M1 gouvernance |
| `INV-MEMBERSHIP-003` | Une même adhésion active ne doit pas être dupliquée | C3 ou M1 gouvernance |
| `BR-ASSIGN-001` | Une tâche peut être affectée uniquement à un membre admissible | M0 |
| `BR-ASSIGN-002` | L’admissibilité peut être déterminée par une policy | M0 |
| `BR-ASSIGN-003` | Une affectation terminée doit conserver : | M0 |
| `INV-CAP-001` | Une capacité ne peut pas être négative | C3 ou M1 gouvernance |
| `BR-CAP-001` | Une allocation peut être refusée si elle dépasse la capacité disponible | C3 ou M1 gouvernance |
| `BR-CAP-002` | La stratégie doit être configurable : | C3 ou M1 gouvernance |
| `INV-SPRINT-001` | Un sprint appartient à un projet | C3 ou M1 gouvernance |
| `INV-SPRINT-002` | start_date <= end_date | C3 ou M1 gouvernance |
| `INV-SPRINT-003` | Un sprint CLOSED est immuable pour ses engagements principaux | C3 ou M1 gouvernance |
| `BR-SPRINT-001` | Un sprint ne peut démarrer avant sa date de début selon policy | C3 ou M1 gouvernance |
| `BR-SPRINT-002` | Deux sprints actifs simultanément peuvent être interdits ou autorisés par projet selon policy | C3 ou M1 gouvernance |
| `BR-SPRINT-003` | Un sprint clôturé ne doit pas accepter de nouvel item | C3 ou M1 gouvernance |
| `BR-SPRINT-004` | La vélocité doit être dérivée des éléments terminés | C3 ou M1 gouvernance |
| `BR-BACKLOG-001` | Un même WorkItem ne devrait pas apparaître deux fois dans le même backlog | C3 ou M1 gouvernance |
| `BR-BACKLOG-002` | Le ranking doit produire un ordre total ou partiel cohérent | C3 ou M1 gouvernance |
| `INV-RISK-001` | Un risque appartient à un projet | C3 ou M1 gouvernance |
| `INV-RISK-002` | Un risque possède une probabilité et un impact évaluables | C3 ou M1 gouvernance |
| `INV-RISK-003` | Le score doit être cohérent avec la policy de scoring active | C3 ou M1 gouvernance |
| `INV-RISK-004` | Un risque fermé ne peut pas être réescaladé sans réouverture explicite | C3 ou M1 gouvernance |
| `BR-RISK-001` | Le score doit être calculé via : | C3 ou M1 gouvernance |
| `BR-RISK-002` | Une implémentation simple peut utiliser : | C3 ou M1 gouvernance |
| `BR-RISK-003` | Une criticité supérieure à un seuil peut déclencher : | C3 ou M1 gouvernance |
| `BR-RISK-004` | Un risque matérialisé peut produire un Issue | C3 ou M1 gouvernance |
| `BR-RISK-005` | La matérialisation ne supprime pas nécessairement le risque | C3 ou M1 gouvernance |
| `INV-ISSUE-001` | Un issue appartient à un projet | C3 ou M1 gouvernance |
| `INV-ISSUE-002` | Un issue ouvert possède une date d’ouverture | C3 ou M1 gouvernance |
| `INV-ISSUE-003` | Un issue résolu possède une date de résolution | C3 ou M1 gouvernance |
| `INV-ISSUE-004` | opened_at <= resolved_at | C3 ou M1 gouvernance |
| `INV-ASSUMP-001` | Une hypothèse doit être exprimée explicitement | C3 ou M1 gouvernance |
| `BR-ASSUMP-001` | Une hypothèse invalidée peut générer : | C3 ou M1 gouvernance |
| `INV-DEC-001` | Une décision doit posséder : | C3 ou M1 gouvernance |
| `BR-DEC-001` | Une décision ne doit pas être supprimée silencieusement une fois appliquée | C3 ou M1 gouvernance |
| `INV-CR-001` | Une ChangeRequest appartient à un projet | C3 ou M1 gouvernance |
| `INV-CR-002` | Une ChangeRequest doit expliciter l’objet du changement | C3 ou M1 gouvernance |
| `INV-CR-003` | Les impacts doivent être évalués lorsqu’ils sont requis par policy | C3 ou M1 gouvernance |
| `BR-APPROVAL-001` | Une approbation doit avoir : | C3 ou M1 gouvernance |
| `BR-APPROVAL-002` | Une même personne peut être empêchée d’approuver sa propre demande selon policy | C3 ou M1 gouvernance |
| `BR-APPROVAL-003` | Un changement ne passe à APPROVED que si : | C3 ou M1 gouvernance |
| `BR-GATE-001` | Un gate ne peut être considéré comme franchi si ses critères obligatoires échouent | C3 ou M1 gouvernance |
| `BR-GATE-002` | Un gate peut exiger une ou plusieurs approbations | C3 ou M1 gouvernance |
| `INV-REVIEW-001` | Une review doit cibler un sujet métier explicite | C3 ou M1 gouvernance |
| `BR-REVIEW-001` | Une review terminée peut produire des ActionItem | C3 ou M1 gouvernance |
| `INV-ACTION-001` | Une action possède : | C3 ou M1 gouvernance |
| `BR-ACTION-001` | Une action clôturée ne peut pas redevenir ouverte sans opération explicite | C3 ou M1 gouvernance |
| `INV-WORKLOG-001` | Un worklog possède : | C3 ou M1 gouvernance |
| `INV-WORKLOG-002` | La durée doit être strictement positive | C3 ou M1 gouvernance |
| `INV-WORKLOG-003` | Un worklog ne peut pas être associé à un membre inexistant dans le contexte applicatif | C3 ou M1 gouvernance |
| `INV-TIME-001` | Une timesheet concerne un membre et une période | C3 ou M1 gouvernance |
| `INV-TIME-002` | Les worklogs inclus doivent appartenir au même membre | C3 ou M1 gouvernance |
| `INV-TIME-003` | Une timesheet approuvée peut être rendue immuable | C3 ou M1 gouvernance |
| `INV-BUDGET-001` | Un budget appartient à un projet | C3 ou M1 gouvernance |
| `INV-BUDGET-002` | Un budget possède une devise de référence | C3 ou M1 gouvernance |
| `INV-BUDGET-003` | Les lignes du budget doivent utiliser la même devise de référence ou une conversion explicite | C3 ou M1 gouvernance |
| `INV-BUDGET-004` | Les montants ne doivent pas être représentés en float | C3 ou M1 gouvernance |
| `BR-BUDGET-001` | Une baseline budgétaire approuvée devient immuable | C3 ou M1 gouvernance |
| `BR-BUDGET-002` | Toute modification de baseline doit produire une nouvelle version ou une ChangeRequest selon policy | C3 ou M1 gouvernance |
| `INV-BUDGETLINE-001` | Une ligne appartient à exactement un budget | C3 ou M1 gouvernance |
| `INV-BUDGETLINE-002` | Le montant alloué doit respecter : | C3 ou M1 gouvernance |
| `INV-COST-001` | Un coût possède : | C3 ou M1 gouvernance |
| `INV-COST-002` | Un coût réel ne peut pas avoir un montant invalide ou une devise absente | C3 ou M1 gouvernance |
| `INV-PROGRAM-001` | Un programme possède une identité et un nom | C3 ou M1 gouvernance |
| `INV-PROGRAM-002` | Les projets référencés doivent rester des Aggregate Roots séparés | C3 ou M1 gouvernance |
| `INV-PORT-001` | Un portefeuille possède une identité stable | C3 ou M1 gouvernance |
| `INV-PORT-002` | Un portefeuille peut contenir : | C3 ou M1 gouvernance |
| `BR-PORT-001` | La priorisation doit passer par : | C3 ou M1 gouvernance |
| `BR-PORT-002` | Les dimensions de scoring doivent être explicites | C3 ou M1 gouvernance |
| `BR-HEALTH-001` | La santé globale doit être dérivée via : | C3 ou M1 gouvernance |
| `BR-HEALTH-002` | Elle ne doit pas être saisie arbitrairement comme vérité métier | C3 ou M1 gouvernance |
| `BR-HEALTH-003` | Une stratégie simple peut utiliser : | C3 ou M1 gouvernance |
| `BR-PROGRESS-001` | Un projet ne doit pas automatiquement calculer son avancement uniquement par nombre de tâches | C3 ou M1 gouvernance |
| `BR-PROGRESS-002` | La progression peut être : | C3 ou M1 gouvernance |
| `INV-DATE-001` | start <= end | M0 |
| `INV-DATE-002` | Une période vide n’est acceptable que si le modèle l’autorise explicitement | M0 |
| `INV-DUR-001` | Une durée ne peut pas être négative | M0 |
| `INV-MONEY-001` | Le montant utilise Decimal | C3 ou M1 gouvernance |
| `INV-MONEY-002` | La devise est obligatoire | C3 ou M1 gouvernance |
| `INV-MONEY-003` | Addition autorisée uniquement entre devises compatibles | C3 ou M1 gouvernance |
| `INV-MONEY-004` | Toute conversion doit être explicite | C3 ou M1 gouvernance |
| `INV-PERCENT-001` | Par défaut : | M0 |
| `INV-VERSION-001` | Une version d’Entity doit être monotone | M0 |
| `BR-VERSION-001` | Une tentative d’écriture avec version obsolète doit produire : | M0 |
| `BR-IDEMP-001` | Le rejeu d’une même commande externe ne doit pas créer de duplication métier | M0 |
| `BR-ARCH-001` | Un objet archivé reste consultable | C3 ou M1 gouvernance |
| `BR-ARCH-002` | L’archivage n’efface pas son historique métier | C3 ou M1 gouvernance |
| `BR-EVT-001` | Un événement représente un fait passé | M0 |
| `BR-EVT-002` | Un événement ne doit être émis qu’après mutation métier valide | M0 |
| `BR-EVT-003` | Les événements doivent être déterministes par rapport à l’état et à la commande | M0 |
| `AC-RULE-001` | Une transition projet invalide lève InvalidStateTransition | M0 |
| `AC-RULE-002` | Une transition tâche invalide lève InvalidStateTransition | M0 |
| `AC-RULE-003` | Une auto-dépendance est rejetée | M0 |
| `AC-RULE-004` | Un cycle de dépendances est rejeté | M0 |
| `AC-RULE-005` | Une tâche bloquée par dépendance ne peut pas démarrer | M0 |
| `AC-RULE-006` | Un DateRange incohérent est impossible à construire | M0 |
| `AC-RULE-007` | Un Progress hors bornes est impossible à construire | M0 |
| `AC-RULE-008` | Un projet terminé possède une date de fin réelle | M0 |
| `AC-RULE-009` | Une tâche terminée émet TaskCompleted | M0 |
| `AC-RULE-010` | Un jalon atteint possède reached_at | M0 |

**Note de migration** : pour les règles de niveau `C3 ou M1 gouvernance`, la V2 conserve l'identifiant et le domaine mais différencie leur activation par une policy spécifique. Le libellé abrégé ci-dessus n'est pas le texte normatif intégral de la V1 ; la règle détaillée doit être relue lors de l'activation du module.

---

# Annexe B - Réconciliation des identifiants provisoires du document 06 V2

| Identifiant document 06 | Contrat porté dans le document 07 V2 | Décision |
|---|---|---|
| `INV-REL-001` | `INV-TASK-007` | Référence ProjectId valide et scope géré |
| `INV-REL-002` | `INV-TASK-008` / `APP-MILE-001` | Jalons et tâches du même projet |
| `INV-REL-003` | `INV-SUBTASK-001` et `APP-DEP-001` | Cycles parenté, concurrence |
| `INV-REL-004` | `INV-DEP-001`, `INV-DEP-003` | Pas d'auto-lien ni de cycle |
| `INV-REL-005` | `BR-ARCH-002`, `APP-ARCH-003`, `SEC-010` | Pas d'effacement implicite, rétention applicable |
| `INV-REL-006` | `INV-REG-002`, `INV-TRUTH-001` | Projection non autoritative |
| `INV-REL-007` | `INV-EVID-004`, `SEC-CTX-002` | Respect des droits d'accès à la source |
| `INV-REL-008` | `INV-VER-002` | Verdict exige méthode, source et résultat |
| `INV-REL-009` | `INV-DEC-002`, `INV-APPROVAL-001` | Observation d'agent distincte de décision |
| `INV-REL-010` | `INV-SRC-003`, `APP-SRC-002` | Réconciliation avant fusion d'identités |

Les identifiants `INV-REL-*` restent des références historiques de conception dans `06 V2`, pas un second registre de tests. Une fois la révision validée, le document 06 devrait renvoyer aux ID canoniques du document 07.

---

# Annexe C - Matrice de contrôle des sources et des versions

| Affirmation | Source attendue | Source insuffisante seule | Réaction en cas de manque |
|---|---|---|---|
| « Une tâche est terminée » | Task gérée et transition valide | Message conversationnel | Ne pas promouvoir TaskStatus |
| « Les tests sont verts » | Run CI/tests exacts, conclusion, référence | Capture sans cible identifiable | `UNKNOWN` ou `PARTIAL` |
| « La version est qualifiée » | Rapport de qualification et références exactes | `Task.DONE` ou CI d'une autre branche | Aucune élévation |
| « Le package est publié » | Artefact registry/tag/release identifié | Numéro de version dans pyproject | `NOT_PROVEN` |
| « Le client a accepté » | Décision ou approbation de l'autorité client | Livrable livré | `PENDING` |
| « Nous avons l'autorisation d'exécuter » | Mandat et permissions effectives | Operating Brief éditable seul | Refus d'effet |
| « Le snapshot est le passé original » | Capture datée avec provenance originale | Reconstitution a posteriori | `RECONSTRUCTED` |
| « Ce projet est prioritaire » | Décision de portefeuille habilitée | Suggestion Pythos | Proposition uniquement |

---

# Annexe D - Design Learning Notes

| Pression constatée | Solution simple envisagée | Évolution seulement si justifiée | Preuve à rechercher |
|---|---|---|---|
| Transitions simples | Enum + méthodes protégées | State Pattern en cas de comportement polymorphe | Tests de transitions |
| Tâches indépendantes | `ProjectId` typé dans Task | Coordination applicative | Tests de références et concurrents |
| Dépendances | Graphe et vérification topologique | Moteur de planification avancé plus tard | Cycles et conflits |
| Contexte inter-sessions | Snapshot immuable | Event Sourcing seulement avec besoin de replay | Restart et intégrité |
| Connexion GitHub | Référence, observation, adapter | Synchronisation bidirectionnelle après cas réel | Tests de contrat et conflit |
| Recommandation de travail | Read Model NextAction | Planificateur autonome si besoin réel | Non-mutation des Tasks |
| Collaboration Pythos | DTO + ports optionnels | Workflows automatiques à mandat fin | Autorisation et idempotence |
| Détection de maturité | Policy spécialisée et références | Confiance calculée seulement si explicable | Exact commit + preuves |

**Leçon** : `SourceRef` ne signifie pas `Evidence`, `Evidence` ne signifie pas `Verification`, `Verification` ne signifie pas `Approval`, et `Approval` ne signifie pas nécessairement `ProjectCompleted`. C'est une distinction de domaine, pas un catalogue de patterns GoF.

---

# Annexe E - Journal de révision et statut

| Version | Date | Évolution | Statut |
|---|---|---|---|
| V1 | Historique | Noyau de règles Project, Task, Dependence, Agile, RAID, gouvernance, budget et événements | Document source préservé |
| V2.0.0 | 2026-11-02 | Classification des règles, M0/M1/M2/C3, nouvelles familles de provenance, snapshot, décision, sécurité et Pythos ; conservation des identifiants V1 | `REVIEW` |

**Décision proposée** : `CONDITIONAL GO` pour la révision documentaire, sous réserve de validation des invariants nouveaux, d'arbitrage des ADR à impact, et de réconciliation avec les contrats des documents 08 à 12. Aucun GO technique ni aucune qualification runtime n'est affirmé.
