# D-SEM-01 - Compatibilité sémantique des identifiants de règles V1/V2

> **Statut : ACCEPTED (décision de compatibilité documentaire) / BASELINE PR STILL REVIEW**
>
> Date : 2026-11-03
>
> Décideur habilité : propriétaire du projet PyProjectKit (approbation explicite reçue le 2026-11-03)
>
> Type : décision de compatibilité documentaire, préalable à la baseline M0
>
> Dossier : [audit V1/V2](../r0/2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md), [proposition initiale](../r0/R0-02_V2_RULE_ID_REMEDIATION_PROPOSAL.md), [candidat 07 V2](../specifications/review/07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md), [contrôle statique](../r0/R0-02_D_SEM_01_STATIC_VALIDATION.md).

## 1. Problème observé

La spécification 07 V2 du 2 novembre 2026 réutilise six identifiants V1 pour des obligations différentes dans son corps, tout en reprenant les significations historiques en annexe A. Les tests et la traçabilité pourraient associer la même clé à deux comportements distincts.

| Clé affectée | Contrat V1 à préserver | Nouvelle obligation V2 à identifier séparément |
|---|---|---|
| `BR-DELIV-001` | Critères obligatoires satisfaits avant acceptation | Relation à Project/Milestone |
| `BR-DELIV-002` | Approval éventuellement nécessaire | Critères d'acceptation (déjà couverts par 001) |
| `BR-ASSIGN-001` | Membre admissible uniquement | Référence/portée valide |
| `BR-ASSIGN-002` | Admissibilité par Policy possible | Au plus un assigné actif M0 |
| `BR-ASSIGN-003` | Conserver `unassigned_at` à la fin | Interdire contournement des statuts terminaux |
| `INV-DATE-002` | Période vide seulement si contrat l'autorise | Compatibilité des types de bornes |

## 2. Alternatives considérées

**Option A - Préserver les IDs et sens de V1 (préférée).** Créer de nouveaux IDs V2 uniquement pour les exigences réellement nouvelles. Avantages : stabilité des références, cohérence avec l'annexe historique, migrations et tests explicables. Inconvénient : noms V2 supplémentaires et table de correspondance à maintenir.

**Option B - Conserver les significations du corps V2.** Déplacer les anciennes règles sous de nouveaux IDs. Avantage : pas de modification du corps V2 actuel. Inconvénient : rupture de compatibilité sémantique des identifiants, requérant réécriture des références historiques. Déconseillée sans justification d'une migration incompatible.

**Option C - Aliaser les deux significations sous le même identifiant.** Avantage apparent : pas de migration visible. Inconvénient : rend les critères non déterministes et non vérifiables. Option rejetée comme proposition technique, mais pas comme décision humaine formelle.

## 3. Proposition explicite à valider

1. Préserver les significations V1 pour les six codes historiques.
2. Introduire `INV-DELIV-V2-001`, `BR-ASSIGN-V2-001`, `BR-ASSIGN-V2-002` et `INV-DATE-V2-001` pour les nouvelles obligations.
3. Conserver `BR-ASSIGN-003` strictement comme règle de conservation de `unassigned_at` lorsqu'une affectation se termine. L'arbitrage « historique d'affectation dans la première tranche M0 ou ultérieurement » est une **question de périmètre séparée**.
4. Ne pas créer un deuxième code pour la règle déjà couverte par `BR-DELIV-001`.
5. Harmoniser ensuite les références des documents 08 à 12 et des tests M0.
6. N'attribuer le statut `ACCEPTED` à la décision qu'avec une approbation humaine datée et référencée.

## 4. État des modifications proposées

- Une copie entière de **07 V2 corrigée** a été placée sur la branche `docs/r0-reconciliation-review`, sous `docs/specifications/review/`.
- Le corps actif comporte une définition unique par identifiant vérifié.
- Les anciennes formulations sont préservées dans l'annexe historique.
- Les **10 assertions documentaires ciblées** de la vérification sur blob sont `PASS`.
- La baseline documentaire canonique de `main` n'a pas été remplacée. Aucun code runtime n'est concerné.

## 5. Points de vigilance restant à décider

- L'historique d'affectation `unassigned_at` fait-il partie du *premier vertical slice* ou de la qualification M0 complète ?
- La limitation à un assigné actif doit-elle être un invariant universel, une policy M0 ou un choix provisoire de l'adapter ?
- Les nouveaux IDs proposés sont-ils conformes à la nomenclature documentaire cible et sans collisions dans tous les artefacts historiques ?
- Y a-t-il des références secondaires non répertoriées dans les documents 08 à 12 à migrer ?

## 6. Décision humaine

| Champ | Valeur |
|---|---|
| Verdict | **ACCEPTED - option A** |
| Option retenue | **Option A : préservation des six significations V1 et identifiants V2 distincts** |
| Date de validation | **2026-11-03, vers 10:06 CET (Europe/Paris)** |
| Référence de l'approbation | [Enregistrement GitHub du consentement exprimé dans la conversation](https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491) |
| Réserves | **La décision ne tranche pas les sept ADR M0, ni le périmètre exact de la fonctionnalité d'historisation ; correction de la baseline en PR non fusionnée.** |
| Impacts sur le gate Q-R0 | **Blocage de décision D-SEM-01 levé ; reste la consolidation de la baseline et les autres critères de Q-R0. Gate = NOT_ASSESSED.** |

> **Portée de l'approbation** : le propriétaire a validé l'option A dans la conversation de pilotage ; le commentaire GitHub référencé ci-dessus en consigne la décision. Ceci n'est pas une revue GitHub signée par le propriétaire, ni une approbation de la PR entière ou des autres ADR. La copie corrigée de 07 V2 demeure sur branche de revue. `Q-R0` n'est pas évalué.

## 7. Traçabilité de l'entrée en vigueur de la décision

- **Autorité** : propriétaire humain du projet, approbation explicite par message dans cette conversation, 2026-11-03 vers 10:06 CET.
- **Trace GitHub** : https://github.com/tawounfouet/pyprojectkit/issues/2#issuecomment-6599599491.
- **Portée** : identité et sémantique des six codes V1 ; séparation des quatre IDs V2.
- **Preuve de préparation technique** : contrôle documentaire ciblé 10/10 sur le blob `e7dd0c629f6e1745446e035a3e03969650079fcc` ; ce n'est pas une qualification du runtime.
- **Statut du correctif** : accepté en principe, présent dans la PR #4 en brouillon, non encore intégré à une baseline canonique approuvée.
- **Décisions indépendantes** : D-01..D-07 en `PROPOSED`, `Q-R0 = NOT_ASSESSED`, `BOOT-01` non commencé.
