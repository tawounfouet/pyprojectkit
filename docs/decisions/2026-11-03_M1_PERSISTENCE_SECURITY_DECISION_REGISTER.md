# PyProjectKit - Décisions M1 de persistance et sécurité

> Date : 2026-11-03 | Type : compte rendu d'arbitrage technique délégué
>
> Statut global : **M1_LOCAL_PILOT_ARCHITECTURE_APPROVED / IMPLEMENTATION_NOT_STARTED**
>
> Source du mandat : https://github.com/tawounfouet/pyprojectkit/issues/8#issuecomment-6607173475
>
> Les choix sont acceptés **pour le pilote local hors données sensibles**, pas pour un déploiement multi-tenant, une publication ou un verdict de gate.

## 1. Synthèse des décisions effectivement arrêtées

| Identifiant | Choix arrêté | Statut | Condition de preuve |
|---|---|---|---|
| [ADR-M1-01](../adr/m1/ADR-M1-01_SQLITE_DURABLE_STORE.md) | `sqlite3` pour premier store durable local, port substituable | ACCEPTED_FOR_M1_LOCAL_PILOT | Multi-process restart, CAS graph/AR, tests rollback |
| [ADR-M1-02](../adr/m1/ADR-M1-02_SCHEMA_MIGRATION_AND_UOW.md) | Schéma versionné, migrations checksummées, FK/UUID, UoW commune | ACCEPTED_FOR_M1_LOCAL_PILOT | Suite SQLite/InMemory, intégrité, backup/restore |
| [ADR-M1-03](../adr/m1/ADR-M1-03_CONTEXT_SCOPE_AND_AUTHORIZATION.md) | Principal fourni par hôte fiable, `ScopeId`, policy scoped fail-closed | ACCEPTED_FOR_M1_LOCAL_PILOT | Refus 2 scopes/2 acteurs, pas de fuite pages/counts/logs |
| [QUAL-M0-TECH-01](../qualification/2026-11-03_M0_TECHNICAL_QUALIFICATION_CONSOLIDATION.md) | Code M0 InMemory utilisable comme référence de tests M1 | TECHNICAL_SCOPE_VERIFIED | 17 tests + mypy/CI sur SHA exact |

## 2. Portée de la délégation

Le propriétaire du projet a autorisé Pythos à **prendre les décisions de cadrage** relatives à la consolidation M0 et aux choix de persistance et de sécurité M1. Ce mandat est consigné dans l'issue M1 #8. Cette trace ne prétend pas qu'il a examiné chaque ligne SQL, policy ou test.

**Autorisés** : définition du contrat local, préparation des migrations et tests, fixtures synthétiques, préparation de l'issue du premier vertical slice.

**Non autorisés** : ingestion de données réelles, service multi-utilisateurs exposé, choix de chiffrement déduit sans modèle de menace, release du package, fusion sur `main`, GO de `Q-R0/Q-M0/Q-M1`.

## 3. Recommandations de priorité pour VS-M1-01

1. Figé comme cible : `SQLite + migrator 0001 + ContextScope` derrière les ports et sans casser le M0 InMemory.
2. **Tests sécurité d'abord** : acteur non vérifié refusé ; une ressource d'un autre scope est invisible, y compris via nombres et pagination.
3. **Tests UoW** : état persistant après restart dans un nouveau processus, cohérence Project/Task/Graph, rollback et conflit de version.
4. **Tests migrations** : schéma ancien, modification de checksum, sauvegarde/restauration, corruption/schéma incompatible en erreur contrôlée.
5. **Tests de concurrence** : deux processus sur même fichier, accès à la version commune du graphe et impossibilité d'un cycle après commit.
6. **Evidence** : SHA, versions SQLite/Python, migration appliquée, journal de tests et limites, sans secret ni données privées.
7. Ne commencer M1-B (observations/preuves) que lorsque le **VS-M1-01** remplit sa DoD définie et qu'un mandat de développement a été donné.

## 4. Différences à protéger

- `Project` (Aggregate Root) n'est pas `ProjectRegistryEntry` (projection).
- `ProjectStatus.ON_HOLD` n'est pas une décision portefeuille `PARK`.
- `Task.DONE` n'est pas `VerificationAssessment.VERIFIED`.
- Une preuve externe inconnue / cassée ne devient jamais `PASS`.
- `ActorContext(scope: str)` historique n'est pas en soi une preuve d'autorisation.
- Une CI M0 verte ne prouve ni SQLite ni `Q-M1`.

## 5. Points ouverts avant début de la réalisation M1

| Sujet | État |
|---|---|
| Source M0 sur `main` | PR #6 encore en brouillon |
| Spécifications et ADR M0 D-01..D-07 | En revue sur PR #4/#5 |
| Licence et politique de diffusion | Non arbitrées |
| Protection effective de `main` | Non vérifiée |
| Contrat exact `VerifiedActorContext`/permissions M1 | À stabiliser dans M1-04 |
| Chiffrement et durée de conservation de données réelles | Non autorisés, à décider avant données réelles |
| Q-R0, Q-M0, Q-M1 | NOT_ASSESSED |
| M1 code/test/CI | NOT_STARTED |

## 6. Décision finale de ce dossier

**GO de cadrage technique M1-A pour un pilote local sur données synthétiques.** Ce `GO_DE_CADRAGE` n'est **pas** le gate `Q-M0` ni une autorisation de déploiement ou de démarrage automatique du code M1. Les trois ADR sont acceptés sous mandat de décision déléguée pour cette portée uniquement.
