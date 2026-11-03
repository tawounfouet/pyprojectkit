# R0-10 - Registre des décisions d'architecture

> Statut : INDEX PROPOSE / REVIEW
>
> **Aucun ADR n'est réputé `ACCEPTED` à la date de création de cet index.**

Les identifiants `ADR-PJ-RM-xx` proviennent de la roadmap 13. Ils sont des **références de suivi provisoires**. Avant de créer des fichiers ADR canoniques, vérifier leur chevauchement avec les décisions V1 et V2 pour éviter des numéros concurrents.

| Référence | Question | Périmètre de décision | Statut |
|---|---|---|---|
| ADR-PJ-RM-01 | `Project` et `Task` comme Aggregate Roots séparés ? | R0 / M0 | PROPOSED |
| ADR-PJ-RM-02 | `Milestone` interne à `Project` ? | R0 / M0 | PROPOSED |
| ADR-PJ-RM-03 | Graphe des dépendances, cohérence concurrente ? | R0 / M0 | PROPOSED |
| ADR-PJ-RM-04 | Package et API Python minimale, version Python supportée ? | R0 / M0 | PROPOSED |
| ADR-PJ-RM-05 | Contrat `Repository` / `UnitOfWork` ? | R0 / M0 | PROPOSED |
| ADR-PJ-RM-06 | Événements internes et garanties après commit ? | M0 | PROPOSED |
| ADR-PJ-RM-07 | Persistance durable pilote ? | M1 | DEFERRED |
| ADR-PJ-RM-08 | Séparer provenance, observation et évaluation ? | M1 | DEFERRED |
| ADR-PJ-RM-09 | Snapshot historique et continuité ? | M1 | DEFERRED |
| ADR-PJ-RM-10 | Portée et contrôles de confidentialité ? | R0 minimal, M1 complet | PROPOSED |
| ADR-PJ-RM-11 | DTO et mandat Pythos optionnels ? | M2 | DEFERRED |
| ADR-PJ-RM-12 | Critères de qualification et preuves sur SHA ? | R0 / chaque gate | PROPOSED |

## Cycle de décision

`PROPOSED -> UNDER_REVIEW -> ACCEPTED / REJECTED / SUPERSEDED`

Une décision acceptée doit contenir : problème réel, contexte, alternatives évaluées, conséquences, owner, date de validation, liens vers sources et tests de conformité. Un consensus apparent dans plusieurs documents `REVIEW` ne suffit pas à approuver un ADR.

## Format candidat d'un ADR

```markdown
# ADR-PJ-XXX - Sujet
Statut : PROPOSED
Date : YYYY-MM-DD
Décideur habilité : PENDING

## Contexte / pression métier
## Décision proposée
## Alternatives et compromis
## Invariants / sécurité / modes d'échec
## Conséquences et réversibilité
## Tests et preuves attendus
## Documents et WorkItems impactés
## Décision et référence d'approbation
```

Documents sources : `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP.md` section 6 ; spécifications V2 04 à 12 ; convention commune Py*Kit.

## Réconciliation du 3 novembre 2026 (en revue)

Le [crosswalk des décisions V2](../r0/R0-10_ADR_CROSSWALK.md) rapproche les identifiants historiques par sujet. Le [dossier de décisions M0](../r0/R0-04_M0_DECISION_DOSSIER.md) présente sept arbitrages proposés et leurs alternatives.

**Aucun de ces documents ne vaut `ACCEPTED` ; gate `Q-R0` toujours `NOT_ASSESSED`.**
