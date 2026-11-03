# Gate Q-R0 - Autorisation d'entrer dans le bootstrap M0

> **Verdict actuel : NOT_ASSESSED**
>
> **Décision humaine : PENDING**
>
> Préparer le gate n'autorise pas l'implémentation du noyau.

| Critère | État initial | Source de preuve attendue |
|---|---|---|
| Dépôt et branche exacts inspectés | PARTIAL | Fiche R0-01, inspection local/distant |
| Baseline V2 M0 réconciliée | OPEN | Matrice GAP avec contradictions qualifiées |
| Vocabulaire M0 stabilisé | OPEN | Glossaire R0-03 |
| Agrégats et graphe décidés | OPEN | ADR R0-04 approuvés |
| Repository, UoW, erreurs, événements cohérents | OPEN | Contrats R0-05 et scénarios négatifs |
| Autorisations minimales et confidentialité définies | OPEN | Matrice sécurité R0-06 |
| `AC-001..AC-012` tracés aux tests | OPEN | Matrice R0-07 |
| Overlay revu et réserves enregistrées | OPEN | R0-08 |
| Un seul vertical slice, son scope et son mandat approuvés | OPEN | R0-09 et ticket M0 |
| Index ADR sans collision documentaire | OPEN | R0-10 |

## Politique de verdict

- `GO` : critères bloquants satisfaits, périmètre explicite, décision humaine et références exactes.
- `CONDITIONAL GO` : uniquement pour des réserves non critiques, avec owner, mesure et condition de levée.
- `NO-GO` : contradiction, sécurité, autorité ou preuve bloquante insuffisante après évaluation.
- `NOT_ASSESSED` : contrôle et décision de gate pas encore réalisés.

## Journal des décisions

| Date | Verdict | Décideur | Preuve | Réserves |
|---|---|---|---|---|
| 2026-11-03 | NOT_ASSESSED | PENDING | Mise en place de la gouvernance seulement | R0-02 à R0-10 ouverts |

Aucune ligne de ce journal n'accorde une autorisation de publication, de fusion, de release ou de création du package M0.

## Dossier de revue disponible sur branche (non fusionné)

Le dossier [`R0_REVIEW_README.md`](R0_REVIEW_README.md) référence la matrice d'écarts, le glossaire, les sept décisions proposées, la matrice sécurité, les tests AC et le crosswalk ADR. Il est présenté dans une [PR documentaire en brouillon](https://github.com/tawounfouet/pyprojectkit/pull/4).

**État de ces contrôles : PREPARED_FOR_REVIEW, pas PASS.** Les dossiers V2 historiques et l'approbation humaine restent des prérequis pour décider `Q-R0`.

## Bloquant supplémentaire constaté par revue V1/V2

Le [dossier d'audit direct V1/V2](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) identifie six collisions de codes de règles entre les versions, parfois même entre le corps de 07 V2 et son annexe historique. Un [patch correctif proposé](R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md) attend approbation.

**D-SEM-01 : NOT_RESOLVED / BLOCKING.** Ne pas déclarer `Q-R0 = GO` tant que cette collision n'est pas arbitrée et propagée vers la baseline et la traçabilité des tests.
