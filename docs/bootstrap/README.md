# PyProjectKit - Bootstrap M0 (alpha de développement)

Noyau Python headless pour les projets et tâches, les dépendances acycliques, les jalons et les transactions in-memory. **Ce livrable est un prototype M0 de revue, pas une release publiée ou un Q-M0 approuvé.**

## Installation locale

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/first_project.py
```

- Python `>=3.12` : **cible candidate** actuellement testée sur Python 3.13 dans l'environnement d'exécution. La CI vise 3.12 et 3.13, mais son exécution GitHub reste à confirmer.
- Licence : non décidée. Aucun fichier LICENSE ni revendication de droit de redistribution n'est créé ; ne pas publier sur un index.
- Les permissions doivent venir d'un hôte qui authentifie le principal. La `ExplicitPolicy` et `ActorContext` illustrent une frontière de confiance, ils ne sont **pas** un fournisseur d'identité ni un système d'isolation de code Python hostile.
- InMemory : commit atomique local protégé par verrou et versionnement optimiste ; pas de durabilité de process, pas de concurrence multi-processus.
- Événements locaux stockés après commit confirmé ; pas de bus externe durable ni d'outbox.
- `D-SEM-01` a été accepté pour les identifiants V1/V2, mais les décisions D-01..D-07 doivent encore être ratifiées.

## Découpage

- `domain.py` : entités, value objects, statuts, erreurs et invariants sans I/O.
- `memory.py` : stores InMemory, repositories, graphe et UnitOfWork avec working set isolé.
- `service.py` : API applicative, commands/queries, policy d'autorisation et événements transactionnels.

Voir `docs/qualification/BOOTSTRAP_REPORT.md` pour le périmètre des preuves exactes et les réserves.