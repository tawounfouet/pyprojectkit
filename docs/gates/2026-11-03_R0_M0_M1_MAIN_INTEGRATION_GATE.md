# PyProjectKit - Gate de qualification pour intégration alpha sur main

> Date : 2026-11-03
>
> **Décision : CONDITIONAL GO FOR MAIN INTEGRATION (LOCAL SYNTHETIC ALPHA ONLY)**
>
> Mandat humain de qualifier et intégrer sur main : https://github.com/tawounfouet/pyprojectkit/issues/1#issuecomment-6610885985
>
> Validateur technique : Pythos, sous mandat explicite. **Pas de review GitHub indépendante.**
>
> Références : PR #4 (R0), #6 (M0), #9 (M1 design), #10 (M1 code), issue #1 et [registre des arbitrages M0](../adr/2026-11-03_M0_ALPHA_PILOT_DECISION_REGISTER.md).
>
> **Ce dossier fixe une décision d'intégration au dépôt, non un GO de publication, d'usage client ou de production.** Sa validité doit être recontrôlée sur le dernier commit fusionné de main.

## 1. Couverture et preuves avant fusion

| Gate | Portée vérifiée | Verdict d'intégration |
|---|---|---|
| `Q-R0` | V1/V2 comparées, D-SEM-01 acceptée ; D-01..D-07 adoptés techniquement pour alpha ; baseline minimale/écarts documentés | **CONDITIONAL GO - alpha**, réserves de baseline V2 intégrale et revue indépendante |
| `Q-M0` | SHA `ab2d4246c758f70b35507ec7fe016f9344da723c` ; CI run `41653259680`, Python 3.12/3.13, 17 tests PASS, wheel et mypy strict PASS | **CONDITIONAL GO - noyau InMemory** |
| `Q-M1` | SHA M1 + correctif de lecture inter-owner, CI en cours de consolidation ; migrations SQLite, reprise, 5 familles, observations, preuves, snapshots/handoffs, refus des fuites | **CONDITIONAL GO - pilote local synthétique**, sous réserve de réussite CI HEAD avant merge |

Le rapport M1 antérieur à la correction de sécurité `docs/qualification/M1_REPORT.md` demeure un historique de 40 tests, **pas une preuve du correctif ajouté**. Les preuves du nouveau HEAD seront réinscrites en addendum dans ce dossier lorsque la CI sera vérifiée.

## 2. Findings de la revue

**SEC-PILOT-01 / corrigé sur PR #10** : un lecteur ayant `PROJECT_VIEW` sur un scope pouvait voir le Project d'un autre owner sans partage explicite. Correction : visibilité du Project conditionnée à l'owner ou à un droit d'accès partagé vérifié par l'hôte. Test de non-divulgation ajouté aux listes, comptes, Query, Resume et export.

**PACK-PILOT-01 / couverture renforcée** : les tests antérieurs construisaient une wheel après une installation éditable. Le pipeline M1 a été renforcé pour installer et importer la wheel créée dans un venv isolé et en mode `--no-index`, sur Python 3.12/3.13.

**GOV-PILOT-01 / réserve explicite** : pas de reviewer GitHub indépendant ; les choix D-01..D-07 sont des décisions techniques sous mandat d'intégration, pas une approbation individuelle historique.

**LIC-PILOT-01 / publication bloquée** : pas de licence. En l'absence d'un choix explicite du propriétaire, aucune release, PyPI ou réutilisation sous licence n'est revendiquée.

**SEC-PILOT-02 / périmètre strict** : données synthétiques uniquement ; pas d'IAM de production, chiffrement SQLite, isolation de code Python hostile ou Outbox durable.

## 3. Conditions suspensives du merge

- [x] Mandat explicite du propriétaire pour aller jusqu'à la fusion, tracé dans issue #1.
- [x] Qualif M0 sur SHA exact : 17 tests, mypy, wheel, CI Python 3.12/3.13.
- [x] Qualif M1 de référence : 40 tests, restart, SQLite, preuves et absence cross-scope sur SHA antérieur.
- [x] Correction d'un défaut d'accès entre owners de même scope et tests négatifs locaux.
- [ ] Dernière CI M1 sur HEAD intégrant correctif et installation wheel isolée, 3.12 et 3.13, explicitement vérifiée dans le dossier.
- [ ] Inventaire PR et absence d'erreur bloquante au moment du merge.
- [ ] Contrôle des SHA exacts, réconciliation des branches de base et validation des retargets.
- [ ] Contrôle de la CI sur le HEAD final de `main` après fusion.

Les lignes à cocher restant ouvertes ne peuvent être déclarées satisfaites que sur preuves réellement obtenues. Si les checks GitHub échouent, **NO-GO au merge** jusqu'à correction.

## 4. Ordre de fusion autorisé, sous contrôle

1. PR #4 : revue R0 et arbitrages documentaires vers main.
2. PR #6 : noyau M0 vers main, en conservant l'ascendance utile à PR #10.
3. PR #9 : plan et décisions M1 vers main.
4. PR #10 : retarget `feat/m0-bootstrap` vers `main` après intégration M0, vérifier diff et CI, puis intégrer le code M1.

Toute fusion utilise un SHA attendu et l'API standard GitHub, sans réécriture forcée de branche, ni contournement volontaire de règle de protection. Si la règle exige une review tierce, l'intégration attend cette review ; le mandat utilisateur ne la remplace pas.

## 5. Réserves et actions avec responsables

| Réserve | Responsable | Levée avant |
|---|---|---|
| Licence et conditions de diffusion | Propriétaire humain | Publication PyPI, tag de release et réutilisation sous licence |
| Revue GitHub indépendante et politique de `main` | Propriétaire / maintainer | Toute release destinée à des tiers |
| Identity management, ressources et chiffrement | Maintainer sécurité | Données réelles, clients, production et service hostile |
| Persistence distribuée, Outbox, backup/restauration élargis | Maintainer architecture | Garantie réseau/distribuée |
| Validation formelle des ADR M0/M1 au-delà du pilote | Propriétaire humain | Extension du périmètre d'usage |
| CI post-merge sur `main` | Intégrateur | Annonce de clôture complète |

## 6. Autorité et limites de décision

Le propriétaire a donné instruction d'exécuter la qualification jusqu'au merge, ce qui constitue un mandat d'intégration de l'alpha **si** les préconditions sont remplies. Le choix définitif d'une licence ou l'approbation d'une sécurité de production ne peuvent pas être déduits de cet ordre.

**Ne pas annoncer de réussite de merge tant que l'API GitHub et la lecture post-merge de main ne l'ont pas confirmé.**
