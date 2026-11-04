# Q-M2 - Préflight vérifié et recommandations de revue

> Date de vérification : 2026-11-04  
> Statut : `READY_FOR_INDEPENDENT_REVIEW / INTEGRATION_BLOCKED`  
> Périmètre : `SYNTHETIC_LOCAL_ONLY`  
> Dossier principal : `23_PYPROJECTKIT_M2_FINAL_QUALIFICATION_AND_CLOSURE.md` (document de cadrage de la revue)  
> **Aucun procès-verbal Q-M2 signé dans ce document.**

## 1. Vérifications indépendantes des déclarations

| Élément | Résultat observé |
|---|---|
| `main` | `26487b61f54a49fa1d5eec6bd2d36eda01524ac8` |
| Protection `main` | **`protected=false`**, `required_status_checks.contexts=[]`, état effectif de l'objet `branches/main` |
| Rulesets GitHub | `[]` via l'API autorisée |
| Endpoint de protection historique | `403 Resource not accessible by integration`; ne pas en déduire des paramètres inexistants |
| CODEOWNERS | Aucun fichier `.github/CODEOWNERS` trouvé à la racine testée |
| PR M2-A | #16, tête `d99ca06067849f968ef98024a1515b433bf0f26e`, CI #118 SUCCESS |
| PR M2-B | #17, tête `6d074d7dff4d2e15831c41db0b6c07809162e6e8`, CI #162 SUCCESS |
| PR M2-C | #18, tête de référence `2a6afab3d12dbbe891900b956696aa872e0c44fa`, CI #203 SUCCESS |
| CI Q-M2 | 168 tests PASS pour chaque Python 3.12/3.13, mypy strict et wheel smoke PASS |
| Reviews soumises | **Aucune** sur les PR #16, #17 et #18 au premier examen |
| Human gate | `PENDING` ; aucun verdict indépendant retrouvé |

Les branches sont empilées. La CI sur feature branch ne remplace pas la CI sur le HEAD de `main` après les fusions autorisées.

## 2. Registre de revue des ADR (recommandations techniques NON signées)

| ADR | Avis technique à proposer au reviewer | Condition / limite |
|---|---|---|
| M2-01 | `ACCEPT_FOR_SYNTHETIC_PILOT` proposé | DTO v1 strict, aucun token de capacité, pas de signature de transport |
| M2-02 | `ACCEPT_FOR_SYNTHETIC_PILOT` proposé | TrustedHost seule autorité, mandat en mémoire provisionné par l'hôte ; pas de Python hostile in-process |
| M2-03 | `ACCEPT_FOR_SYNTHETIC_PILOT` proposé | SQLite 0003, inbox append-only et transaction locale ; pas de `exactly-once` distribué |
| M2-04 | `ACCEPT_WITH_LIMITS` proposé | Fake verifier ne confère jamais M1 `assessment PASS`; revue indépendante réelle toujours à fournir |
| M2-05 | `ACCEPT_FOR_SYNTHETIC_PILOT` proposé | `WorkItemRef` réfère à Task, sans Aggregate Root universel |
| M2-06 | `ACCEPT_WITH_LIMITS` proposé | Pilotes Git/TEACHING fictifs, pas de Pythos réel, ni de vrai dépôt PySRMKit |
| M2-07 | `ACCEPT_WITH_LIMITS` proposé | Reprise autorisée avec métadonnées et stale/missing, sans reconstruire un mandat volatile |
| M2-08 | `ACCEPT_WITH_LIMITS` proposé | Evidence manifest non probant à lui seul, ne signe aucun Q-M2 |

Ces lignes ne changent pas les ADR : statut GitHub réel **PROPOSED** tant qu'une autorité compétente ne les approuve pas avec commentaire et référence de décision. Un agent ne s'attribue pas une signature d'architecte.

## 3. Traitement proposé d'AC-031

**Option de moindre risque pour le seul pilote local** : exclure entièrement l'exécution des opérations privilégiées (`merge`, `publish`, `delete`, priorité réservée). Les tests peuvent vérifier l'absence de surface, la restriction des mandats et l'absence de mutation. Cela **ne démontre pas un DENY d'un outil réel**, qui n'existe pas dans ce périmètre.

En conséquence, **maintenir `AC-031=PARTIAL`**, et consigner une exception de périmètre uniquement si un reviewer habilité accepte le risque dans une décision `CONDITIONAL_GO_LOCAL_SYNTHETIC_PILOT`. Si une vraie interface d'outil est ajoutée, de nouveaux tests doivent la couvrir.

## 4. Traitement requis d'AC-034

Aucune synthèse, réponse du modèle ou autorisation générale de l'utilisateur ne remplace le reviewer humain indépendant prévu par le plan 23.

Pour considérer le gate : 
1. Obtenir un reviewer identifié distinct de l'auteur et du producteur du rapport.
2. Lire le diff, les huit ADR, la matrice Q-M2 et le registre des risques.
3. Documenter les observations, décisions et exclusions.
4. Signer/enregistrer `GO_LOCAL_SYNTHETIC_PILOT`, `CONDITIONAL_GO_LOCAL_SYNTHETIC_PILOT` ou `NO_GO`.
5. Émettre une **autorisation de merge distincte**, avec portée et SHA vérifiés.

## 5. Gouvernance GitHub à rendre effective

**Blocker supplémentaire identifié** : `main` n'est pas protégée.

- [ ] Créer une protection/ruleset sur `main`.
- [ ] Exiger les checks CI Python 3.12/3.13 sur les PR, sans bypass administrateur.
- [ ] Exiger une review indépendante et le traitement des conversations bloquantes.
- [ ] Interdire force-push et suppression.
- [ ] Relire les règles effectives après mise en place.

Le connecteur GitHub présent ne permet pas de créer/modifier une branch protection, et le GET de l'ancien endpoint renvoie 403. La configuration doit être réalisée par un administrateur GitHub habilité ; **ne pas annoncer son succès par simple création d'une issue**.

Voir [issue #19](https://github.com/tawounfouet/pyprojectkit/issues/19).

## 6. Revue indépendante et clôture

- [ ] Reviewer nommé et review(s) sur #16, #17, #18.
- [ ] Résolution formelle AC-031 et AC-034.
- [ ] ADR-M2-01..08 acceptés/amendés/rejetés individuellement.
- [ ] Registre des 14 risques renseigné.
- [ ] Q-M2 signé avec exclusions/expiration.
- [ ] Autorisation de merge distincte.
- [ ] Intégration ordonnée #16 -> #17 -> #18, avec vérification des diff et migration 0003.
- [ ] Requalification complète sur le HEAD effectif de `main`.
- [ ] Rapport post-merge daté, SHA et résultats CI.
- [ ] Décision distincte de release, aucun tag ou publication implicite.

Voir [issue #20](https://github.com/tawounfouet/pyprojectkit/issues/20).

**État après préflight : `CODE_CANDIDATE_REVIEWABLE`, `Q_M2_HUMAN_PENDING`, `MAIN_PROTECTION_PENDING`, `NO_MERGE`, `NO_RELEASE`.**
