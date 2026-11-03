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

## Historique du blocage sémantique D-SEM-01 (résolu sur le plan de la décision)

Le [dossier d'audit direct V1/V2](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md) identifie six collisions de codes de règles entre les versions, parfois même entre le corps de 07 V2 et son annexe historique. Le [patch option A](R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md) a été approuvé le 2026-11-03, tout en restant sur la branche de revue tant que la PR #4 n'est pas fusionnée.

**D-SEM-01 : décision ACCEPTED le 2026-11-03.** La correction a été arbitrée par le propriétaire (option A), mais son intégration à la baseline et la traçabilité globale restent à vérifier avant `Q-R0`.

## Avancement D-SEM-01 : correction candidate effectivement déposée

La [copie de revue de 07 V2](../specifications/review/07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md) contient les six corrections de sens et quatre nouveaux IDs proposés. Le [contrôle statique ciblé](R0-02_D_SEM_01_STATIC_VALIDATION.md) a validé 10 assertions sur un blob identifié. La [fiche D-SEM-01](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md) présente les alternatives et sollicite une décision humaine.

**Statut actualisé : D-SEM-01 ACCEPTED / PATCH_IN_DRAFT_PR / DOCUMENT_CHECK_PASS.** La décision humaine est consignée ; l'adoption de la baseline et les autres prérequis bloquent toujours l'évaluation `Q-R0`.

## Approbation D-SEM-01 reçue le 3 novembre 2026

L'[enregistrement de l'approbation humaine](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491) permet de lever **le seul blocage de choix sémantique D-SEM-01**. La [fiche de décision](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md) est désormais `ACCEPTED` pour son périmètre documentaire.

**Non acquis** : revue et éventuelle fusion de la PR #4, baseline V2 alignée et adoptée, les sept choix de conception M0, contrôles d'autorisation, paquet Python, CI et décision formelle `Q-R0`. **Verdict global maintenu : NOT_ASSESSED.**

## Revue des sept ADR structurants et entrée BOOT-01

Les fiches [D-01..D-07](R0-04_ARCHITECTURE_DECISION_REVIEW_BOARD.md) sont prêtes pour la [revue humaine #5](https://github.com/tawounfouet/pyprojectkit/issues/5), mais demeurent toutes `PROPOSED`. La [première tranche M0](R0-09_FIRST_VERTICAL_SLICE_PROPOSAL.md) est également une **proposition**, pas un mandat d'implémentation. L'[overlay](R0-08_SOFTWARE_DESIGN_OVERLAY_REVIEW.md) est revu pour son périmètre M0, mais non adopté formellement.

Pour passer `Q-R0` : décider D-01..D-07, aligner/valider la baseline, établir la politique d'autorisation et la cible de repo, documenter les preuves exactes, puis enregistrer un verdict humain. **État global : NOT_ASSESSED.**

## Addendum de qualification du 3 novembre 2026, après demande explicite d'intégration

La [décision d'intégration alpha conditionnelle](../gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md) et le [registre technique D-01..D-07](../adr/2026-11-03_M0_ALPHA_PILOT_DECISION_REGISTER.md) complètent l'historique de cette note. L'état `NOT_ASSESSED` inscrit dans les paragraphes précédents décrit **la situation avant la revue de qualification et le mandat de merge**. Le résultat le plus récent est `CONDITIONAL GO FOR MAIN INTEGRATION`, strictement borné au pilote local et synthétique, sans qualification de release ou production. Les conditions pré-merge et post-merge sont vérifiables dans le dossier de gate ; ne pas assimiler ces statuts à une autorisation de publication.
