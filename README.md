# PyProjectKit - noyau M0, registre M1 et pilote synthétique M2

**Statut (2026-11-05)** : prototype alpha M0/M1/M2 intégré dans `main` et qualifié techniquement uniquement sur données synthétiques. Gate humain Q-M2 **en attente**, protection de `main` absente. Historique : [accord conditionnel d'intégration](docs/gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md). Cette décision ne vaut pas autorisation de publication, d'usage en production ni de traitement de données réelles sensibles. **Licence en attente, aucune publication PyPI.**

**Mise à jour de clôture VS01 (2026-11-05)** : la baseline R3.1 (PR #21) et le noyau expérimental VS01 (PR #22) sont **fusionnés de manière additive sur `main`**. Les 257 tests sur Python 3.12 et 3.13 passent au SHA `84cb3bd824e4c84dbc37d0eef26700a944999fbe`, ainsi que les 89 tests VS01, le typage strict et l'installation de wheel isolée. Il ne s'agit ni d'une substitution du legacy, ni d'une release, ni d'une approbation de Q-M2. [Handoff VS01](docs/reboot/VS01_MILESTONE_CLOSEOUT_AND_NEXT.md), [CI complète](https://github.com/tawounfouet/pyprojectkit/actions/runs/42097758699), [CI VS01](https://github.com/tawounfouet/pyprojectkit/actions/runs/42097758638).

## M2 - périmètre actuellement intégré

M2-A/B/C propose des contrats d'OperatingBrief, un mandat hôte, une inbox SQLite pour les reports, une réconciliation idempotente et une Query de reprise. Les deux pilotes sont **synthétiques** ; aucun runtime Pythos réel ni commande externe privilégiée n'est implémenté. Les PR #16/#17/#18 sont fusionnées, mais **Q-M2 reste en attente de revue humaine indépendante** avec AC-031 et AC-034 partiels. Voir [issue #20](https://github.com/tawounfouet/pyprojectkit/issues/20).

Le chantier R3.1 a été intégré comme **documentation** par la PR #21, sans modification du code métier historique. La précédence des plans 26/27 a été arbitrée pour le cadrage, avec texte 27 incomplet. Les validations de release, Q-M2 et G0 restent indépendantes. [Audit R3.1](docs/r3/2026-11-05_R3_1_BASELINE_RECONCILIATION.md), [matrice 26/27](docs/r3/2026-11-05_R3_1_M3_26_27_CROSSWALK.md) et [registre des décisions](docs/r3/2026-11-05_R3_1_ARBITRATION_AND_LIMITED_CLOSEOUT.md).

## Portée du prototype

- **M0 préservé** : `Project`, `Task`, `Milestone`, dépendances acycliques, UoW InMemory et événements après commit.
- **M1-A** : adaptateur `sqlite3` durable, migrations 0001/0002/0003 checksummées, versions optimistes, sauvegarde SQLite, ContextScope et cinq familles de registre.
- **M1-B** : références externes scoped, Claim/Observation, EvidenceRef, assessments ciblés par version, cas de réconciliation avec conservation des contradictions, décisions et approbations distinctes.
- **M1-C** : snapshots append-only, handoff, contexte de reprise et NextAction explicite (y compris `NONE_WITH_REASON`).
- **M1-D** : tests multi-processus, tests de non-divulgation par scope et enfant privé, cinq familles synthétiques et profils de policy différents.

### Démarrer

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/first_project.py
python examples/m1_registry_demo.py
```

### CLI de démonstration

```bash
pyprojectkit --demo --db /tmp/pyprojectkit-pilot.sqlite init
pyprojectkit --demo --db /tmp/pyprojectkit-pilot.sqlite register --family PACKAGE --name 'Démo synthétique'
pyprojectkit --demo --db /tmp/pyprojectkit-pilot.sqlite list
```

La CLI refuse les appels sans `--demo`. **Le credential démonstratif intégré au code est public et ne constitue pas une authentification réelle.** Il n'est valable que pour les fixtures synthétiques. Les projets et scopes sont créés uniquement dans le chemin SQLite explicitement choisi, qui doit rester hors du dépôt et des artefacts CI.

### Usage Python M1

```python
from pathlib import Path
from pyprojectkit.m1 import RegistryService, SqliteDatabase, TrustedHost

host = TrustedHost({"secret-provisionné-hors-payload": ("alice", {"scope-fixture": {
    "SCOPE_CREATE", "PROJECT_VIEW", "PROJECT_CREATE", "TASK_VIEW", "RESUME"
}})})
actor = host.authenticate("secret-provisionné-hors-payload", "scope-fixture")
service = RegistryService(SqliteDatabase(Path('/tmp/pyprojectkit-local.sqlite')), host)
service.create_scope(actor)
pid = service.register_project(actor, "Projet synthétique", "PACKAGE")
print(service.resume(actor, pid).next_action.reason)
```

Ne pas soumettre `actor_id`/`scope` fournis librement par une requête comme preuve d'identité. Seul un adaptateur hôte de confiance peut construire les principaux autorisés. Les accès au système de fichiers doivent être restreints par le système d'exploitation : le code Python exécuté localement avec accès direct au fichier SQLite n'est **pas** isolé par les policies applicatives.

## Architecture

```text
src/pyprojectkit/{domain,ports,memory,service}.py   # M0 inchangé
src/pyprojectkit/m1/schema.py                       # SQLite migrations
src/pyprojectkit/m1/sqlite.py                       # UoW, repositories, graph, history
src/pyprojectkit/m1/security.py                     # TrustedHost + verified context
src/pyprojectkit/m1/models.py                       # M1 read models
src/pyprojectkit/m1/service.py                      # M1 Commands/Queries
src/pyprojectkit/m1/cli.py                          # démonstration synthétique
src/pyprojectkit_next/                                # nouveau noyau expérimental VS01, additif
```

**Limites** : SQLite local non chiffré et non multi-serveur, UoW avec `BEGIN IMMEDIATE` sérialisant les writers, pas d'outbox distribuée, pas de connecteur IAM, OAuth, Pythos, GitHub/Drive sync, ni protection contre un programme Python hostile déjà dans le même processus. Une évaluation `PASS` est un **record applicatif déclaré par un évaluateur autorisé**, pas une vérification CI indépendante : les fixtures n'affirment pas une qualification de projet réel.

Les preuves GitHub Actions, la matrice AC-013..AC-026 et les limites seront conservées dans `docs/qualification/M1_REPORT.md` en liaison avec l'issue GitHub M1 #8.

## Qualification complémentaire de sécurité et d'intégration

Le contrôleur M1 filtre maintenant les projets d'un même scope par **propriétaire** ou par partage explicite provenant de l'hôte vérifié : `PROJECT_VIEW_ALL` ou `PROJECT_VIEW:<uuid>`. Un droit `PROJECT_VIEW` seul ne donne plus accès aux projets d'autres propriétaires. Les Queries, comptes, facettes, exports et reprises respectent cette restriction. Cette propriété s'applique au pilote local avec processus hôte de confiance, pas à un service exposé au code hostile.

**CI historique sur main (2026-11-04, SHA `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`)** : [run #208](https://github.com/tawounfouet/pyprojectkit/actions/runs/41919258680) - 168 tests pytest par Python 3.12/3.13, `mypy --strict`, wheel isolée. Ces résultats ne valent pas autorisation de production ou publication. Dossier historique : [Gate alpha](docs/gates/2026-11-03_R0_M0_M1_MAIN_INTEGRATION_GATE.md) et [rapport M1](docs/qualification/M1_REPORT.md).
