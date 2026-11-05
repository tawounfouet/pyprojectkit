# PyProjectKit - VS01, clôture technique et passage au jalon suivant

> Nature : note de handoff technique. Les résultats post-merge ne sont **pas** anticipés ici.

## Critères techniques VS01

1. Le package historique `pyprojectkit` reste importable, ses tests M0/M1/M2 restent exécutables et ses migrations SQLite `0001..0003` inchangées.
2. `pyprojectkit_next` apporte Project, Task, jalons, dépendances acycliques, changements d'état, affectation, progression, owner+scope fail-closed, événements post-commit, Unit of Work InMemory avec rollback et concurrence conservatrice.
3. Un test différentiel compare un scénario M0 réel au noyau VS01. Il qualifie **le sous-ensemble commun** uniquement, pas la substitution complète des API historiques.
4. CI verte sur Python 3.12 et 3.13, tests de négation de permissions, `mypy --strict`, wheel isolée installée hors du dépôt, GitGuardian.
5. Fusion additive sans suppression, sans modification de données, et audit `main` post-merge au SHA exact.

## Contrat de non-substitution

Les interfaces exposées par le namespace `pyprojectkit` restent le contrat de compatibilité legacy. `pyprojectkit_next` conserve un contrat expérimental distinct : ID chaînes canoniques (interop UUID explicite), API immutable, politique owner+scope plus restrictive, noms d'événements parfois différents et UoW in-memory conservatrice. Aucun alias transparent ni suppression de code historique. La fusion du prototype sur `main` ne valide pas une migration de données ni un changement de release PyPI.

## Gouvernance et portée de la fusion

L'utilisateur, propriétaire du projet, a explicitement demandé la finalisation et la fusion du milestone le 5 novembre 2026. Cette autorisation concerne **une fusion additive et testée** de VS01 (et la baseline R3.1 si elle est qualifiée), sans autoriser la substitution du noyau, ARCH-02, l'archivage legacy ou une publication. `G0=PENDING`, `ARCH-02=BLOCKED`, `Q-M2=PENDING` sont conservés tant que leurs propres exigences ne sont pas satisfaites.

La branche `main` n'avait aucune protection effective lors du préflight. La configuration d'une protection reste une tâche administrative ouverte. Aucune revue indépendante n'est inventée : le propriétaire a choisi de reporter la nomination de reviewer (HD-08).

## Prochain milestone recommandé

**VS-REBOOT-02 - Contrats publics, interfaces et persistance** (à cadrer) :

- Recenser les consommateurs de l'API M0 et qualifier les éventuelles ruptures ; conserver les imports legacy.
- Définir le port de persistance durable, la stratégie de migration/compatibilité et les tests de restauration sur données **synthétiques uniquement**.
- Évaluer les permissions fines et la séparation authn/authz en conservant le fail-closed ; tout outbox, IAM réel ou usage Pythos exige une qualification distincte.
- Préparer un gate décisionnel avant toute substitution ou migration de données réelles.

## Preuves attendues à la clôture

Inscrire dans le bilan final les SHA de PR #21, PR #22 et `main`, les conclusions de checks au HEAD et post-merge, les tests exacts et les limitations inchangées. Ne pas marquer « post-merge verified » avant que GitHub l'ait effectivement prouvé.
