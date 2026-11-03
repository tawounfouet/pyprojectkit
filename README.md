# PyProjectKit - prototype M0 + M1 (registre local)

**Statut** : implémentation de revue sur `feat/m1-registry-continuity`, empilée sur `feat/m0-bootstrap`. Ni Q-R0, ni Q-M0, ni Q-M1 n'ont été approuvés. **Pas de publication PyPI ni de traitement de données sensibles réelles.** Licence en attente.

## Portée du prototype

- **M0 préservé** : `Project`, `Task`, `Milestone`, dépendances acycliques, UoW InMemory et événements après commit.
- **M1-A** : adaptateur `sqlite3` durable, migration 0001/0002 checksummée, versions optimistes, sauvegarde SQLite, ContextScope et cinq familles de registre.
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
```

**Limites** : SQLite local non chiffré et non multi-serveur, UoW avec `BEGIN IMMEDIATE` sérialisant les writers, pas d'outbox distribuée, pas de connecteur IAM, OAuth, Pythos, GitHub/Drive sync, ni protection contre un programme Python hostile déjà dans le même processus. Une évaluation `PASS` est un **record applicatif déclaré par un évaluateur autorisé**, pas une vérification CI indépendante : les fixtures n'affirment pas une qualification de projet réel.

Les preuves GitHub Actions, la matrice AC-013..AC-026 et les limites seront conservées dans `docs/qualification/M1_REPORT.md` en liaison avec l'issue GitHub M1 #8.