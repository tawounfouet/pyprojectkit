# VS-REBOOT-01 - Noyau expérimental isolé

> Date : 2026-11-05 | Statut : `EXPERIMENTAL` | G0 : `PENDING` | ARCH-02 : `BLOCKED`

## Objectif et frontières

Ce changement ajoute `pyprojectkit_next` dans **le même dépôt**, sans remplacer `pyprojectkit` ou modifier les migrations SQLite historiques. Il est volontairement **additif** : la véritable bascule Clean Reboot reste conditionnée à l'archivage restaurable et aux gates encore ouverts.

## Réalisé

- Entités `Project` et `Task` immuables, identifiants typés, transitions validées et versions monotones.
- Couche application avec autorisation **owner + scope**, refus par défaut, horloge et génération d'IDs injectées.
- Adaptateur InMemory et Unit of Work : snapshots isolés, commit atomique, rollback implicite, conflits optimistes, journal local d'événements alimenté seulement après commit réussi.
- Exécution strictement synthétique, sans données réelles, SQLite, Pythos ou droits GitHub.
- Tests : créations, transitions, dates, autorisations, sécurité négative, refus de clôture, rollback, conflits, événements.

## Parité et limites

| Domaine | Niveau VS01 |
|---|---|
| Project / Task / statuts / IDs | Sous-ensemble implémenté, tests locaux et CI |
| Dépendances, jalons, cycles de graphe | **NON IMPLÉMENTÉ** ; ne pas déclarer de parité M0 intégrale |
| Authentification | **NON IMPLÉMENTÉE** ; l'hôte doit fournir un `ActorContext` fiable, non forgeable à sa frontière |
| AuthZ | Politique owner+scope expérimentale ; RBAC réel, multi-tenant et délégation différés |
| Unit of Work | InMemory mono-processus, conflit global conservateur |
| Events | Journal local post-commit, **pas** d'outbox, de bus ou de garantie de livraison |
| M1 / M2 / SQLite 0001..0003 | **DEFER**, aucune migration |
| Packaging et version de release | Version legacy inchangée, aucune publication |

## Lancer

```bash
python -m pip install -e '.[test]'
python -m pytest -q tests/test_reboot_vs01.py
python examples/reboot_vs01_demo.py
```

## Règles avant une suite

1. Préserver la CI historique, les 168 tests legacy et les imports `pyprojectkit`.
2. Ne pas fusionner cette PR avant CI complète et décision de gouvernance applicable.
3. Ne pas écraser `main` ni modifier/supprimer M0/M1/M2 avant archive indépendante restaurée et mandat distinct.
4. Assumer qu'une revue indépendante Q-M2 demeure à traiter séparément, sans auto-approbation.
