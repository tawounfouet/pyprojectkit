# ARCH-06 - Contrat de persistance V1, candidat limité

> Statut : `CANDIDATE / MEMORY_CHARACTERIZED / SQLITE_NOT_IMPLEMENTED / G2_PENDING`.
> Périmètre : `VS-REBOOT-02`, préparation de `A06-01` et `A06-02` uniquement.
> Source de référence : `2026-11-05_PYPROJECTKIT_ARCH_06_ARCH_07_IMPLEMENTATION_PLAN.md`, sections 2, 3, 5 et `RS-AC-01..14`.

## 1. Problème métier avant la technologie

Le noyau `pyprojectkit_next` fonctionne en mémoire, au sein d'un processus. L'utilisateur souhaite pouvoir retrouver un projet après redémarrage et obtenir les mêmes décisions métier et refus d'accès avec un support durable. **Un `Protocol` qui compile ne suffit pas** : il faut caractériser les transitions, conflits et défaillances observables, puis comparer le futur adapter SQLite aux mêmes oracles sur données synthétiques.

Ce document fixe un **contrat candidat**, pas un ADR adopté et pas un mandat de création du schéma SQLite avant `G1=GO` et `G2=GO` (ou décision formelle de dérogation).

## 2. Port existant : état de fait

Le port `UnitOfWork` de `src/pyprojectkit_next/ports.py` expose `get/list/add/save` pour Project/Task, `list/add_dependency`, `record` et `commit`. Le port et l'adapter mémoire actuels ne proposent **pas** :

- de méthode `rollback()` explicite ; la sortie sans commit abandonne les modifications locales ;
- de journal d'événements durable ou d'outbox ; `InMemoryDatabase.events` est un journal volatile ;
- d'opération de réconciliation `CommitOutcomeUnknown` ;
- de version de schéma, migration, transaction interprocessus, backup et restauration de fichiers ;
- de `RegistryReader` paginé avec count, facettes et contrôle d'accès avant agrégation.

**Ne pas assimiler ces absences à des comportements déjà prouvés.** La Memory UoW utilise une révision globale CAS en processus ; cette approche est volontairement conservatrice et ne définit pas automatiquement la stratégie SQLite.

## 3. Obligations comportementales du futur adapter

| Contrat | Oracle | Preuve Memory | Preuve SQLite |
|---|---|---|---|
| `C06-01` Atomicité Project/Task + graphe + journal local | Sans commit, aucune écriture ; avec commit, toutes ou aucune | Test de rollback | Non implémenté |
| `C06-02` CAS et isolation | Une transaction obsolète ne remplace pas un commit concurrent | Conflit interleaving | Non implémenté |
| `C06-03` Fermeture et création concurrentes | Pas de projet terminé avec tâche ouverte apparue après le contrôle, même si le port UoW est utilisé directement | Interleavings + validation au commit du snapshot final | Non implémenté |
| `C06-04` Dépendances acycliques | Refus cycle et inter-projets ; état inchangé | Tests graphe | Non implémenté |
| `C06-05` Domain Events | Aucun event avant confirmation ; aucune réussite inventée | Tests d'événements locaux | Outbox durable à concevoir |
| `C06-06` Autorisation de lecture | Même résultat sur une Query lorsqu'on ajoute des objets cachés | Test métamorphique | RegistryReader différé |
| `C06-07` Persistance durable | Réouverture après arrêt du processus conserve identités, statuts et versions | Non applicable | Non implémenté |
| `C06-08` Migration et recovery | Schéma checksummé ; restauration et corruption fail-closed | Non applicable | Non implémenté |
| `C06-09` Résultat de commit ambigu | Pas de succès fictif ni de retry aveugle ; réconciliation sur intention identifiée | Simulateur séparé, non transactionnel, testé | Non implémenté |

## 3.1. Invariant inter-agrégats renforcé sur Memory

La validation de `C06-03` ne peut pas reposer seulement sur `ProjectService` : un appel direct à `UnitOfWork` ne doit pas persister un projet `COMPLETED` tant qu'il reste une tâche non terminale. `InMemoryUnitOfWork.commit()` contrôle l'état final du snapshot avant écriture et émission d'événement. `add_task()` refuse les parents `COMPLETED` ou `CANCELLED`. La clôture coordonnée d'une tâche et de son projet dans une même UoW reste autorisée. La même règle devra être imposée atomiquement dans l'adaptateur SQLite futur.

**Ceci protège la cohérence locale, sans établir la durabilité, une isolation interprocessus ni une autorisation G3.**

## 3.2. Contrat expérimental de résultat de commit ambigu

La simulation de la perte d'accusé et de l'idempotence est maintenant exécutable dans `pyprojectkit_next.recovery`. Son journal volatile ne partage aucune transaction avec `InMemoryUnitOfWork` : **elle ne constitue pas une preuve de persistance ou de reprise après redémarrage**. Voir `docs/contracts/ARCH06_COMMIT_OUTCOME_AND_IDEMPOTENCY_SIMULATION_V1.md` et ses oracles `C06-09.1..8`. Le futur port SQLite devra qualifier `RS-AC-09` dans une transaction réellement durable, sous les gates applicables.

## 4. Sémantique d'erreur attendue

Les erreurs actuelles du noyau sont `Conflict`, `NotFound`, `InvalidStateTransition`, `DependencyViolation`, `AccessDenied`. Le port durable ne doit pas faire remonter une exception brute contenant un chemin SQLite, un SQL text ou un secret. Un futur `CommitOutcomeUnknown` doit être **distinct** de `Conflict`, avec mécanisme de réconciliation et règles d'idempotence documentés avant adoption. Une erreur de lecture d'un objet invisible et un objet absent ne doit pas révéler l'existence de la ressource.

## 5. Conformité et limites RS-AC

| Critère | État au démarrage A06-02 | Précision |
|---|---|---|
| `RS-AC-01` | `PARTIAL` | Parcours Memory caractérisé, aucun SQLite |
| `RS-AC-02` | `MEMORY_PASS_ONLY` | Rollback UoW, pas de disque |
| `RS-AC-03` | `MEMORY_PASS_ONLY` | Interleaving in-process, pas multiprocessus |
| `RS-AC-04` | `MEMORY_PASS_ONLY` | Course fermeture/création bornée |
| `RS-AC-05` | `MEMORY_PASS_ONLY` | Cycle et cross-project ; concurrency durable non démontrée |
| `RS-AC-06..08` | `NOT_IMPLEMENTED` | Migrations, backup/restore, corruption |
| `RS-AC-09` | `SIMULATOR_ONLY` | Failpoints et réconciliation en mémoire seulement, sans backend durable |
| `RS-AC-10` | `MEMORY_PASS_ONLY` | Filtrage owner/scope sur Query exposée |
| `RS-AC-11` | `PARTIAL` | Métamorphisme `list_projects` oui ; count/facet/page inexistants |
| `RS-AC-12..13` | `DEFERRED` | Portfolio multiple et référence fournisseur |
| `RS-AC-14` | `PENDING_CI` | Requiert tests au SHA courant, deux Pythons et wheel isolée |

## 6. Contrôles avant le prochain lot

1. Tracer les gates `G0/G1/G2` et obtenir la revue des ADR de persistance.
2. Décider si la CAS SQLite doit être globale (par DB) ou granulaire (par aggregate) et le contrat des transactions concurrentes.
3. Prévoir l'outbox durable comme **même transaction** que les mutations, puis les règles de lecture/publication.
4. Définir et tester le refus des versions de schéma futures/altérées, backup/restore et échec ambigu.
5. Reprendre **ces mêmes tests paramétrés** avec un adapter SQLite avant toute déclaration `RS-AC PASS`.

## 7. Convention Software Design & Learning

- **Problem before Pattern** : éviter la perte de projets et les états incohérents.
- **Unit of Work + Optimistic Concurrency** : une transaction et un contrôle de version au lieu de commits épars.
- **Hexagonal Architecture / DIP** : use cases dépendants du port, jamais de `sqlite3`.
- **Contract Testing** : les mêmes oracles pour Memory et SQLite, avec des preuves distinctes.
- **Evidence before Status** : `MEMORY_PASS_ONLY` ne signifie pas `G3=GO`.

**Aucun schéma SQLite, aucun adaptateur durable et aucune donnée réelle créés dans cette tranche.**
