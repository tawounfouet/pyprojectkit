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
