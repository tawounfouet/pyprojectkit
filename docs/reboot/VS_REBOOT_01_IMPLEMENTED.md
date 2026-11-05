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
| Dépendances, jalons, cycles de graphe | Implémentés sur le sous-ensemble : graphes acycliques, gardes de démarrage, dates et jalons immuables ; la parité M0 intégrale reste non démontrée |
| Authentification | **NON IMPLÉMENTÉE** ; l'hôte doit fournir un `ActorContext` fiable, non forgeable à sa frontière |
| AuthZ | Politique owner+scope expérimentale ; RBAC réel, multi-tenant et délégation différés |
| Unit of Work | InMemory mono-processus, conflit global conservateur |
| Events | Journal local post-commit, **pas** d'outbox, de bus ou de garantie de livraison |
| M1 / M2 / SQLite 0001..0003 | **DEFER**, aucune migration |
| Packaging et version de release | Version legacy inchangée, aucune publication |

## Lancer

```bash
python -m pip install -e '.[test]'
python -m pytest -q tests/test_reboot_vs01.py tests/test_reboot_vs01_parity.py
python examples/reboot_vs01_demo.py
```

## Règles avant une suite

1. Préserver la CI historique, les 168 tests legacy et les imports `pyprojectkit`.
2. Ne pas fusionner cette PR avant CI complète et décision de gouvernance applicable.
3. Ne pas écraser `main` ni modifier/supprimer M0/M1/M2 avant archive indépendante restaurée et mandat distinct.
4. Assumer qu'une revue indépendante Q-M2 demeure à traiter séparément, sans auto-approbation.

## Extension de parité M0 (2026-11-05)

- Graphe de dépendances transactionnel (snapshot immutable, cycle, doublons, inter-projets, scope).
- Démarrage ou déblocage de tâche impossible tant qu'un prérequis n'est pas `DONE`.
- Jalons datés et immuables, création et atteinte transactionnelles.
- Concurrence conservatrice : un commit d'écriture invalide tout snapshot ancien ; les graphes ne se corrompent pas.
- Différences non résolues : IDs `str` (M0 legacy : UUID), assignation, progression, `IN_REVIEW -> IN_PROGRESS`, contrats publics et permissions fines ; pas de parité totale revendiquée.

## Extension de parité M0 : affectation, progression et revue

Statut : implémentation expérimentale additive, sans changement de `pyprojectkit` historique.

- `Task.assignee_id` est une valeur immuable ; `assign_task()` refuse une affectation vide, identique ou effectuée sur une tâche terminale. L'identité du destinataire n'est **pas** vérifiée auprès d'un IAM réel.
- `Task.progress` est un entier strict (pas de booléen) entre 0 et 100. `update_task_progress()` exige une tâche `IN_PROGRESS` ou `IN_REVIEW` et un projet actif. `DONE` force `progress=100`. Comme dans le modèle M0 existant, `progress=100` avant le statut `DONE` n'est pas interdit par la seule validation de valeur : cela ne déclenche aucune clôture implicite.
- `actual_start_at` est enregistré au premier `start_task()` et conservé lors des déblocages et retours de revue ; le temps provient de l'horloge injectée.
- `return_task_to_work()` expose `IN_REVIEW -> IN_PROGRESS`, contrôle le statut du projet et les prérequis, sans créer de progression ni de date nouvelles.
- Événements `TaskAssigned`, `TaskProgressUpdated` et `TaskReturnedToWork` alimentent uniquement le journal InMemory après succès du commit. Les refus, conflits et rollbacks ne publient aucun événement.
- Les nouvelles opérations réutilisent la politique fail-closed `owner+scope` ; elles ne confèrent pas de rôle ni de permission GitHub.
- Tests de contrat et tests négatifs dans `tests/test_reboot_vs01_task_semantics.py`, exécutés en CI sur Python 3.12 et 3.13. La parité complète de tous les contrats publics M0 reste à qualifier, notamment le format historique des identifiants et la granularité de permission.

Le noyau reste isolé, la PR demeure un brouillon et aucune migration M1/M2 n'est autorisée par cette extension.
