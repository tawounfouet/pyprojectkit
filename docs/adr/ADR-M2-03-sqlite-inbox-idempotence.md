# ADR-M2-03 - Inbox SQLite, émision des briefs et idempotence M2-B

> Date : 2026-11-04
> Statut : **PROPOSED / validation humaine requise**
> Source : `19_PYPROJECTKIT_M2B_IMPLEMENTATION_PLAN.md`
> Tranche : M2-05 et M2-07, pilote synthétique local.

## Pression de conception
Un `brief_id` envoyé par un agent n'atteste pas son émission. Un retry, une défaillance avant ACK ou un arrêt peuvent produire des doublons et des historiques incohérents si inbox et M1 ont des commits différents.

## Décision proposée et implémentation candidate
- Ajouter une migration SQLite incrémentale `0003` dans l'adapter M1, sous checksum conservé pour les versions 0001/0002. Aucun ORM requis.
- `m2_issued_briefs` enregistre l'émission depuis l'hôte uniquement : référence exacte, `brief_id`, mandat, acteur, scope, projet, tâche, mode, watermark, empreinte, émission et expiration. L'ancien `BuildAuthorizedOperatingBrief` M2-A reste une Query non persistante.
- `m2_report_inbox` contient un rapport à l'état **ACCEPTED_AS_DECLARATION**, versionné et borné, avec clé `(scope_id,mandate_id,report_id)` et clé de retry indépendante `(scope_id,mandate_id,idempotency_key)`. `fingerprint = SHA-256` des octets JSON canoniques du DTO.
- `m2_report_links` relie chaque ingestion à `history` M1 ; `HistoryRecord` observation, références d'evidence non vérifiées et handoff sont enregistrés sous le même `SqliteUnitOfWork` et dans la même connexion.
- DDL de lecture seule via triggers `UPDATE/DELETE` interdits pour receipts, inbox, liens et évaluations ; corrections par nouvel append uniquement.
- `BEGIN IMMEDIATE`, contraintes `UNIQUE`, FKs et `DEFERRABLE INITIALLY DEFERRED` constituent les mécanismes locaux testables. L'UoW couvre **SQLite seulement**, jamais GitHub/LLM.
- Collision d'identifiant ou de clé avec fingerprint distinct, ou identité/clé contradictoire : `IdempotencyConflict`. Retry identique et actuellement autorisé : même `ingestion_id`, aucun nouveau lien.
- `CommitOutcomeUnknown` n'est ni succès ni rollback présumé. `reconcile()` vérifie sous autorisation actuelle si un reçu a été durablement écrit avant un nouveau retry.
- Après redémarrage, les mandats volatiles M2-A doivent être **reprovisionnés par l'hôte** : jamais reconstruits depuis le rapport.
- `PRIVATE` explicitement hors du chemin de délégation; données réelles exclues en SQLite non chiffrée.

## Alternatives rejetées à ce stade
- Écrire successivement inbox + `RegistryService.observe` + `record_handoff` dans des transactions séparées : refus d'atomicité.
- Déduplication `set()` en mémoire, `last-write-wins`, ou déduire un succès d'un ACK réseau : garanties insuffisantes.
- Outbox distribuée/Redis/Kafka, IAM autonome, Event Sourcing : sans pression démontrée.

## Limites et tests de conformité
- Historique append-only local, pas un événement d'intégration livré et pas une garantie `exactly-once` distante.
- Aucun chiffrement SQLite, aucune purge rétention de données réelles, ni signature cryptographique de producteurs.
- Tests : replay, collision report/key, threads, crash injecté, ACK perdu après commit, récupération par autre processus et backup, rejet de mandat périmé, impact nul sur Project/Task.

## Arbitrage humain
Revue des index, classes de données et conditions de conservation avant usage non synthétique. **Proposed != approved**.
