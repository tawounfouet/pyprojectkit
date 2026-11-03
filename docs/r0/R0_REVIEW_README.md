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

La copie de 07 V2 reste en `REVIEW`, n'est pas une baseline normative approuvée et n'est pas sur `main` tant que la PR n'est pas fusionnée. Le blocage sémantique est **techniquement préparé pour décision**, pas clos.
