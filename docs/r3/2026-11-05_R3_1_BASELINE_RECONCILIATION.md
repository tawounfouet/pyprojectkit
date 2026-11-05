# R3.1 - Baseline et réconciliation M0/M1/M2 avant convergence ProjectHub

> Date du constat : 2026-11-05  
> Projet : PyProjectKit  
> Nature : rapport documentaire et registre de stabilité, non décision de release  
> Statut : `REVIEW / BASELINE_CAPTURED / REMEDIATIONS_OPEN`  
> Référence : `main@a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`  
> Portée : synthétique / locale pour les garanties M1/M2 ; aucune autorisation de données réelles ni de production  
> Cadre : R3.1 avant tout arbitrage R3.2 ou implémentation M3-A

## 0. Décision de méthode

L'existant doit être stabilisé par une **baseline traçable**, sans refonte générale du domaine, sans migrations nouvelles et sans promesse de portabilité non démontrée. Ce dossier enregistre l'état des lieux, les écarts documentaires et les garde-fous. Il ne modifie aucune règle métier.

Le présent dossier ne signe aucun ADR, ne vaut ni `Q-M2=GO`, ni approbation de fusion, ni autorisation de publier ou d'exploiter PyProjectKit. La branche de travail et sa PR sont des propositions à revoir.

## 1. Sources et précédence

1. Exigences V2 : sémantique des `FR`, `NFR`, `AC`, dont `AC-038..040`.
2. Invariants et architecture V2 : frontières de domaine, sécurité scoped, provenance et sémantique d'échec.
3. Code GitHub à SHA exact et pipeline GitHub Actions : comportement et implémentation observables.
4. Rapports de qualification : résultats bornés à leur environnement et leur SHA.
5. Décisions humaines : seul fondement de l'adoption des ADR, des gates et de la release.
6. Plans `26` et `27` : propositions à réconcilier, non vérités normatives nouvelles.

Une documentation descriptive en retard ne doit pas rétrograder un code déjà intégré ; symétriquement, une CI verte ne crée pas d'approbation humaine.

## 2. Baseline GitHub vérifiée

| Dimension | État vérifié le 2026-11-05 | Référence |
|---|---|---|
| Dépôt | `tawounfouet/pyprojectkit`, `main` | [Repository](https://github.com/tawounfouet/pyprojectkit) |
| SHA | `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38` | [Commit](https://github.com/tawounfouet/pyprojectkit/commit/a523d9c61c30ef41afe3bc9cf0723beafe3c2d38) |
| Fusions M2-A, B, C | PR [#16](https://github.com/tawounfouet/pyprojectkit/pull/16), [#17](https://github.com/tawounfouet/pyprojectkit/pull/17), [#18](https://github.com/tawounfouet/pyprojectkit/pull/18) fusionnées | GitHub |
| CI sur `main` | Run [41919258680](https://github.com/tawounfouet/pyprojectkit/actions/runs/41919258680) SUCCESS, Python 3.12/3.13 | 168 tests par version, mypy strict et wheel smoke |
| Version | `0.2.0a1`, `requires-python >=3.12`, aucune dépendance runtime obligatoire | `pyproject.toml` |
| Structure | `src/pyprojectkit/{domain,ports,service,memory}.py`, `m1/`, `m2/` | Arbre Git au SHA |
| Persistance | In-memory M0 ; SQLite M1 et M2 ; migrations 0001, 0002, 0003 | `m1/schema.py`, `m1/sqlite.py` |
| Protection de main | `protected=false` | [Issue #19](https://github.com/tawounfouet/pyprojectkit/issues/19) |
| Repository rulesets | Liste vide (`[]`) | API GitHub |
| Revue indépendante PR #16/#17/#18 | Aucune review soumise dans les vérifications réalisées | [Issue #20](https://github.com/tawounfouet/pyprojectkit/issues/20) |
| Gate humain Q-M2 | `PENDING`, AC-031 et AC-034 `PARTIAL` | Matrice Q-M2, issue #20 |
| Publication / release | Aucune release GitHub constatée ; aucune approbation de publication | [Issue #13](https://github.com/tawounfouet/pyprojectkit/issues/13) |

**Limite du contrôle :** les résultats CI sont lus depuis les workflows existants, pas réexécutés localement dans la présente livraison. Le statut reste celui du SHA cité.

## 3. Inventaire des contrats et garanties à préserver

### M0 - Noyau de domaine

- `Project` et `Task` sont des objets métier distincts, avec identités UUID typées, versions et transitions validées.
- `Milestone` appartient au projet ; `Dependency` et `assert_acyclic` protègent le graphe des tâches.
- `ports.py` expose `ProjectRepository`, `TaskRepository`, `DependencyGraphPort`, `UnitOfWork`, `Clock`, `IdFactory` et `AuthorizationPolicy`.
- `ProjectService` applique des permissions, l'isolement de scope, les validations de transitions et publie des Domain Events après commit.
- `InMemoryUnitOfWork` utilise des snapshots/copies, versions optimistes, verrou et staging des événements.

**Garde-fous :** ne changer ni les noms/exports publics, ni les transitions, ni la direction des imports, ni la règle de commit/event. Le contexte `ActorContext` M0 reste une frontière hôte supposée fiable ; il n'apporte pas en soi les garanties `VerifiedActor` M1.

### M1 - Registre durable, preuves et continuité

- `RegistryService` et `SqliteUnitOfWork` portent le registre, les historiques append-only, les observations, reconciliations, décisions, snapshots et handoffs.
- `TrustedHost` émet `VerifiedActor` ; les listes et agrégats sont filtrés avant counts/facettes/pagination.
- Visibilité : owner ou partage explicite, avec règles supplémentaires pour `PRIVATE`.
- SQLite dispose de versions CAS, `BEGIN IMMEDIATE`, migrations checksummées et backup via API SQLite.
- `PortfolioPage` constitue une projection de registre, non un agrégat `Portfolio` universel.

**Garde-fous :** conserver la migration 0001..0003 sans altération, le traitement de `UNKNOWN` et la confidentialité des listes/exports. Ne pas assimiler le contrôle in-process à une isolation contre du code hostile.

### M2 - Mandats et rapports synthétiques

- `WorkItemRef(kind="TASK")` reste un contrat M2 explicite, non un agrégat `WorkItem` universel.
- Les briefs et reports sont des DTO versionnés et des déclarations ; ils ne sont pas des droits exécutoires ni des preuves de succès.
- Mandats vérifiés côté hôte, TTL, scope, révocation, cible exacte et autorisations en lecture.
- Inbox SQLite et reçus avec idempotence, `CommitOutcomeUnknown`, reprise/reconciliation et vérification séparée.
- `ResumeWorkItemQuery` matérialise sections absentes/périmées et références de provenance.

**Garde-fous :** pas de vrai runtime Pythos, pas de commandes `merge/publish/delete`, pas de promotion de report en `Task DONE` ou `assessment PASS` et aucune décision humaine simulée.

## 4. Écarts constatés à traiter en R3.1

| ID | Gravité | Écart | Action proposée | Statut |
|---|---|---|---|---|
| R31-01 | P0 | `main` non protégée et aucune ruleset | Configurer checks obligatoires, revues, anti-force-push ; relire preuve | `OPEN / #19` |
| R31-02 | P0 | Gate Q-M2 indépendant absent ; AC-031/034 partiels ; ADR M2 non signés | Examen humain, risques/exclusions, verdict séparé | `OPEN / #20` |
| R31-03 | P0 doc | `docs/ROADMAP_TRACKING.md` commence par `M0 NOT_STARTED` | Préserver historique et ajouter un addendum vérifié daté | `IN_PR` |
| R31-04 | P1 doc | README décrit prototype M0/M1 et 41 tests ; `pyproject.toml` décrit M0/M1 | Émettre correction descriptive ciblée (non versionnage automatique) | `OPEN` |
| R31-05 | P0 plan | Document 26 et illustration 27 utilisent les mêmes IDs M3-01..06 différemment | Matrice 26/27, pas de tickets M3 créés avant arbitrage | `IN_PR / BLOCKED_SOURCE_27` |
| R31-06 | P1 | `RegistryService` et plusieurs services M2 manipulent SQLite directement | Audit des ports et contrats lors de R3.2/M3-A, pas de refactor R3.1 | `DEFERRED_TO_R3_2` |
| R31-07 | P1 | `requires-python >=3.12`, CI limitée à 3.12/3.13 | Décider matrice de compatibilité et politique futures versions | `OPEN` |
| R31-08 | P1 | Licence absente et politique d'exploitation non qualifiée | Conserver blocage release, suivre [#13](https://github.com/tawounfouet/pyprojectkit/issues/13) | `OPEN` |
| R31-09 | P1 doc | Les plans 26/27 ne figurent pas dans le dépôt `main` | Indexer les sources et importer la version 27 complète après récupération | `OPEN` |

La priorité P0 d'un écart documentaire indique un blocage de la traçabilité, pas nécessairement une défaillance du code.

## 5. Décisions encore ouvertes

| Objet | État | Autorité nécessaire |
|---|---|---|
| `D-SEM-01` | ACCEPTED sur compatibilité d'identifiants de règles, portée documentaire limitée | Décision déjà enregistrée |
| D-01..D-07 | Adoption alpha conditionnelle documentée, ne présume pas de validation universelle | Revue d'architecture |
| ADR-M2-01..08 | PROPOSED / revue indépendante requise | Reviewer habilité |
| Q-M2 | HUMAN_GATE_PENDING ; 9 `PASS_SYNTHETIC`, 2 `PARTIAL` | Reviewer humain indépendant |
| Protection `main` | OPEN / non effective | Admin du dépôt |
| ADR-M3-01..11 | PROPOSED dans le plan 26 | Autorités de conception et gate correspondant |
| Modèle `WorkItem`, `Portfolio`, `ContextScope`, stratégie persistence | À arbitrer en R3.2, pas décidé en R3.1 | Product Owner / Domain Owner / Architecte |

## 6. Règles de non-régression requises avant R3.2 / M3-A

1. Tests M0 : transitions, dépendances acycliques, transactions atomiques, versions concurrentes, événements après commit.
2. Tests M1 : migrations 0001..0003 et checksums, restauration, contrôle owner+scope, redaction, résultats `UNKNOWN`, historique append-only, reprise.
3. Tests M2 : briefs/report stricts, mandats, révocation, idempotence et `CommitOutcomeUnknown`, aucune élévation vers `PASS`, `DONE` ou une autorisation de publication.
4. CI : au minimum les deux jobs actuels (3.12/3.13), mypy strict, wheel isolée et démonstrations synthétiques ; toute extension doit ajouter ses propres tests.
5. Sécurité : aucun accès par simple `actor_id` client ; filtrer avant agrégation/pagination ; aucune donnée sensible ou exécution distante.
6. Compatibilité : préserver les imports du package et l'absence de dépendance obligatoire à Django/FastAPI/PostgreSQL/Pythos.
7. Évidence : conserver SHA précis, job et résultat ; ne pas déclarer `Q-M2`, `Q-M3` ou release approuvés d'après la seule CI.

## 7. Sorties vérifiables R3.1

| Sortie | État dans cette livraison |
|---|---|
| Baseline SHA, CI, structure, version et limites | `DOCUMENTED` |
| Décalage roadmap et documentation | `DOCUMENTED / ADDENDUM_PROPOSED` |
| Crosswalk 26/27 et différences de planification | `DOCUMENTED_PARTIAL`, illustration 27 seule |
| Liste des décisions et autorités | `DOCUMENTED / GATES_PENDING` |
| Matrice de garanties M0/M1/M2 | `DOCUMENTED`, CI antérieure utilisée |
| Refactor ou migration de code | `NOT_EXECUTED_BY_DESIGN` |
| Revue / adoption humaine | `PENDING` |
| Mise à jour du README et de `pyproject.toml` | `PENDING_SEPARATE_DOC_PR` |

## 8. Critère de sortie R3.1

R3.1 ne peut être déclaré `CLOSED` que lorsque :
- les documents de baseline et crosswalk sont approuvés ;
- `docs/ROADMAP_TRACKING.md` ne présente plus un historique comme statut présent ;
- la source intégrale de 27 est obtenue et les collisions d'IDs sont arbitrées, ou l'incertitude est formellement enregistrée avec un propriétaire ;
- les réserves #19/#20 sont traitées ou font l'objet d'exceptions formelles documentées ;
- les tests de non-régression sont conservés au SHA qui fera l'objet de la revue.

**Verdict à la création :** `R3_1 = PARTIAL / REVIEW_REQUIRED` ; `M3_IMPLEMENTATION = NOT_STARTED` ; `MAIN_MUTATION = NONE` ; `Q_M2 = HUMAN_PENDING`.

## 9. Suites

- Obtenir le texte intégral de `27_PYPROJECTKIT_M3A_IMPLEMENTATION_PLAN.md` et signer le crosswalk.
- Résoudre la gouvernance (#19 et #20) sans inventer de reviewer ni de protection active.
- Préparer R3.2 : ADR sur frontières métier, adaptateurs, scopes, ports/UoW et intégration Django.
- Autoriser M3-01 seulement après décision humaine du périmètre et relecture du SHA de `main`.

## 10. Liens

- [CI main post-merge](https://github.com/tawounfouet/pyprojectkit/actions/runs/41919258680)
- [Issue #19 : protection de main](https://github.com/tawounfouet/pyprojectkit/issues/19)
- [Issue #20 : revue Q-M2](https://github.com/tawounfouet/pyprojectkit/issues/20)
- [Issue #13 : release hardening](https://github.com/tawounfouet/pyprojectkit/issues/13)
- Plan 26 M3 : texte intégral fourni dans le projet ChatGPT, non importé dans `main` au contrôle du 2026-11-05.
- [Crosswalk R3.1](2026-11-05_R3_1_M3_26_27_CROSSWALK.md)
- [Contrat de non-régression M0/M1/M2](2026-11-05_R3_1_NON_REGRESSION_CONTRACT.md)
