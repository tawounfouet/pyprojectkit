# ADR-M1-02 - Schéma SQLite, migrations, sérialisation et UoW

> Statut : **ACCEPTED_FOR_M1_LOCAL_PILOT** - décision technique déléguée, 2026-11-03
>
> Mandat : https://github.com/tawounfouet/pyprojectkit/issues/8#issuecomment-6607173475
>
> Source : plan M1 sections 4.2-4.3, 8.1, 9, 12, 16 ; [ADR-M1-01](ADR-M1-01_SQLITE_DURABLE_STORE.md).
>
> Pas de schéma de production ou de migration exécutée à la date de cette décision.

## 1. Motivation

Le M0 InMemory applique des copies isolées et un contrôle de versions avant écriture sous `RLock`. Ce comportement n'est pas une preuve d'atomicité SQLite, de migration d'une ancienne base ni de sûreté concurrente multi-processus. M1 doit **conserver les invariants sans changer silencieusement l'API publique M0**.

## 2. Alternatives

- **A. Schéma relationnel explicite, migrations ordonnées, FKs, contrainte de version et payload JSON strictement validé lorsque nécessaire. RETENUE.**
- B. Une table générique `objects(id, type, pickle)` : difficile à migrer, dangereuse avec des données non fiables et opaque pour les autorisations. Rejetée.
- C. ORM obligatoire d'emblée : utile ultérieurement si coût prouvé, mais non indispensable au pilote et contraire au minimalisme initial. Différée.
- D. Déduire le schéma au démarrage des objets Python sans versions : risque de rupture et de perte de données. Rejetée.

## 3. Décision appliquée aux contrats futurs

**DEC-M1-DATA-01 - Tables minimales M1-A** : `schema_migrations`, `projects`, `tasks`, `project_milestones`, `task_dependencies`, `dependency_graph_versions`, `context_scopes`, `project_scope_links`. Les autres tables M1-B/C seront créées par migrations ultérieures, pas à vide sans besoin.

- Identifiants `ProjectId`, `TaskId`, `MilestoneId` persistés sous représentation stable (UUID textuel normalisé), jamais dérivés des noms.
- Toutes les tables ressources portent ou permettent de résoudre une relation explicite au `ScopeId`, à une `ProjectId` autorisée et à leurs éventuelles permissions propres.
- FKs activées, unicité et index par scope/référence ; suppression en cascade **interdite** par défaut pour les preuves, décisions, observations et historiques.
- Les statuts sont persistés sous valeurs canoniques du domaine ; changement d'Enum = migration ou mapping explicite.
- Dates enregistrées sous format ISO 8601 avec fuseau UTC lorsque nécessaires ; `target_date` est une date civile distincte d'un instant `reached_at`.
- Versions optimistes entières pour Project et Task et révision unique de graphe par Project, avec `UPDATE ... WHERE id=? AND version=?` et vérification exacte du nombre de lignes affectées.
- Pas de `pickle` ni d'import de classes arbitraires depuis une colonne ; JSON versionné et validé aux frontières pour les payloads qui le justifient.
- Éviter qu'un `Milestone` interne au Project devienne un Aggregate Root juste pour faciliter les requêtes SQL.

## 4. Migrations et sûreté opérationnelle

**DEC-M1-DATA-02** : migration `0001` initiale suivie de migrations ordonnées, versionnées et tracées par checksum. Un changement de fichier de migration déjà appliqué doit être rejeté et expliqué, jamais accepté silencieusement.

- Préconditions explicites : version/état du schéma, copie de sauvegarde cohérente et risque destructif évalué.
- Exécution transactionnelle lorsqu'elle est supportée pour les opérations concernées ; ne pas supposer que tous les changements de schéma, PRAGMAs ou migrations arbitraires sont atomiques.
- Préférer des migrations *forward-only* et des restaurations testées ; aucun `down` destructif automatique.
- Le chemin de fichier est contrôlé, ne dépend pas d'une chaîne non fiable fournie par la Query, et sa permission OS est restreinte.
- Journal de migration et erreurs dépourvus de données sensibles.

## 5. Contrat de transaction et de cohérence

**DEC-M1-DATA-03** : `save()` modifie seulement l'état transactionnel courant, `commit()` explicite. Hors commit, sortie de scope et exception doivent annuler la transaction. Le service Application ne connaît ni `sqlite3` ni le nom des tables.

- `SqliteUnitOfWork` ouvre/ferme exactement une frontière de connexion/transaction par use case, sans auto-commit par Repository.
- Les ports M0 doivent être substituables : implémentation InMemory et SQLite sur **une suite de tests contractuelle commune**, en distinguant les garanties spécifiques à chaque adapter.
- Après commit confirmé, événements de succès locaux. Entre commit et dispatch, une panne peut perdre une notification : **ne pas promettre de livraison durable** sans Outbox.
- Si le résultat du commit est inconnu après interruption, lever `CommitOutcomeUnknown` ou équivalent, conserver un `operation_id`/correlation id suffisamment durable pour une **relecture de réconciliation**, et ne pas rejouer aveuglément.
- Une exception due à `SQLITE_BUSY` ne garantit pas que l'écriture a été annulée si la phase de commit était incertaine : gérer le stade de transaction et la garantie effective.
- Aucun snapshot M1 capturé par une Query ne doit prétendre être un instant parfaitement cohérent entre sources si le watermark ne l'établit pas.

## 6. Suite de preuves à produire avant qualification

| Test | Contrat |
|---|---|
| `SQL-M1-01` | Migration 0001 sur base vierge + checksum |
| `SQL-M1-02` | Réouverture depuis nouveau process, IDs, versions, jalons et dépendances égaux |
| `SQL-M1-03` | Deux UoW, versions concurrentes, seconde mise à jour obsolète refusée |
| `SQL-M1-04` | Graphe A->B puis B->A sous deux writers, aucun cycle confirmé |
| `SQL-M1-05` | Sans commit, exception et crash injecté, pas de persistance partielle |
| `SQL-M1-06` | FK, index, unicité et contraintes résistent aux entrées invalides |
| `SQL-M1-07` | Sauvegarde et restauration avec validation d'intégrité |
| `SQL-M1-08` | Migration de schéma non idempotente ou checksum modifié détecté |
| `SQL-M1-09` | Date/timezone, version et JSON invalides rejetés sans mutation |
| `SQL-M1-10` | Contrats communs M0/InMemory/SQLite réussis sur SHA exact |

L'absence d'exécution des tests signifie **NOT_TESTED**, pas `PASS`. Le choix d'un schéma SQL ne qualifie pas un adapter.

## 7. Impact et compatibilité

Tout changement de protocole des ports M0 nécessite un contrat de migration et des tests ; `ProjectRegistryEntry` demeure une projection, pas la source transactionnelle `Project`. Les modèles M1 de preuves et de snapshots ne sont pas insérés artificiellement dans les Aggregate Roots M0.

**Décision : ACCEPTED_FOR_M1_LOCAL_PILOT**, à réévaluer avant stockage partagé, données réelles ou publication.
