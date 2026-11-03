# PyProjectKit - Audit de clôture après intégration R0/M0/M1 sur main

> Date : 2026-11-03
>
> Statut : **MAIN_MERGED / SYNTHETIC_LOCAL_ALPHA_CONDITIONAL_GO / RELEASE_NOT_APPROVED**
>
> Référence de `main` au lancement de cet audit : `95522030356b0320e9e057885ee2a06f359bf3c8`.
>
> Mandat de qualification et de merge du propriétaire : https://github.com/tawounfouet/pyprojectkit/issues/1#issuecomment-6610885985.
>
> Cette qualification concerne **exclusivement** le pilote Python local, synthétique, sans IAM de production ni donnée réelle sensible. Elle ne constitue pas un accord de publication PyPI.

## 1. Traçabilité GitHub des quatre PR

| Ordre | PR | Objet | Résultat confirmé par GitHub | SHA de fusion |
|---|---|---|---|---|
| 1 | [#4](https://github.com/tawounfouet/pyprojectkit/pull/4) | Réconciliation R0, décisions documentaires, gate alpha | `merged=true` | `8e9a2143b92c4d4d1b5954f41d8d4c55105acc09` |
| 2 | [#6](https://github.com/tawounfouet/pyprojectkit/pull/6) | Noyau M0, tests/ports/InMemory | `merged=true` | `8b6489baf88d754b8e35e9198670df0a4a3f1465` |
| 3 | [#9](https://github.com/tawounfouet/pyprojectkit/pull/9) | Plan M1, SQLite et sécurité, ADR M1-01/02/03 | `merged=true` | `d99e57f0e49b06bfa15f79ea2f938b4fe3851d3f` |
| 4 | [#10](https://github.com/tawounfouet/pyprojectkit/pull/10) | SQLite Registry, preuves, continuité, correctif de sécurité | `merged=true` | `95522030356b0320e9e057885ee2a06f359bf3c8` |

La PR #10 a été retargetée de `feat/m0-bootstrap` vers `main` après fusion de M0. Le diff final comprenait **14 fichiers propres à M1**. Toutes les opérations de fusion ont utilisé l'API GitHub, méthode `merge` et garde sur SHA HEAD attendu, sans force-push. Le comparateur GitHub a confirmé `main` **identical** au commit `955220...` après les quatre fusions.

## 2. Qualification technique pré-merge sur le SHA exact du code

**Dernier HEAD de PR #10 avant merge** : `4711bab3778bc2406da96796c65a25914c79c2a0`.

GitHub Actions **#41685790390**, jobs Python **3.12** et **3.13** : `SUCCESS`.

| Contrôle | 3.12 | 3.13 |
|---|---|---|
| Pytest M0 et M1 | **41 passed** | **41 passed** |
| `mypy --strict` | **13 fichiers sans erreur** | **13 fichiers sans erreur** |
| Wheel `pyprojectkit-0.2.0a1-py3-none-any.whl` | **Build PASS** | **Build PASS** |
| Installation wheel dans une venv séparée avec `--no-index` | **PASS** | **PASS** |
| Import `SqliteDatabase` et `RegistryService` dans cette venv | **PASS** | **PASS** |
| Invocation de la CLI depuis cette venv | **PASS** | **PASS** |

L'ancienne preuve M0 est GitHub Actions **#41653259680** sur le SHA M0 `ab2d4246c758f70b35507ec7fe016f9344da723c` : **17 tests**, wheel et mypy strict sur Python 3.12/3.13.

## 3. Audit de sécurité, classification et correctif

**Finding SEC-PILOT-01 (corrigé)** : avant correction, un principal avec `PROJECT_VIEW` pouvait lire le Project d'un autre propriétaire dans le même scope, sans partage explicite. Reproduction adversariale obtenue dans la copie de travail. Correction intégrée à PR #10 :

- vérification propriétaire ou permissions `PROJECT_VIEW_ALL` / `PROJECT_VIEW:<uuid>` provisionnées par `TrustedHost` ;
- filtrage avant listes, totaux, facettes, pagination, exports et reprise ;
- tests négatifs de refus générique sans révélation d'existence ;
- suite locale et CI passée de **40** à **41 tests**.

**Scope de sécurité effectivement qualifié** : code hôte local de confiance, ressources et identités synthétiques, SQLite fichier local. Le credential public de la CLI `--demo` est **exclusivement démonstratif**. Pas de protection contre un code Python hostile contrôlant le processus, ni d'IAM externe, chiffrement SQLite, clé gérée ou politique de données sensibles.

Contrôle documentaire de PR #4 : la source métier 07 V2 examinée ne contenait pas d'e-mail ni de secret évident correspondant aux signatures de clés courantes. Ce contrôle textuel n'est pas une certification anti-fuite exhaustive.

## 4. Vérifications de main après fusion

Le connecteur GitHub confirme la présence sur `main` des fichiers :

- `src/pyprojectkit/m1/security.py`, `service.py` et `tests/test_m1.py`, y compris le correctif et sa régression ;
- `.github/workflows/ci.yml` avec installation de wheel dans une venv isolée et hors ligne ;
- `docs/gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md` ;
- `docs/adr/2026-11-03_M0_ALPHA_PILOT_DECISION_REGISTER.md` ;
- `docs/implementation/15_PYPROJECTKIT_M1_IMPLEMENTATION_PLAN.md`.

**Réserve d'observabilité** : l'action GitHub disponible pour chercher les workflows par commit ne retourne que les jobs liés à des pull requests. Elle ne permet pas, à elle seule, de confirmer une exécution de workflow déclenchée par `push` sur le SHA de merge de `main`. Un workflow de vérification sur une branche **créée directement depuis `main`** fournit une contre-vérification de la même base de code, et sera tracé dans l'addendum ci-dessous lorsqu'il sera terminé.

## 5. Verdict de gate et décisions restant ouvertes

Les gates de [qualification conditionnelle alpha](../gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md) ont été appréciés avec une portée strictement délimitée :

- `Q-R0` : **CONDITIONAL GO pour baseline d'intégration alpha** ; corpus V1/V2 et décisions techniques suffisamment reconciliés pour le prototype, sans ratification de tous les ADR pour la production.
- `Q-M0` : **CONDITIONAL GO pour noyau InMemory alpha**, avec non-régression démontrée.
- `Q-M1` : **CONDITIONAL GO pour pilote local synthétique**, avec reprise SQLite, claims/observations/evidence, snapshots/handoffs et contrôle d'accès corrigé.
- **Release, PyPI, service réseau, données réelles sensibles : NO AUTHORIZATION.** La licence est non décidée.

L'acceptation technique des options D-01..D-07 relève d'un mandat d'intégration, **pas d'une revue GitHub indépendante inventée**. Les ADR M1 additionnels, et les choix de licence, chiffrement, rétention, sauvegarde multi-environnements et politique de protection de branche restent des actions ouvertes.

## 6. Follow-up bloquants avant usage au-delà du pilote

| Point | Responsable | Déclencheur de levée |
|---|---|---|
| Licence et stratégie de distribution | Propriétaire humain | Avant toute publication PyPI, release ou attribution de droits de réutilisation |
| Politique d'identités et de secrets de production | Responsable sécurité | Avant connexion réseau / utilisation avec tiers |
| Isolation des données sensibles, chiffrement/backup/rétention | Responsable sécurité / données | Avant données personnelles, clients ou employeurs réelles |
| Outbox durable, transactions/résilience distribuées | Maintainer architecture | Avant promesse de livraison durable interprocessus |
| Revue indépendante et branch protections `main` | Propriétaire / maintainer | Avant release officielle destinée à des tiers |
| Qualifier les ADR non clos au-delà du pilote | Propriétaire humain | Avant extension des garanties du produit |

## 7. Addendum de vérification sur base main

**VERIFIED** : la branche documentaire a été créée directement à partir de `main` au commit `95522030356b0320e9e057885ee2a06f359bf3c8`. Le comparateur GitHub entre `main` et la branche QA confirme **un seul fichier ajouté : ce rapport**, aucun changement applicatif ni CI. Le run GitHub Actions **#41686411069** a terminé avec succès sur Python 3.12 (job `126093227923`) et 3.13 (job `126093228343`). Les logs de chaque job montrent **41 tests PASS**, `mypy --strict` sans erreur sur **13 fichiers**, wheel `0.2.0a1` construite, installation dans une venv séparée via `--no-index` et import `isolated import: OK`. Cette exécution valide la base de code intégrée sur main avec le seul ajout documentaire de cette PR ; **elle n'est pas un run déclenché directement sur le SHA de merge 955220**.

**Verdict à ce stade : les quatre merges sur main sont confirmés ; le prototype alpha local synthétique dispose d'une qualification conditionnelle et de preuves CI avant merge. Aucune release n'est autorisée.**


## 8. Conclusion opérationnelle avant merge du rapport

- **Code / branches** : PR #4/#6/#9/#10 effectivement fusionnées ; `main` sur `95522030356b0320e9e057885ee2a06f359bf3c8` au moment de la qualification.
- **Contenu** : comparateur GitHub `main...docs/post-merge-qa-20261103` : exactement un nouveau document, zéro changement de code.
- **Validation post-merge sur base `main`** : CI #41686411069, Python 3.12 et 3.13 `SUCCESS`, 41 tests et mypy strict, wheel venv offline PASS.
- **Autorité** : intégration alpha expressément mandatée par le propriétaire ; aucun reviewer externe inventé.
- **Verdict** : `INTEGRATION_ALPHA_LOCAL_SYNTHETIC_QUALIFIED_CONDITIONALLY`. Les garanties de release, de sécurité de production, de licence et de données sensibles restent **NOT_APPROVED**.
