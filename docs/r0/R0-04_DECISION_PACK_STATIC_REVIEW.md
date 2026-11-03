# R0-04 - Rapport de contrôle documentaire du dossier ADR M0

> Date : 2026-11-03 | Statut : STATIC_DOCUMENT_CHECK_PASS / REVIEW_REQUIRED
>
> Cible : branche `docs/r0-reconciliation-review`, PR GitHub #4 (draft).
>
> **Ne constitue pas un test Python, une revue humaine ou un verdict Q-R0.**

## Méthode réellement exécutée

Lecture distante des **sept fichiers Markdown** sur la branche de PR, vérification du titre correspondant à D-01..D-07, du statut `PROPOSED / NOT APPROVED`, des sections alternatives, tests et sources, et de l'absence de caractère em dash U+2014. Vérification également de la présence des trois livrables de synthèse, overlay et vertical slice.

## Résultats

| Dossier | Blob SHA contrôlé | Structure et statut |
|---|---|---|
| [`D-01`](../adr/proposals/D-01_PROJECT_TASK_AGGREGATE_BOUNDARIES.md) | `c4721ce7c78c14a1008c16cd6a5386f8a9347243` | PASS |
| [`D-02`](../adr/proposals/D-02_MILESTONE_OWNERSHIP_AND_DATES.md) | `be3fe872818b2373eb9821db5b30545955e7151e` | PASS |
| [`D-03`](../adr/proposals/D-03_DEPENDENCY_GRAPH_CONCURRENCY.md) | `f94e07546894dfac1b04f1985e064463f5e5dbc4` | PASS |
| [`D-04`](../adr/proposals/D-04_UNIT_OF_WORK_AND_FAILURE_SEMANTICS.md) | `609d4075c9efe5c47bbc7eeb0ac91b20800eb84d` | PASS |
| [`D-05`](../adr/proposals/D-05_APPLICATION_AUTHORIZATION_M0.md) | `fafdb4056a72adcdd370c9e7888e2e87eaa9858c` | PASS |
| [`D-06`](../adr/proposals/D-06_PUBLIC_COMMANDS_AND_DOMAIN_EVENTS.md) | `0e99389377e96e4ff06f02ed3a3f1b4de951728a` | PASS |
| [`D-07`](../adr/proposals/D-07_PYTHON_PACKAGING_AND_COMPATIBILITY.md) | `834202ac7d576f867882f5a4dd4e57a5ca73a7b5` | PASS |

**Résultat : 7/7 PASS** sur ce contrôle de structure des ADR candidats.

### Autres pièces confirmées sur la branche

- `docs/r0/R0-04_ARCHITECTURE_DECISION_REVIEW_BOARD.md` : blob `9ac24b70fab1a65798c1f527c801f6755724c4d2`, présent et lisible.
- `docs/r0/R0-08_SOFTWARE_DESIGN_OVERLAY_REVIEW.md` : blob `222016ef5825ec1656fc77050daf46bf2bb84122`, présent et lisible.
- `docs/r0/R0-09_FIRST_VERTICAL_SLICE_PROPOSAL.md` : blob `778b170edb7794dd861c14f0fc8be00b878c2d11`, présent et lisible.

## Limites essentielles

- Ce contrôle ne juge pas si les options recommandées sont économiquement ou techniquement les meilleures ; leur bien-fondé exige revue et tests.
- Le choix `D-03` devra être éprouvé sous concurrence réelle, et `D-05` sous refus d'accès et non-divulgation.
- `D-07` conserve des incertitudes explicites : versions Python, licence, version/distribution et API publique.
- Les fiches ne sont **pas approuvées** et n'ont pas été fusionnées sur `main`.
- Aucun test, lint, type check, build, CI ou import du package M0 n'a été exécuté.
- `Q-R0` demeure `NOT_ASSESSED` ; `BOOT-01` demeure `NOT_STARTED`.

## Prochaine action

Faire enregistrer dans [l'issue de revue #5](https://github.com/tawounfouet/pyprojectkit/issues/5) l'approbation, les réserves ou les refus de chaque dossier avant consolidation de la baseline.