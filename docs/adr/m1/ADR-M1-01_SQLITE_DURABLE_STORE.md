# ADR-M1-01 - SQLite comme premier adaptateur durable de PyProjectKit

> Statut : **ACCEPTED_FOR_M1_LOCAL_PILOT** - décision technique déléguée, 2026-11-03
>
> Décideur : Pythos, dans le périmètre de cadrage technique autorisé par le propriétaire
>
> Mandat et traçabilité : https://github.com/tawounfouet/pyprojectkit/issues/8#issuecomment-6607173475
>
> Document de référence : [plan d'implémentation M1](../../implementation/15_PYPROJECTKIT_M1_IMPLEMENTATION_PLAN.md), sections 4, 8.1, 9, 12, 16
>
> Interdit : interpréter cet ADR comme un `Q-M1 GO`, un support production multi-serveur ou une approbation de publication du package.

## 1. Problème

M0 sauvegarde Project, Task, Milestone et le graphe dans une `InMemoryDatabase` protégée par `RLock` du processus. Les 17 tests et la CI prouvent des scénarios de transaction en mémoire, **pas** la reprise après arrêt du processus ni les conflits entre processus. M1 exige un registre durable, des projections et une reprise explicable sans dépendre d'une conversation.

Le premier vertical slice `VS-M1-01` exige `Persist -> Stop -> Restart -> Resume`, identités et versions conservées, aucune fuite cross-scope.

## 2. Alternatives

| Option | Analyse | Décision |
|---|---|---|
| A. SQLite via `sqlite3` standard library | Fichier local autonome, transactions, contraintes, pilote reproductible hors réseau, compatibilité Python M0 ; migration et locking à implémenter | **RETENUE pour pilote M1 local** |
| B. PostgreSQL d'emblée | Concurrence multi-connexions plus large et administration puissante ; impose serveur, provisioning, secrets et surface opérationnelle plus importante | Différée ; port de substitution préservé |
| C. Fichier JSON ou pickle | Facile pour une démo, mais garanties de transaction, migrations, FKs, recherche et sécurité insuffisantes ; pickle non fiable dangereux | Non retenue |
| D. SQLite comme unique backend définitif | Simplifie l'offre, mais impose une limite non démontrée à de futurs usages | Non retenue |

## 3. Décision et bornes

**DEC-M1-PERSIST-01** : implémenter `SqliteUnitOfWork`, `SqliteProjectRepository`, `SqliteTaskRepository` et `SqliteDependencyGraphPort` derrière les **ports M0 existants** lorsque leurs garanties sont compatibles ; ajuster les ports uniquement par ADR de compatibilité avec tests InMemory et SQLite.

- **Unité transactionnelle** : Project, Task, Milestone et dépendances d'un même use case doivent être validés dans la même transaction `sqlite3.Connection` lorsqu'une atomicité commune est promise.
- **Durabilité pilote** : base fichier local identifiée par chemin explicite ; connexion à durée de vie bornée, ouverte/fermée proprement. Pas de base en RAM ni de secret de chemin enregistré dans un export public.
- **Portabilité** : tests de compatibilité sur Python 3.12 et 3.13 ; ne pas rendre FastAPI, Django, PyAuthKit, Pythos ni SQLAlchemy obligatoires.
- **Concurrence** : contrôle optimiste `expected_version` par AR et **révision commune du graphe par Project** sous transaction SQL. La détection de cycles sur une simple copie mémoire ne suffit pas.
- **Atomicité des événements** : Domain Events de succès observables localement seulement après commit confirmé ; un Outbox durable n'est pas imposé tant que la livraison interprocessus n'est pas demandée. L'absence d'Outbox doit rester visible.
- **Limitation** : pas de garantie de service multi-tenant réseau, de haute disponibilité, de réplication ni de durabilité face à tous les modes de panne système.

## 4. Choix techniques à mesurer, sans faux contrat

- `PRAGMA foreign_keys=ON` sur chaque connexion.
- `busy_timeout` configurable et borné ; un verrouillage prolongé doit produire une erreur/échéance explicite.
- `BEGIN IMMEDIATE` candidat pour les transactions d'écriture ; le choisir après mesurer la contention, pas pour prétendre résoudre tous les conflits.
- `journal_mode=WAL` **optionnel** pour le pilote ; garder le mode effectif traçable et valider la politique de copie/sauvegarde.
- Utiliser `sqlite3.backup()` pour des sauvegardes cohérentes, avec tests de restauration ; ne pas copier simplement une base WAL ouverte.
- Ne pas journaliser de données confidentielles, de contenu de preuve ni de SQL paramétré contenant des secrets.
- Données de test **synthétiques**, aucune archive financière/client/employeur autorisée par défaut.

## 5. Contrat de stockage indispensable avant implémentation

1. `get`, `add`, `save(expected_version)`, `list`, `snapshot(project_id)`, `replace_if_version` et `commit` observables de façon comparable à M0.
2. Aucune mutation visible depuis une nouvelle connexion si la UoW sort sans commit.
3. Les erreurs d'identité, version, verrouillage, contrainte ou commit incertain sont typées sans masquer la cause métier.
4. Les lectures de données sous scope passent d'abord par l'autorisation applicative ; aucune requête scalaire ou rapport ne doit lire les lignes interdites puis compter.
5. Une session SQLite n'est jamais un acteur autorisé par sa seule possession du chemin fichier. Le contrôle d'accès du système d'exploitation au fichier reste une barrière supplémentaire, non un remplacement de la policy métier.

## 6. Preuves bloquantes pour le premier vertical slice

- `M1-01` : ADR enregistré, version `sqlite3.sqlite_version`, OS et PRAGMAs relevés.
- `M1-02` : contrat InMemory/SQLite identique pour les invariants et refus, tests sur même suite.
- Deux **processus distincts** accèdent à un même fichier : une mise à jour obsolète échoue ; les écritures concurrentes de graphe ne produisent aucun cycle.
- `stop -> restart` avec Project, Task, Milestone et Dependency puis nouvelles Queries.
- Rejouer le fichier migré après fermeture totale et vérifier les identités et versions.
- Rollback sans commit, exception et crash injecté ; aucune mutation partielle présentée comme succès.
- Test de sauvegarde et restauration, aucune preuve privée dans artefacts CI.
- Refus hors scope et tests sur counts/exports/erreurs en collaboration avec ADR-M1-03.

## 7. Critères de révision et risques

Réviser l'ADR si un besoin avéré de plusieurs writers distribués, de chiffrement au repos géré ou d'HA dépasse les limites de SQLite. Le port doit permettre un adapter PostgreSQL ultérieur sans import SQL dans le domaine.

**Non couvert** : schema exact, migrations et sérialisation, couverts par [ADR-M1-02](ADR-M1-02_SCHEMA_MIGRATION_AND_UOW.md) ; autorisation par [ADR-M1-03](ADR-M1-03_CONTEXT_SCOPE_AND_AUTHORIZATION.md).

**Statut d'exécution au moment de la décision : NOT_IMPLEMENTED / NOT_TESTED**. L'approbation porte sur le **choix d'architecture pour le pilote local M1**, pas sur sa mise en œuvre.
