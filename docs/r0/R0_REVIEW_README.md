# R0 - Dossier de revue et ordre de lecture

> Tous les documents de ce dossier sont **PROPOSED / REVIEW** ; aucune décision M0 n'est approuvée.

## Documents proposés dans la branche de revue

1. [Matrice de réconciliation V2](2026-11-03_V2_RECONCILIATION_MATRIX.md) - statut et risques par GAP.
2. [Glossaire du domaine M0](R0-03_DOMAIN_GLOSSARY.md) - termes, noms, identités et temporalité.
3. [Dossier d'arbitrages M0](R0-04_M0_DECISION_DOSSIER.md) - options, compromis, tests et décisions en attente.
4. [Matrice de sécurité](R0-06_M0_SECURITY_MATRIX.md) - contrôles de refus minimaux.
5. [Trace AC-001..AC-012](R0-07_M0_ACCEPTANCE_TRACEABILITY.md) - critères vers scénarios et futures preuves.
6. [Crosswalk des ADR](R0-10_ADR_CROSSWALK.md) - déduplication par sujet, identifiants historiques conservés.

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
