# PyProjectKit - M1 - Rapport de livraison et de qualification technique

> Date : 2026-11-03
>
> **Statut : IMPLEMENTED_FOR_SYNTHETIC_LOCAL_PILOT / FORMAL_Q_M1_NOT_ASSESSED**
>
> Projet : `tawounfouet/pyprojectkit`, PR #10 sur `feat/m1-registry-continuity`, base `feat/m0-bootstrap` (PR #6)
>
> SHA de code soumis aux tests GitHub : `74506cd2e26540cf8b080b6ad546b026ce0eb8ee`
>
> Source normative de planification : `15_PYPROJECTKIT_M1_IMPLEMENTATION_PLAN.md` (PR #9)
>
> ADR de cadrage M1 acceptés pour le pilote : `ADR-M1-01/02/03`. Les ADR-M1-04..12, les ADR M0 D-01..07 et les gates restent soumis à revue.
>
> **Cette livraison ne constitue ni une qualification de sécurité de production, ni l'autorisation d'utiliser des données privées réelles, ni une publication PyPI.**

## 1. Contenu effectivement implémenté

L'adaptateur SQLite (`sqlite3` standard library) s'ajoute au noyau M0 sans remplacer l'adaptateur InMemory. Un nouveau processus peut retrouver les objets M0 et les historiques M1 persistés dans un fichier SQLite. La couche Application reste distincte des accès SQL et de l'hôte de confiance.

| Tranche | Capacité opérationnelle du prototype | Code / scénario |
|---|---|---|
| M1-A | `SqliteUnitOfWork`, M0 Project/Task/Milestone/Graph, migrations 0001/0002 contrôlées, version, rollback, backup, scopes et registre | `m1/schema.py`, `m1/sqlite.py`, `m1/security.py`, `m1/service.py` |
| M1-B | ExternalReference scoped, Claim, Observation, EvidenceRef et Assessment par cible/version, deux sources contradictoires conservées, ReconciliationCase, Decision, Approval | `m1/service.py`, historique append-only et triggers SQLite |
| M1-C | Snapshot immuable, Handoff, NextAction existante ou absente avec raison, ResumeContext et lecture de portefeuille scoped | `m1/models.py`, `m1/service.py` |
| M1-D | Cinq familles de projets, policies différentes selon scope, tests adversariaux, redémarrage interprocessus et exemple de bout en bout | `tests/test_m1.py`, `examples/m1_registry_demo.py`, CLI de démo |

### Inventaire M1-01..M1-20

| WorkItems | Implémentation candidate | Qualification |
|---|---|---|
| M1-01 / M1-02 | SQLite, migrations, UoW, repositories M0, CAS graph, backup | Tests de persistance / contrat pilote |
| M1-03 / M1-04 / M1-05 | Project Registry, VerifiedActor/ContextScope, CLI synthétique | Tests de scope, liste, démo CLI |
| M1-06 / M1-07 | Références externes, Claim et Observation historisées | Tests 0/1/N et contradiction |
| M1-08 / M1-09 / M1-10 | Assessments, ReconciliationCase, Decision et Approval | Tests PASS ciblé SHA, source indisponible et autorité |
| M1-11 / M1-12 / M1-13 | Snapshot, NextAction, Handoff | Tests d'immutabilité et `NONE_WITH_REASON` |
| M1-14 / M1-15 | ResumeContext, PortfolioReader scoped avec facettes/pages | Tests reprise et refus cross-scope |
| M1-16 / M1-17 | Cinq familles synthétiques sans dépendance Git/sprint | Tests des catégories et projet personnel fictif |
| M1-18 / M1-19 | Redémarrage réel, rollback/crash, graphe multi-processus, contrôles de confidentialité | Tests en subprocess et négatifs |
| M1-20 | Matrice AC, rapport d'implémentation et dossier de gate | Présent document ; revue humaine en attente |

`IMPLEMENTED` dans ce tableau veut dire code de pilote présent, **pas** validation définitive de chaque WorkItem, de ses ADR et de l'ensemble des garanties métier.

## 2. Preuves de test

**Exécution locale** (Python 3.13, environnement du chantier) :

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python examples/m1_registry_demo.py
python -m compileall -q src examples
python -m pip wheel --no-build-isolation --no-deps -w dist .
```

- **40 tests PASS localement**, dont les **17 tests du noyau M0**, sans modification de leurs cas.
- Scénario M1 : cinq projets synthétiques, une tâche ouverte, preuve enregistrée, assessment ciblé, observation, décision approuvée, snapshot, handoff, puis nouvelle connexion SQLite et reprise.
- Construction de wheel alpha locale `pyprojectkit-0.2.0a1-py3-none-any.whl` : réussie avant les seuls ajouts de tests/rapport.
- GitHub Actions Matrix Python 3.12/3.13 : voir section 3.

### Scénarios négatifs majeurs réellement testés

- Transaction abandonnée sans `commit()` et exception précommit : aucune écriture visible après réouverture.
- **Crash de sous-processus** avant commit : aucune mutation persistée.
- **Deux processus** sur le même graphe : une seule dépendance contradictoire confirmée, aucune création de cycle.
- Migration checksum altérée : refus sans réparation silencieuse.
- Sauvegarde SQLite via `backup()` puis restauration du Project et de ses versions.
- Clés étrangères invalides et modification/suppression d'historique interdites par triggers.
- Identité/scopes falsifiés : refus, sans permission obtenue par un champ arbitraire.
- Projet d'un autre scope absent des listes, facettes, comptes, pages, Queries et ResumeContext.
- Snapshot classé PRIVATE, Observation privée et métadonnées de scope PRIVATE non retournés à un acteur sans permission.
- Evidence inexistante / inaccessible : pas de PASS déduit ; `PASS(sha-A)` ne valide pas `sha-B`.
- Deux observations contradictoires conservées après résolution, sans remplacement du contenu historique.
- `Task.DONE` ne crée pas d'Approval, `Portfolio.PARK` est distinct de `Project.ON_HOLD`.
- Snapshot ancien ne remplace pas l'état courant ; handoff ne clôture aucune Task.
- Absence de tâche ouverte : `NextAction(None, None, NONE_WITH_REASON...)`.
- **Nouveau processus Python** : Tasks ouvertes, versions, décision, snapshot, handoff et NextAction sont retrouvés sans état de conversation.

## 3. CI sur SHA exact

**Run GitHub Actions #41665577635, `SUCCESS`, sur SHA `74506cd2e26540cf8b080b6ad546b026ce0eb8ee` :**

| Exigence | Python 3.12 | Python 3.13 |
|---|---|---|
| Pytest M0 + M1 | **40 PASS** | **40 PASS** |
| `mypy --strict` | **PASS : 13 fichiers** | **PASS : 13 fichiers** |
| Wheel | **PASS : `0.2.0a1`** | **PASS : `0.2.0a1`** |
| Exemple et CLI | **PASS (job CI)** | **PASS (job CI)** |

**Traçabilité vérifiée** : jobs GitHub Actions `126019852624` (Python 3.12) et `126019852230` (Python 3.13). Les logs affichent `40 passed`, `Success: no issues found in 13 source files` et une wheel construite dans chaque job. Une modification ultérieure de documentation ne modifie pas le SHA de code qualifié ici.

## 4. Matrice AC-013..AC-026

Les catégories ci-dessous sont **qualifications de prototype synthétique**. La validation métier et la politique de sécurité finale restent à décider.

| AC | Scénario et test | État prudent |
|---|---|---|
| AC-013 | Cinq familles `PACKAGE/PRODUCT/CLIENT/TEACHING/PERSONAL` sans Git obligatoire | `VERIFIED_PILOT` |
| AC-014 | Registry owner, status, priority, due date, NextAction | `VERIFIED_PILOT` |
| AC-015 | Reprise interprocessus du Project, Tasks, décisions, snapshot, handoff | `VERIFIED_PILOT` |
| AC-016 | Claim, Observation, Assessment et ProjectStatus jamais confondus | `VERIFIED_PILOT` |
| AC-017 | Policy logicielle stricte refuse publication sans assessment `PASS` | `VERIFIED_FOR_LOCAL_POLICY`, pas de service de publication externe |
| AC-018 | Assessment SHA A non applicable à SHA B | `VERIFIED_PILOT` |
| AC-019 | Source indisponible ne crée pas de PASS | `VERIFIED_FOR_DECLARED_AVAILABILITY`, absence de fetch externe |
| AC-020 | Observations contradictoires préservées, conflit historisé et résolution séparée | `VERIFIED_PILOT` |
| AC-021 | Task DONE ne crée aucune Approval ni certification | `VERIFIED_PILOT` |
| AC-022 | Aucune prochaine action = `NONE_WITH_REASON` | `VERIFIED_PILOT` |
| AC-023 | Portfolio PARK indépendant du Project ON_HOLD | `VERIFIED_PILOT` |
| AC-024 | Scopes, compte/facettes, page, export, snapshot PRIVATE | `VERIFIED_FOR_TRUSTED_LOCAL_HOST`, pas de sécurité multi-tenant hostile |
| AC-025 | Projet personnel financier fictif sans relevé ni secret importé | `VERIFIED_SYNTHETIC_FIXTURE_ONLY` |
| AC-026 | Policies de validation différentes par scope sans mutation du core M0 | `VERIFIED_PILOT` |

## 5. Risques et limites bloquantes avant Q-M1

1. **Security** : le moteur fonctionne avec code hôte de confiance et fichier SQLite local protégé par l'OS. Il n'isole pas un programme Python hostile ayant accès au processus, au système de fichiers ou au credential. Le credential fixe de la CLI est **public et réservé à `--demo`**.
2. **Données** : SQLite local non chiffré ; aucune donnée client, employeur, financière ou personnelle réelle dans le pilote sans politique chiffrement/retention/sécurité validée.
3. **Concurrence** : `BEGIN IMMEDIATE` sérialise les writers SQLite dans un fichier local ; ni réplication, ni haute disponibilité, ni sûreté multi-serveur n'est démontrée.
4. **Événements** : notifications locales postcommit, pas de livraison Outbox au-delà d'un crash.
5. **Qualification** : Assessment PASS est un record d'un évaluateur habilité dans la démo, **pas une validation indépendante d'une CI externe**. La source inaccessible reste explicitement indisponible.
6. **Interopérabilité** : aucun sync GitHub, Drive, OAuth, PyAuthKit ou Pythos, volontairement différé.
7. **Architecture** : ADR-M1-04..12 et ADR M0 D-01..D-07 encore à ratifier ; `Q-R0/Q-M0/Q-M1` non prononcés ; PR #4/#6/#9 non fusionnées.
8. **Distribution** : version alpha `0.2.0a1`, **licence non déterminée**, aucune publication PyPI ni tag officiel.
9. **Restauration** : backup/restauration simple testé ; restauration après corruption sévère, rotation, chiffrement et politique de rétention non qualifiées.
10. **Projections** : Registry calculé sur les objets transactionnels, sans cache. La pagination est triée et filtrée, mais n'est pas un snapshot multi-requêtes garanti face à des écritures concurrentes entre appels distincts.

## 6. Verdict de livraison

- **Code M1** : `IMPLEMENTED_FOR_LOCAL_SYNTHETIC_PILOT`.
- **Tests locaux** : `40/40 PASS` sur la copie de travail.
- **CI sur SHA** : `41665577635 SUCCESS`, Python 3.12/3.13 : 40 tests PASS, mypy strict 13 fichiers PASS, wheel PASS.
- **Licences/permissions de distribution** : `NOT_APPROVED`.
- **Gates** : `Q-R0 = NOT_ASSESSED`, `Q-M0 = NOT_ASSESSED`, `Q-M1 = NOT_ASSESSED`.
- **Prochaine action sûre** : revue des ADR restant ouverts, contrat de sécurité sur données réelles, revue des PR empilées, décision humaine formelle de gate.

**Le développement de bout en bout est engagé et son code est disponible. La réussite d'une suite de tests ne remplace pas l'approbation et la qualification formelles du produit.**