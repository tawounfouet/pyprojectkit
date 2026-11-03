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

## Prochaine action

Poursuivre `R0-02` : comparer systématiquement les textes V2, qualifier les divergences, identifier les arbitrages nécessaires et préparer une revue des décisions bloquantes. Vérifier en parallèle les protections de `main` et les éventuelles sources locales non publiées.
