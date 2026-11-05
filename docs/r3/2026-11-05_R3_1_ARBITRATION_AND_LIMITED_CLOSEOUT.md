# R3.1 - Registre d'arbitrages et décision de clôture à portée limitée

> Date : 2026-11-05  
> Périmètre : stabilisation de la baseline M0/M1/M2 et réconciliation des plans M3 26/27  
> Initiative : demande explicite du Product Owner de déléguer les arbitrages R3.1 à Pythos  
> Décideur technique délégué : Pythos, **pour le cadrage documentaire uniquement**  
> Statut : `DECISIONS_R3_1_DRAFT_APPLIED / R3_1_WORK_COMPLETE_WITH_RESERVATIONS / PR_REVIEW_PENDING`  
> Référence de base : `main@a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`  
> Projet : [PyProjectKit](https://github.com/tawounfouet/pyprojectkit)  
> PR : [#21](https://github.com/tawounfouet/pyprojectkit/pull/21) - **DRAFT, NON FUSIONNEE**

## 1. Autorité et séparation des décisions

Le Product Owner a confié à Pythos les arbitrages nécessaires pour terminer R3.1. Ce mandat conversationnel autorise la rédaction de décisions de **priorité, précédence documentaire, découpage et gel du périmètre**, et la préparation de correctifs traçables sur une branche de travail.

Ce mandat **ne constitue pas** :
- une revue indépendante humaine (Pythos est l'auteur des propositions et des modifications) ;
- la signature de `Q-M2`, `Q-M3A` ou de la gate de publication ;
- une autorisation tacite de merge sur `main` non protégée ;
- une acceptation des ADR de sécurité, de stockage ou de produit encore `PROPOSED` ;
- un acquittement des risques #19, #20 ou #13.

**Règle :** le statut d'exécution documentaire, la décision d'adopter l'architecture et la décision de publier sont trois décisions distinctes.

## 2. Décisions de cadrage R3.1

| ID | Arbitrage retenu pour la baseline | Portée | Réouverture si |
|---|---|---|---|
| R31-D01 | La documentation V2 conserve l'autorité sur exigences `FR/NFR/AC`. Le code et la CI au SHA attestent uniquement les comportements réellement présents. | Référence de vérité | Nouvelle version V2 approuvée |
| R31-D02 | Le document `26` reste **répertoire d'IDs de référence proposé** pour `M3-01..24`. Les titres de l'illustration `27` ne peuvent pas réaffecter ces IDs. | Backlog et traçabilité préliminaires | Texte 27 complet et décision humaine de remplacement versionné |
| R31-D03 | Le document `27` est classé `DRAFT_DETAIL_NON_NORMATIVE_ILLUSTRATED` tant que son texte complet et sa chaîne d'approbation ne sont pas récupérés. La source manquante n'empêche pas la clôture du **cadrage** R3.1, avec réserve de provenance ouverte. | Uniquement R3.1 | Texte original retrouvé |
| R31-D04 | M3-01 de 26 (audit HEAD et contrats) demeure un préflight obligatoire. R3.1 en réalise l'inventaire initial ; son statut M3-01 ne passe pas automatiquement à `DONE`. | Entrée M3 | Nouvelle baseline et gate de démarrage |
| R31-D05 | L'API n'est **pas** une fondation obligatoire de M3-A : `M3-18` reste optionnelle, à examiner en M3-C. Aucun choix obligatoire Django/FastAPI au niveau du noyau. | Architecture candidate | Besoin métier + ADR API |
| R31-D06 | PostgreSQL est une option conditionnelle. `AC-038` exige la substituabilité démontrée sur une portée déclarée, pas le support immédiat de PostgreSQL. | Persistance candidate | Besoin de concurrence/volumétrie/portabilité qualifié |
| R31-D07 | Les durées 3 semaines (26) et 8 semaines (illustration 27) ne sont pas des engagements ; aucune deadline ne découle de l'infographie. | Planning | Réestimation du backlog approuvée |
| R31-D08 | Le seuil de couverture `>=85 %` affiché dans l'image 27 n'est pas rendu obligatoire sans définition de périmètre, outil, baseline, seuil et gate. Priorité aux tests de conformité/risques, préservation des 168 tests CI historiques. | Qualité | ADR/QA gate explicite |
| R31-D09 | Les rôles métier/portefeuille de ProjectHub ne doivent pas conférer de permissions automatiquement. `TrustedHost`, scopes, owner/shares et non-divulgation restent inchangés. | Sécurité | Nouvelle matrice IAM validée |
| R31-D10 | Les services liés à SQLite et le packaging `m1/m2` sont des sujets d'évaluation R3.2/M3-A, pas des défauts justifiant une réécriture R3.1. | Architecture | Test de contrat ou besoin validé |
| R31-D11 | Les issues #19 et #20 restent bloquantes pour la gouvernance Q-M2 et la fusion selon la politique actuelle, mais **n'empêchent pas l'analyse en lecture seule ni les propositions ADR R3.2**. | Avancement sans modification de main | Revue humaine / mise en place ruleset |
| R31-D12 | Les corrections de statut documentaire sont proposées par PR, sans modifier les migrations `0001..0003`, l'API M0, les contrats M2, le schéma ou les permissions. | Non-régression | Revue du diff et CI au HEAD |

**Important :** les décisions R31-D01..12 expriment les arbitrages d'organisation pris dans le mandat de travail R3.1. Elles ne sont pas équivalentes à `ADR-M3-XX ACCEPTED`.

## 3. Résolution du conflit 26 / 27

| Axe | Source de référence R3.1 | Règle appliquée |
|---|---|---|
| `M3-01` | Audit et inventaire du 26 | Ne pas l'utiliser pour persistance dans un ticket |
| `M3-02` | Ports / Repository / UoW du 26 | Intention semblable à l'image 27 ; préserver les tests de contrat |
| `M3-03` | Substitution in-memory/SQLite et PostgreSQL candidat | Concurrence reportée à `M3-05` du 26 |
| `M3-04` | Migrations, backups, restauration | Observabilité conservée à `M3-06` du 26 |
| `M3-05` | Concurrence, idempotence, failure semantics | RBAC non ajouté silencieusement à son contenu |
| `M3-06` | Audit/logs/security fitness et CI | API reste `M3-18` optionnelle |
| M3-A durée | 26 = trois semaines hypothétiques ; 27 image = huit semaines indicatives | Aucun engagement avant estimation par WorkItem |
| Prérequis | Non-régression M0/M1/M2, AC-038 et AC-040 ciblés | Aucun `Q-M3A=GO` |

La **réconciliation de l'autorité de planification est résolue**. La **réconciliation textuelle complète de 27 est reportée sous réserve** : ne pas affirmer que son contenu exact a été vérifié.

## 4. Justification de l'exception de portée R3.1

R3.1 a pour objet de figer la photographie technique et d'éviter une dérive de planification. Il n'a pas pour objectif de :
- clôturer rétroactivement `Q-M2` ;
- installer une ruleset GitHub que la connexion ne peut pas modifier ;
- sélectionner PostgreSQL/FastAPI ;
- démarrer M3 ni un refactoring ;
- qualifier des données réelles ou l'isolation d'un processus hostile.

Les risques gouvernance #19/#20 sont **transférés inchangés** vers leurs gates propriétaires, jamais déclassés. L'absence du texte 27 est traitée par une politique conservatrice de précédence, plutôt que par invention de son contenu.

## 5. Preuves et vérifications

**Baseline figée :** `main@a523d9c61c30ef41afe3bc9cf0723beafe3c2d38` ; [CI `41919258680`](https://github.com/tawounfouet/pyprojectkit/actions/runs/41919258680), Python 3.12/3.13 : 168 PASS par version, mypy strict et wheel smoke PASS.

**PR R3.1 avant arbitrage complémentaire :** `5626f0a874f9475f3bc7b5b429115824774bc9d8` ; [CI `42004439224`](https://github.com/tawounfouet/pyprojectkit/actions/runs/42004439224), 168 PASS par version, mypy strict et wheel smoke PASS.

La PR sera requalifiée à son **HEAD final**, et non sur son SHA précédent. Le contrat M0/M1/M2 est consigné dans [R3.1 non-régression](2026-11-05_R3_1_NON_REGRESSION_CONTRACT.md).

## 6. Matrice de sortie R3.1

| Condition | État vérifié/proposé | Responsable final |
|---|---|---|
| Baseline code + CI documentée | DONE | Pythos, à SHA exact |
| Contrats M0/M1/M2 inventoriés | DONE documentaire | Pythos |
| Collision 26/27 arbitrée en termes de précédence | DECIDED_FOR_R3_1_DRAFT | Délégué projet, sous contrôle du Product Owner |
| Texte 27 complet | EXCEPTION_OPEN : provenance non vérifiée | Propriétaire documentaire |
| README / suivi roadmap alignés | PROPOSED_ON_PR | Reviewer PR |
| Régression CI au HEAD final | RECHECK_REQUIRED_AFTER_FINAL_COMMIT | GitHub CI |
| Protection main #19 | OPEN ; pas de contournement | Administrateur GitHub |
| Q-M2 indépendante #20 | PENDING ; AC-031/034 PARTIAL | Reviewer humain indépendant |
| Revue / merge PR #21 | PENDING ; maintien en draft | Product Owner/reviewer |
| Publication ou traitement de données réelles | NOT_AUTHORIZED | Product Owner et responsables sécurité |

## 7. Verdict et limites de clôture

```yaml
r3_1:
  documentary_work: COMPLETE_ON_BRANCH
  arbitration: DECIDED_WITH_PROVENANCE_EXCEPTION
  branch_validation: REQUIRE_FINAL_SHA_CI
  closure_scope: BASELINE_AND_PLANNING_ONLY
  technical_gate: CONDITIONAL_CLOSE_FOR_READ_ONLY_DESIGN
  pr_21: DRAFT_REVIEW_REQUIRED
  main_merged: false
  independent_human_review: PENDING
  source_27_full_text: NOT_AVAILABLE
  q_m2: HUMAN_GATE_PENDING
  main_protection: NOT_ACTIVE
  m3_code_authorized: false
  production_authorized: false
  release_authorized: false
```

**Décision de cadrage déléguée :** considérer le **travail d'analyse R3.1 achevé sur la branche**, autoriser la préparation documentaire R3.2 **en lecture seule**, mais maintenir la fermeture organisationnelle définitive et la fusion de la PR #21 en attente d'une revue humaine indépendante et des restrictions de gouvernance. Aucun `GO` de sécurité ou de production n'est déclaré.

## 8. Suite immédiate

1. Vérifier la CI sur le SHA final de la PR #21.
2. Faire relire le dossier R3.1 par un humain indépendant et obtenir la décision d'intégration séparée.
3. Traiter [#19](https://github.com/tawounfouet/pyprojectkit/issues/19), [#20](https://github.com/tawounfouet/pyprojectkit/issues/20) et [#13](https://github.com/tawounfouet/pyprojectkit/issues/13) dans leurs gates propres.
4. Préparer les alternatives et les tests contractuels de R3.2 sans code de production.
