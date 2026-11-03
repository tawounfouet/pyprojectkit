# R0-10 - Crosswalk d'ADR historiques vers décisions de livraison M0

> Statut : PROPOSED / REVIEW, aucun ADR `ACCEPTED`.
>
> Cet index crée un **regroupement par question** et conserve les identifiants historiques ; il ne réattribue pas leurs numéros ni n'efface la V1.

## Index M0 condensé

| Sujet d'arbitrage | Suivi roadmap | Références déjà présentes dans la V2 | Décision candidate / alternative | Test de sortie |
|---|---|---|---|---|
| AR Project/Task | `ADR-PJ-RM-01` | `ADR-06-001`, `ADR-07-002` | Deux AR séparés plutôt qu'un God Project | Préservation de l'identité Task et mutation inter-AR explicite |
| Milestone | `ADR-PJ-RM-02` | `ADR-06-002`, `ADR-07-001`, `ADR-APP-03`, `ADR-PJ-10-05` | Entity Project M0 plutôt qu'AR indépendant | Mise à jour via ProjectRepository et règles temporelles |
| Graphe de dépendances | `ADR-PJ-RM-03` | `ADR-06-003`, `ADR-06-016`, `ADR-07-003`, `ADR-APP-04`, `ADR-PJ-10-06` | Port par graphe/version commune plutôt que simples écritures de liens | Cycles séquentiels et race testés selon garanties |
| API et versions | `ADR-PJ-RM-04` | `ADR-PJ-10-15` ; roadmap 13 §6 ; bootstrap 14 §8 | API sync headless, Python `>=3.12` candidat ; nom/version/licence à fixer | Import Python isolé, build et typing |
| Repositories / UoW | `ADR-PJ-RM-05` | `ADR-PJ-10-01..04`, `ADR-APP-05` | `ProjectRepository`, `TaskRepository`, UoW explicite ; alternatives transaction native / adapter | Commit/rollback sans fuite, versions, erreurs |
| Events | `ADR-PJ-RM-06` | `ADR-PJ-10-07`, `ADR-EVT-V2-01..10`, `ADR-APP-14` | Fait interne après commit, pas de livraison externe garantie | Zéro événement de succès sur échec |
| Autorisations M0 | `ADR-PJ-RM-10` (couvre aussi M1) | `SEC-ADR-V2-001..04`, `SEC-ADR-V2-013`, `ADR-PJ-10-13`, `ADR-07-006/015` | Scope projet + ActorContext fiable + guards fail-closed | Refus reads/writes hors scope et non-divulgation |
| Erreurs / commit inconnu | transversal `RM-05/06` | `ADR-ERR-V2-001..016`, 11 §§16-19 | Conflit métier, persistence, issue inconnue distincts | Aucune fausse réussite après timeout de commit |
| Gate / preuve | `ADR-PJ-RM-12` | Roadmap 13 §§15,17 ; 14 §24 | Qualifier sur SHA exact, décision humaine | Matrice AC, résultat d'exécution, références |

**Attention** : les plages `ADR-EVT-V2-01..10` et `ADR-ERR-V2-001..016` sont des familles à rapprocher **ligne par ligne** avant toute aliasisation définitive ; ce tableau n'affirme pas que chacun est un doublon.

## Décisions hors M0

- `ADR-PJ-RM-07..09` : durable registry, preuve et snapshots M1.
- `ADR-PJ-RM-11` : adapter Pythos M2.
- Exports, Portfolio, IAM avancé, Event Sourcing et Outbox durable restent conditionnels, non des prérequis M0.

## Processus d'approbation

Pour chaque sujet M0, produire **une seule** fiche décisionnelle :

1. problème métier et frontière concernée ;
2. options et alternatives éliminées, avec compromis ;
3. garanties et limites explicites (concurrence, échec, autorité) ;
4. références de spécifications à actualiser si décision prise ;
5. tests d'acceptation et preuves futures ;
6. `DECISION_OWNER`, date et lien de décision humaine.

Le verdict d'une revue documentaire **ne vaut pas** adoption. Une décision approuvée peut conserver plusieurs alias historiques vers le même sujet, sans multiplier les ADR canoniques.

**État présent : tous les sujets en PROPOSED ou OPEN.**

## Point de décision documentaire D-SEM-01 - collisions V1/V2

La confrontation des **12 V1 originales** et des V2 a révélé des collisions d'identifiants dans 07 V2 (`BR-ASSIGN-001..003`, `BR-DELIV-001..002`, `INV-DATE-002`). Voir [audit des sources](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) et [patch conceptuel](R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md).

**D-SEM-01 = DECISION_REQUIRED**, préalable à la baseline M0. Il ne s'agit pas d'un ADR d'architecture supplémentaire : l'arbitrage concerne la compatibilité des codes de règles. Proposition : préserver la signification historique de chaque ID et introduire des IDs V2 non conflictuels. Cette proposition n'est pas approuvée.
