# R0-02 - Contrôle documentaire des identifiants D-SEM-01

> Date : 2026-11-03
>
> Statut : **STATIC_DOCUMENT_CHECK_PASS / REVIEW REQUIRED**
>
> Document vérifié : `docs/specifications/review/07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md`
>
> Blob Git : `e7dd0c629f6e1745446e035a3e03969650079fcc` ; commit de modification candidate : `6156928eea23048b5efd4ac65b006e92205c22c9`.

## Méthode exécutée

Lecture du contenu réel du fichier sur la branche de revue et contrôle exact, en distinguant la partie active du document de l'**annexe A historique**. Les assertions comparent le sens de chaque définition du corps avec les formulations historiques des sources V1, puis vérifient l'unicité des nouveaux identifiants dans le corps.

| ID | Corps : définition unique | Sens historique préservé ou nouveau code distinct |
|---|---|---|
| `BR-DELIV-001` | Oui | OK |
| `BR-DELIV-002` | Oui | OK |
| `BR-ASSIGN-001` | Oui | OK |
| `BR-ASSIGN-002` | Oui | OK |
| `BR-ASSIGN-003` | Oui | OK |
| `INV-DATE-002` | Oui | OK |
| `INV-DELIV-V2-001` | Oui | OK |
| `BR-ASSIGN-V2-001` | Oui | OK |
| `BR-ASSIGN-V2-002` | Oui | OK |
| `INV-DATE-V2-001` | Oui | OK |

**Résultat des 10 assertions ciblées : PASS.**

### Contrôles additionnels

- Présence de l'annexe A historique dans le candidat : **Oui**.
- Statut candidat explicitement `REVIEW` / non approuvé : **Oui**.
- Caractère em dash U+2014 dans la version déposée : **Absent**.

## Périmètre et limites

- Ce contrôle examine **uniquement** le document cible et les 10 définitions sélectionnées ; il ne constitue pas un audit sémantique exhaustif de tous les identifiants V1/V2.
- Il ne valide pas les conséquences fonctionnelles de `BR-ASSIGN-V2-001` ni la portée de l'historique d'affectation : ces questions restent ouvertes.
- Il n'exécute aucun code produit, aucun test Python, aucune CI et ne confirme aucune compatibilité runtime ou API.
- Un fichier candidat cohérent n'est pas automatiquement une baseline approuvée. Les références transversales restent à consolider dans les documents 08 à 12.
- Le propriétaire humain doit examiner la proposition et la décider avant toute promotion canonique.

**Verdict historique au premier contrôle : `D-SEM-01 = PROPOSED / STATIC_CHECK_PASS`. Depuis, D-SEM-01 a été `ACCEPTED` le 2026-11-03 et la copie de revue a été recontrôlée sur un nouveau blob, comme détaillé ci-dessus.** Le gate `Q-R0` demeure `NOT_ASSESSED`.

## Recontrôle après approbation humaine (2026-11-03)

Le propriétaire a accepté l'option A de D-SEM-01, consignée dans [l'issue #2](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491). Une nouvelle lecture du **fichier réellement publié sur la branche de revue** a été effectuée après l'ajout de cette mention.

- **Blob actuel contrôlé** : `d841baca4b6b6585fbaefbb727a4028a01630458`.
- **Assertions ciblées** : 10/10 définitions uniques et sémantiquement conformes à la décision A dans le corps actif, dont quatre IDs nouveaux.
- **Statut** : `DOCUMENT_CHECK_PASS` pour cette cible ; `D-SEM-01 = ACCEPTED`.
- **Limite** : ce test documentaire ne remplace ni une revue humaine des autres ADR ni un test Python/CI ; la baseline canonique de `main` n'a pas été fusionnée.

## Contrôle de références interdocuments (sources V2 fournies)

Une recherche exacte des six identifiants historiques `BR-ASSIGN-001..003`, `BR-DELIV-001/002` et `INV-DATE-002` a été réalisée dans **11 autres fichiers V2 PyProjectKit** de la source fournie (trois documents `00`, `04`, `05`, `06`, `08`, `09`, `10`, `11`, `12`). **Résultat : aucune occurrence textuelle exacte hors du document `07` V2.**

Cela limite les remplacements d'identifiants *directs* requis dans les autres spécifications. Ce contrôle **ne démontre pas leur alignement sémantique complet** : l'admissibilité des assignés, le modèle de dates, les garanties de persistance et les critères des tests doivent encore être revus dans leurs contrats.

La comparaison de similitude des définitions communes V1/V2 a aussi signalé des **candidats non tranchés** : `BR-CAP-002` (modes `FAIL/WARN/ALLOW` historiques), `INV-DUR-001` (portée d'une durée négative) et `BR-VERSION-001` (conflit en cas de version obsolète, conditionné au contrat de concurrence). Ils sont à revoir selon leur priorité M0/C3 avant de prétendre à une compatibilité complète. Aucun nouveau conflit bloquant n'est affirmé sans examen de leurs justifications.
