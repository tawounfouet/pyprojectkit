# R0-02 - Première revue de cohérence V2 (ciblée M0)

> Date : 2026-11-03
>
> Statut : PARTIAL_AUDIT / REVIEW
>
> Périmètre : première lecture croisée des parties pertinentes des documents V2 `05` à `12`, complétée par roadmap 13 et bootstrap 14.
>
> Autorité : aucune décision métier ou ADR acceptée par cette note.

Cette première passe ne remplace pas l'audit transversal exhaustif R0-02. Les conclusions indiquent si les textes **semblent cohérents entre eux** sur le point étudié ; elles ne certifient aucune API ni test.

## Résultats initiaux

| GAP | Qualification initiale | Constats établis | Suite |
|---|---|---|---|
| GAP-01 - Task vs WorkItem | `NO_CONFLICT_IN_V2` | 05 V2 §9.3, 06 V2 §18, 07 V2 §9.3 et 08 V2 APP-V2-008 convergent : WorkItem = langage commun, Task = AR concret M0 ; pas d'agrégat WorkItem universel imposé | Transformer en glossaire R0-03 ; vérifier compatibilité V1 et Pythos |
| GAP-02 - frontières DDD | `ALIGNED_PROPOSED` | 05 V2 §8-9, 06 V2 §3.2, 07 V2 et 09 V2 §8 convergent : Project/Task AR distincts ; Milestone dans Project ; Dependency VO/lien | Présenter ADR-PJ-RM-01/02/03 à l'autorité ; décisions toujours ouvertes |
| GAP-03 - concurrence du graphe | `OPEN_RISK / DECISION_REQUIRED` | 11 V2 §16 précise qu'un graphe sans cycle dans un test séquentiel peut subir des écritures concurrentes incompatibles ; 06/10 V2 demandent une frontière cohérente | Définir une garantie explicite InMemory et les limites de concurrence ; test de course avant revendication |
| GAP-04 - UoW et erreurs | `ALIGNED_PROPOSED` | 08 V2 §7.1, 10 V2 §17, 11 V2 §17 conviennent d'un commit explicite, rollback sans commit, erreur de commit non présumée validée, et réconciliation si issue inconnue | Définir les signatures et tests de contrat M0, vérifier les cas limites |
| GAP-05 - Domain Events | `ALIGNED_PROPOSED` | 08 V2 §7.1 et 09 V2 §8 prévoient aucun événement de succès si mutation refusée et aucune promesse de livraison extérieure durable par simple callback | Valider le contrat après commit et la frontière audit / notification |
| GAP-06 - sécurité M0 / M1 | `STAGED_SCOPE / DECISION_REQUIRED` | 12 V2 §4 exige dès M0 ActorContext, contrôle des Commands/Queries et permissions projet ; le multi-contexte et les exports appartiennent à M1 | Décrire le minimum testable de M0, sans repousser les refus d'accès à M1 |
| GAP-10 - première tranche vs Q-M0 | `NO_CONFLICT_IN_PLAN` | 14 §1 et §25 décrit une tranche verticale initiale ; 13 §17 et 14 §24.3 imposent `AC-001..AC-012` pour le gate complet Q-M0 | Tracer l'incrément initial sans le confondre avec la qualification complète |

## Points encore non vérifiés

- `GAP-07` : comparer toutes les enums et transitions proposées, y compris leurs variantes V1.
- `GAP-08` : vérifier matrice Python, licence et contrats publics envisagés ; aucune matrice CI exécutée.
- `GAP-09` : inventorier la totalité des références d'ADR historiques et détecter les collisions.
- Tous les renvois et identifiants `AC-001..AC-012` doivent être vérifiés dans les exigences V2, puis reliés aux tests attendus.
- Les décisions d'autorisation et de concurrence sont à éprouver contre des scénarios négatifs.

## Classification et autorité

- `NO_CONFLICT_IN_V2` : convergence documentaire observée, pas une décision approuvée.
- `ALIGNED_PROPOSED` : plusieurs documents proposent une même orientation, ADR encore nécessaire.
- `OPEN_RISK` : limite de garantie ou danger de mise en œuvre.
- `DECISION_REQUIRED` : arbitrage explicite nécessaire avant de développer ou promettre la capacité.

Le verdict `Q-R0` reste `NOT_ASSESSED`.

## Sources consultées

- `05_PYPROJECTKIT_ENTITIES_AND_VALUE_OBJECTS_V2.md`, sections 8 et 9.
- `06_PYPROJECTKIT_DOMAIN_RELATIONSHIPS_AND_ERD_V2.md`, sections 3 et 18.
- `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md`, sections 9, 16 et 17.
- `08_PYPROJECTKIT_COMMANDS_QUERIES_AND_USE_CASES_V2.md`, sections 2 et 7.
- `09_PYPROJECTKIT_DOMAIN_EVENTS_CATALOG_V2.md`, sections 3 et 8.
- `10_PYPROJECTKIT_REPOSITORIES_UNIT_OF_WORK_AND_PORTS_V2.md`, section 17.
- `11_PYPROJECTKIT_ERROR_MODEL_AND_FAILURE_SEMANTICS_V2.md`, sections 16 et 17.
- `12_PYPROJECTKIT_APPLICATION_SECURITY_AND_AUTHORIZATION_V2.md`, section 4.
- `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP.md`, sections 7 et 17.
- `14_PYPROJECTKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md`, sections 1, 3, 24 et 25.

**Provenance :** documents fournis pour l'analyse dans cette conversation ; ne pas présumer leur version dans le dépôt distant. Cette note ne publie pas leur contenu intégral.
