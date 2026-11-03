# Pilotage de la roadmap PyProjectKit

> Statut : R0 ACTIVE / DOCUMENTATION REVIEW / M0 NOT_STARTED
>
> Référence : `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP.md` et `14_PYPROJECTKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md`.

## Paliers de livraison

| Phase | Finalité | Condition d'entrée | Gate de sortie |
|---|---|---|---|
| R0 | Audit, réconciliation, décisions, backlog | Dépôt cible identifié | `Q-R0` |
| M0 | Domain Kernel, tests et première API | `Q-R0 = GO` ou décision `CONDITIONAL GO` valide | `Q-M0`, `AC-001..AC-012` |
| M1 | Project Registry, preuves et continuité | `Q-M0` | `Q-M1` |
| M2 | Adapter optionnel Pythos | `Q-M1` | `Q-M2` |
| C3 | Extensions avancées à la demande | Besoin métier et gate ciblé | `Q-C3` |

Le découpage en semaines illustré dans les visuels S1-S16+ ne constitue pas une date d'échéance contractuelle. Les jalons GitHub natifs seront créés si et quand cette fonctionnalité est accessible et leur gouvernance décidée.

## R0 - Un seul chantier actif : BOOT-00

| ID | Résultat attendu | Dépendances | État initial |
|---|---|---|---|
| R0-01 | Audit distant/local du dépôt, références exactes | - | PARTIAL - distant observé |
| R0-02 | Matrice de contradictions M0 | R0-01 | OPEN - registre préliminaire |
| R0-03 | Glossaire Task / WorkItem, statuts, IDs, temps | R0-02 | PLANNED |
| R0-04 | ADR frontières agrégats et graphe | R0-02 | PLANNED |
| R0-05 | Contrats Repository/UoW/Events/Errors alignés | R0-03, R0-04 | PLANNED |
| R0-06 | Matrice de sécurité M0/M1 | R0-02 | PLANNED |
| R0-07 | Chaîne AC -> use case -> invariant -> test -> preuve | R0-03, R0-05 | PLANNED |
| R0-08 | Revue et validation overlay | R0-02 à R0-07 | PLANNED |
| R0-09 | Premier vertical slice et mandat explicites | R0-07, R0-08 | PLANNED |
| R0-10 | Index ADR et déduplication | R0-02 | PARTIAL - index initial |

## Politique de suivi

- Suivi de l'ensemble des activités R0 via une issue parente `BOOT-00` et des issues ciblées uniquement selon le WIP.
- Ne pas ouvrir les tickets `BOOT-01..11` comme chantiers actifs avant `Q-R0`.
- Les WorkItems ont un owner, une dépendance, un livrable, une preuve et une prochaine action.
- Aucun statut `IMPLEMENTED`, `VERIFIED` ou `QUALIFIED` sans résultat à la référence exacte.
- Aucun ADR `ACCEPTED` sans approbation humaine ; aucune fusion ou publication implicite.

## Revue documentaire en cours (2026-11-03)

Une [PR documentaire #4 en brouillon](https://github.com/tawounfouet/pyprojectkit/pull/4) contient le dossier R0 de réconciliation, glossaire, décisions candidates, sécurité et traçabilité AC. La PR n'est ni une approbation d'ADR, ni une qualification de M0, ni un lancement de BOOT-01.

## Prochaine action

Poursuivre `R0-02` : comparer systématiquement les textes V2, qualifier les divergences, identifier les arbitrages nécessaires et préparer une revue des décisions bloquantes. Vérifier en parallèle les protections de `main` et les éventuelles sources locales non publiées.

## Mise à jour de l'audit V1/V2

Les 12 documents originaux V1 sont retrouvés et comparés avec leurs V2. Un [rapport de compatibilité](r0/2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) recense six collisions de sens de règles et la préservation de garanties AC héritées. Le [correctif](r0/R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md) correspond à l'option A, **approuvée le 2026-11-03** ([trace](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491)). La PR #4 reste en brouillon et `Q-R0 = NOT_ASSESSED`.

## Décision documentaire D-SEM-01 : état actualisé

La [spécification 07 V2 candidate corrigée](specifications/review/07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md) et la [fiche de décision](adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md) sont désormais incluses dans la PR #4. La validation documentaire ciblée est [documentée](r0/R0-02_D_SEM_01_STATIC_VALIDATION.md), mais la consolidation de baseline, les arbitrages M0 restants et l'autorisation de BOOT-01 restent en attente.


## Décision D-SEM-01 actée

**ACCEPTED (option A, 2026-11-03).** Validation humaine enregistrée [ici](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491) et dans la [fiche de décision](adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md). Le périmètre approuvé est limité à la conservation du sens des six IDs V1 et à leur séparation des nouveaux codes V2. Les décisions D-01..D-07 et le gate `Q-R0` demeurent ouverts.

## Avancement ADR M0 et première tranche de bootstrap

Les sept arbitrages D-01..D-07 sont documentés avec alternatives et tests attendus dans [la matrice de revue](r0/R0-04_ARCHITECTURE_DECISION_REVIEW_BOARD.md), suivie via [l'issue #5](https://github.com/tawounfouet/pyprojectkit/issues/5). La [revue de l'overlay](r0/R0-08_SOFTWARE_DESIGN_OVERLAY_REVIEW.md) et la [proposition de vertical slice](r0/R0-09_FIRST_VERTICAL_SLICE_PROPOSAL.md) ont été ajoutées.

- `D-SEM-01` = ACCEPTED, uniquement compatibilité documentaire.
- `D-01..D-07` = PROPOSED, approbation humaine en attente.
- `R0-08` = REVIEW_DONE_FOR_M0, adoption en attente.
- `R0-09` = SLICE_PROPOSED, pas de mandat `BOOT-01`.
- `Q-R0` = NOT_ASSESSED.

## Qualification technique alpha et passage proposé sur main

La [décision de gate pour intégration locale](gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md) établit un `CONDITIONAL GO` pour le merge du pilote synthétique, avec [arbitrages M0 adoptés pour alpha seulement](adr/2026-11-03_M0_ALPHA_PILOT_DECISION_REGISTER.md). Une CI Python 3.12/3.13 sur PR #10 au SHA `6e52b9bed819dde7465933c3dfd782559d2c9f60` confirme 41 tests par version, mypy strict et installation wheel isolée. Les contrôles post-merge devront être enregistrés séparément. Aucun `GO` de publication, de production, de données sensibles ou de licence n'en découle.
