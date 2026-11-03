# R0 - Dossier de revue et ordre de lecture

> Tous les documents de ce dossier sont **PROPOSED / REVIEW** ; aucune décision M0 n'est approuvée.

## Documents proposés dans la branche de revue

1. [Audit direct des 12 sources V1](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) - compatibilité et collisions sémantiques.
2. [Proposition de remédiation des codes](R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md) - patch conceptuel non approuvé.
3. [Matrice de réconciliation V2](2026-11-03_V2_RECONCILIATION_MATRIX.md) - statut et risques par GAP.
4. [Glossaire du domaine M0](R0-03_DOMAIN_GLOSSARY.md) - termes, noms, identités et temporalité.
5. [Dossier d'arbitrages M0](R0-04_M0_DECISION_DOSSIER.md) - options, compromis, tests et décisions en attente.
6. [Matrice de sécurité](R0-06_M0_SECURITY_MATRIX.md) - contrôles de refus minimaux.
7. [Trace AC-001..AC-012](R0-07_M0_ACCEPTANCE_TRACEABILITY.md) - critères vers scénarios et futures preuves.
8. [Crosswalk des ADR](R0-10_ADR_CROSSWALK.md) - déduplication par sujet, identifiants historiques conservés.

## R0 - Répartition des responsabilités

- `R0-02` : matrice et classification (audit de première passe, clôture non prononcée).
- `R0-03` : glossaire candidat, à approuver après R0-02.
- `R0-04` : décisions d'Aggregate et modèle à arbitrer.
- `R0-05` : contrats UnitOfWork, erreurs et événements à figer.
- `R0-06` : permissions, scopes et fail-closed.
- `R0-07` : plan de qualification, aucun test exécuté.
- `R0-08/09` : approbation de l'overlay et ticket de premier vertical slice, ensuite seulement.
- `R0-10` : index ADR, état PROPOSED.

## Conditions qui empêchent le GO aujourd'hui

- Historique V1 à comparer avant d'approuver les éventuels changements incompatibles.
- Aucun ADR M0 accepté avec référence humaine.
- R0-01 : environnement local, protections de branche et politique de licence non encore confirmés.
- Politique d'autorisation et de cohérence concurrente non validées.
- Sources V2 non inscrites dans une baseline GitHub approuvée.
- Aucun mandat BOOT-01 approuvé.

La revue de ces documents peut progresser en parallèle, mais ne crée pas une autorisation implicite de BOOT-01.


## Contrôle bloquant ajouté

L'audit direct des V1 confirme que six identifiants du document 07 V2 ont un sens différent du contrat V1. Ces collisions empêchent de figer la baseline des règles et les scénarios de qualification par ID. Le dossier de patch n'a pas encore été appliqué aux V2 canoniques.

## Pièces ajoutées pour la décision D-SEM-01

- [Spécification 07 V2 corrigée, copie de revue](../specifications/review/07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md)
- [Compte rendu de vérification statique sur le blob](R0-02_D_SEM_01_STATIC_VALIDATION.md)
- [Fiche de décision formelle D-SEM-01](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md)

La [décision D-SEM-01](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md) a été **ACCEPTED le 2026-11-03** pour l'option A ([trace](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491)). La copie de 07 V2 demeure sur la branche de revue, sans fusion ni qualification technique ; le gate `Q-R0` reste `NOT_ASSESSED`.

## Dossiers d'architecture préparés (2026-11-03)

- [Tableau des sept décisions M0](R0-04_ARCHITECTURE_DECISION_REVIEW_BOARD.md) et [issue de revue humaine #5](https://github.com/tawounfouet/pyprojectkit/issues/5).
- [D-01 - Agrégats](../adr/proposals/D-01_PROJECT_TASK_AGGREGATE_BOUNDARIES.md), [D-02 - Jalons](../adr/proposals/D-02_MILESTONE_OWNERSHIP_AND_DATES.md), [D-03 - Graphe](../adr/proposals/D-03_DEPENDENCY_GRAPH_CONCURRENCY.md), [D-04 - UoW](../adr/proposals/D-04_UNIT_OF_WORK_AND_FAILURE_SEMANTICS.md).
- [D-05 - Sécurité](../adr/proposals/D-05_APPLICATION_AUTHORIZATION_M0.md), [D-06 - API et événements](../adr/proposals/D-06_PUBLIC_COMMANDS_AND_DOMAIN_EVENTS.md), [D-07 - Packaging](../adr/proposals/D-07_PYTHON_PACKAGING_AND_COMPATIBILITY.md).
- [Revue de l'overlay d'apprentissage](R0-08_SOFTWARE_DESIGN_OVERLAY_REVIEW.md) et [première tranche verticale candidate](R0-09_FIRST_VERTICAL_SLICE_PROPOSAL.md).

Les sept décisions demeurent `PROPOSED`. La revue de l'overlay et le vertical slice sont préparés, pas approuvés ni implémentés.

## Qualification en vue du merge alpha sur main

Voir [dossier de gate](../gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md) et [registre des arbitrages M0 adoptés sous mandat technique](../adr/2026-11-03_M0_ALPHA_PILOT_DECISION_REGISTER.md). Le statut `PROPOSED` des fiches D-01..07 est leur statut historique initial ; l'option choisie pour le **seul pilote local synthétique** est consignée dans le registre d'intégration, sans prétendre à une review GitHub indépendante. La licence, la production et les données réelles restent exclues.
