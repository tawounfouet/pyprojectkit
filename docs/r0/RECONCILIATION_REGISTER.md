# R0-02 - Registre initial de réconciliation V2

> **Mise à jour :** les résultats de la première vérification croisée sont dans [l'audit initial du 3 novembre](2026-11-03_INITIAL_V2_CONSISTENCY_AUDIT.md). Le tableau ci-dessous conserve les *questions d'origine*, et non leur dernière classification. En particulier, `GAP-01` et `GAP-10` apparaissent désormais sans conflit documentaire identifié dans le périmètre revu.


> Statut : OPEN / PRELIMINARY - 2026-11-03
>
> Objectif : établir un inventaire des sujets à vérifier **avant** de considérer les spécifications comme une baseline approuvée.

Les lignes ci-dessous sont des **points de réconciliation**, pas une affirmation qu'une incompatibilité matérielle a déjà été démontrée. Chaque décision doit être corroborée par les documents canoniques concernés, puis acceptée par l'autorité du projet.

| ID | Sujet à réconcilier | Sources candidates | Impact M0 | Statut / prochaine action |
|---|---|---|---|---|
| GAP-01 | `Task` (entité métier) vs `WorkItem` (travail de pilotage / modèle Pythos) | 04, 05, 08 V2, roadmap 13, bootstrap 14 | Bloquant si un même nom impose deux cycles incompatibles | OPEN : fixer un glossaire et un mapping sans fusion prématurée |
| GAP-02 | `Project` / `Task` Aggregate Roots, `Milestone` interne à Project, `Dependency` comme lien | 05, 06, 07 V2 | Bloquant pour les frontières transactionnelles | OPEN : proposer ADR-PJ-RM-01/02/03 |
| GAP-03 | Graphe acyclique sous écritures concurrentes | 06, 07, 10, 11 V2, roadmap 13 | Bloquant avant garantie de concurrence | OPEN : préciser vérification et limitation InMemory |
| GAP-04 | Contrat de `Repository` / `UnitOfWork`, rollback et issue inconnue d'un commit | 08, 09, 10, 11 V2 | Bloquant pour l'atomicité du premier scénario | OPEN : définir un contrat testable sans fausse promesse distribuée |
| GAP-05 | Domain Events, audit et `ExecutionReport` ne représentent pas la même vérité | 08, 09, 11, 12 V2 | À clarifier avant événements de succès | OPEN : confirmer le moment d'enregistrement après commit |
| GAP-06 | Autorisations M0 minimales vs `ContextScope` et isolation avancée M1 | 07, 08, 10, 12 V2 | Bloquant pour toute commande/lecture exposée | OPEN : définir matrice M0 et politique fail-closed |
| GAP-07 | Identifiants et cycles de statuts projet, tâche, preuve, qualification, gates Pythos | 04, 05, 07, 08, 11, 12 V2 | Risque de fausse promotion d'état | OPEN : définir les axes distincts et transitions minimales |
| GAP-08 | Version Python de référence, matrice testée, API initiale et choix de licence | Vision 00 V2, roadmap 13, bootstrap 14 | Décision à prendre avant le packaging | OPEN : Python 3.12+ est une cible historique, non qualifiée |
| GAP-09 | Nomenclature des ADR issus des V1/V2 et `ADR-PJ-RM-xx` | 04 à 12 V2, roadmap 13 | Risque de décisions dupliquées | OPEN : réconcilier avant acceptation |
| GAP-10 | Distinction tranche verticale initiale `BOOT-01..11` et gate complet `Q-M0` `AC-001..AC-012` | Requirements 00 V2, roadmap 13, bootstrap 14 | Risque de confondre premier test et qualification M0 | OPEN : tracer AC -> use case -> invariant -> test -> SHA |

## Méthode d'arbitrage

1. Ouvrir les documents V2 sources et relever les extraits pertinents par sujet.
2. Classer les écarts `BLOCKING`, `NON_BLOCKING`, `DEFERRED` ou `NO_CONFLICT`, avec justification.
3. Rédiger un ADR **uniquement** lorsqu'une décision architecturale est requise.
4. Conserver `CURRENT`, `TARGET`, `GAP`, `DECISION`, `EVIDENCE` et la personne qui approuve.
5. Réviser le glossaire, les contrats, les critères d'acceptation et l'overlay en conséquence.
6. Laisser `Q-R0` à `NOT_ASSESSED` jusqu'à la revue effective.

## Ce qui n'est pas fait

- Aucun audit ligne par ligne exhaustif du corpus V2 n'est revendiqué.
- Aucune des orientations candidates ci-dessus n'est acceptée par défaut.
- Aucun code, test, pipeline, version Python ni intégration Pythos n'est qualifié.

Références : `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP.md` sections 6 et 7 ; `14_PYPROJECTKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md` sections 2 à 4.
