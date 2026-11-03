# R0-04 / R0-05 - Dossier d'arbitrages pour autoriser le noyau M0

> Statut : PROPOSED - REVIEW REQUIRED
>
> Date : 2026-11-03
>
> Aucun choix de ce document n'est `ACCEPTED`. Décideur humain et références d'acceptation : PENDING.
>
> Prérequis : matrice de réconciliation V2, glossaire R0-03, crosswalk ADR R0-10.

## Décision D-01 - Frontières d'agrégats

**Problème :** sauvegarder les états Project et Task tout en évitant d'avoir à charger toutes les tâches d'un projet.

**Option A (préférée) :** `Project` et `Task` AR séparés, reliés par `ProjectId` ; invariant inter-AR coordonné dans le use case/UoW.

**Option B :** Task intégrée au Project (God Aggregate potentiel).

**Compromis :** A réduit la contention et évite le chargement profond, mais oblige à gérer explicitement la cohérence de clôture, le rattachement et les courses entre écritures.

**Preuves futures :** roundtrip de Task, contrôle du Project parent, fermeture refusée si critère inter-AR non satisfait, test de concurrence selon adapter.

**Sources :** 05 §§8-9 ; 06 §§3,11 ; 07 §§8-9 ; 10 §§10-11. Ref de suivi : `ADR-PJ-RM-01`.

## Décision D-02 - Milestone

**Option A (préférée) :** Entity interne à Project, persistée par `ProjectRepository`.

**Option B :** AR autonome avec `MilestoneRepository`.

**Compromis :** A garde les invariants simples M0 ; B peut devenir utile si forte concurrence ou historique propre démontrés.

**Preuves :** target_date exigée, `reached_at` cohérent, changements atomiques via Project. Sources : 05 §10 ; 07 §11 ; 10 §14. Réf : `ADR-PJ-RM-02`.

## Décision D-03 - Dépendances et concurrence

**Option A (préférée) :** snapshot de graphe par Project avec révision commune et écriture conditionnelle `replace_if_version` dans une UoW.

**Option B :** écriture d'edges indépendants après vérification en mémoire.

**Compromis :** A apporte un point de concurrence explicite, mais impose un port supplémentaire ; B est plus simple et insuffisant si deux transactions créent un cycle à partir d'instantanés obsolètes.

**Limite annoncée :** tester l'adapter InMemory n'autorise pas à affirmer la sûreté concurrente d'un backend SQL futur.

**Preuves :** insertion A->B puis B->A refusée ; concurrence simulée et absence de mutation partielle ; audit de la garantie annoncée. Sources : 07 §10, 10 §15, 11 §16. Réf : `ADR-PJ-RM-03`.

## Décision D-04 - UoW et résultat de commit

**Option A (préférée) :** `UnitOfWork` synchrone, commit explicite, rollback à la sortie sans commit, repositories partagés dans la même frontière transactionnelle.

**Option B :** commits cachés dans chaque Repository.

**Compromis :** A a une abstraction légère à tester ; B est trompeuse pour une commande modifiant Project et Task ensemble. Un timeout après envoi du COMMIT peut être `CommitOutcomeUnknown`, ni succès ni rollback certain.

**Preuves :** commit unique, sans commit, exception, conflit de version, retour de copies isolées, issue inconnue. Sources : 10 §§17-19, 11 §§17-20. Réf : `ADR-PJ-RM-05`.

## Décision D-05 - Autorisations minimales

**Option A (préférée) :** `ActorContext` fiable fourni par l'hôte + `AuthorizationPolicy` injectée ; deny par défaut, permission et scope projet contrôlés pour Commands et Queries.

**Option B :** sécurité uniquement en API web, sans contrôle dans Application.

**Compromis :** A oblige à fournir une policy explicite à la composition, mais protège les usages CLI/API et les Readers. Pas de fournisseur IAM imposé.

**Preuves :** cas négatifs `SEC-M0-01..06` ; aucun nombre ou ID hors scope en lecture. Source : 12 §§4, 13-17 ; 10 §19. Réf : `ADR-PJ-RM-10` (périmètre M0 uniquement).

## Décision D-06 - API, langage, événements

**Option A (préférée) :** noyau synchrone headless ; commandes `PutProjectOnHold` / `MarkTaskReady`, événements `ProjectPutOnHold` / `TaskMarkedReady` ; `Task` AR, `WorkItem` concept ; événements de succès seulement après commit confirmé.

**Option B :** conserver plusieurs noms publics pour la même transition et émettre les événements pendant le traitement avant commit.

**Compromis :** A simplifie le langage et les garanties ; il faudra documenter toute compatibilité V1 voulue. L'ordre global des événements et leur livraison réseau ne sont pas garantis en M0.

**Preuves :** un événement par transition validée, aucun sur refus ou rollback ; tests d'import sans Pythos. Sources : 07 §8, 08 §§9-11, 09 §§8,10-13. Réfs : `ADR-PJ-RM-04/06`.

## Décision D-07 - Baseline Python et package

**Options :** `requires-python >=3.12` (proposition documents) ou politique de compatibilité différente justifiée par des consommateurs réels.

**À vérifier :** environnements réels ciblés, versions des actions CI, licence, nom/package et version initiale ; la chaîne `0.1.0a1` du bootstrap est uniquement illustrative.

**Preuves :** build/test/import sur matrice explicitement décidée ; aucune release avant validation des métadonnées.

**Sources :** Vision 00 V2 et bootstrap 14 §8. Réf : `ADR-PJ-RM-04`.

## Livrables d'une revue humaine

| ID | Résolution humaine | Référence | Statut actuel |
|---|---|---|---|
| D-01 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-02 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-03 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-04 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-05 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-06 | Accept / Revise / Reject | PENDING | PROPOSED |
| D-07 | Accept / Revise / Reject | PENDING | PROPOSED |

Les tests proposés sont des critères de qualification futurs, pas des contrôles déjà exécutés. La décision de merge de cette PR documentaire ne vaut pas à elle seule `Q-R0 = GO`.

## Précondition documentaire commune aux sept décisions : D-SEM-01

La [revue directe des 12 sources V1](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) a établi des collisions d'identifiants dans 07 V2. Elles doivent être corrigées dans la future baseline avant de valider les contrats M0 et d'écrire des tests par identifiant. La [proposition de remédiation](R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md) conserve les sens V1 et réserve des IDs V2 nouveaux.

**Statut D-SEM-01 : ACCEPTED - option A ([trace humaine](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491)).** Le blocage de décision sémantique est levé. Il reste à intégrer la correction dans la baseline et à valider les options techniques D-01..D-07, qui restent `PROPOSED`.

## Décomposition en fiches de décision individuelles, version de revue

Les sept arbitrages de cette note sont maintenant détaillés dans les fiches [D-01](../adr/proposals/D-01_PROJECT_TASK_AGGREGATE_BOUNDARIES.md), [D-02](../adr/proposals/D-02_MILESTONE_OWNERSHIP_AND_DATES.md), [D-03](../adr/proposals/D-03_DEPENDENCY_GRAPH_CONCURRENCY.md), [D-04](../adr/proposals/D-04_UNIT_OF_WORK_AND_FAILURE_SEMANTICS.md), [D-05](../adr/proposals/D-05_APPLICATION_AUTHORIZATION_M0.md), [D-06](../adr/proposals/D-06_PUBLIC_COMMANDS_AND_DOMAIN_EVENTS.md) et [D-07](../adr/proposals/D-07_PYTHON_PACKAGING_AND_COMPATIBILITY.md).

Le [tableau de revue](R0-04_ARCHITECTURE_DECISION_REVIEW_BOARD.md) et [l'issue GitHub #5](https://github.com/tawounfouet/pyprojectkit/issues/5) concentrent les approbations et les réserves. Aucun D-01..D-07 n'a encore une décision humaine `ACCEPTED`.
