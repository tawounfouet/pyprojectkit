# ARCH-06 - Rapport de caractérisation Memory avant SQLite

> État candidat : `A06-01/A06-02_PREPARED / MEMORY_TESTS_LOCAL_PASS / CI_PENDING`.
> Date : 6 novembre 2026.

## Périmètre exécuté

- 12 tests ciblés dans `tests/test_arch06_memory_characterization.py`.
- Atomicité de changements `Project` + `Task` et abandon sans commit.
- Concurrence CAS globale InMemory, protection contre écrasement silencieux.
- Deux ordres de course fermeture de projet/création de tâche, sans enfant fantôme.
- Graphe de dépendances (cycle et dépendance inter-projets).
- Publication locale d'événements seulement après commit, refus du double commit et de l'événement sans mutation.
- Isolation des snapshots et stabilité des résultats autorisés lorsqu'apparaissent des objets cachés.

Les tests sont exécutables sans SQLite, Django, ProjectHub ni données réelles. Le compte final et le HEAD GitHub doivent être actualisés après CI ; ne pas transférer le nombre de tests locaux sur un SHA différent.

## Non-objectifs et réserves

- Aucun fichier SQLite créé et aucune migration SQL exécutée.
- Aucun crash-process/restart durable, multiprocess concurrency, backup/restore, migration checksummée ou commit ambigu qualifié.
- `list_projects` ne constitue pas un contrat de `RegistryReader` avec count/facet/page ; ces surfaces futures ne sont pas encore couvertes.
- `ActorContext` n'authentifie pas l'acteur : il doit être construit par un hôte de confiance.
- Il manque `G1`, `G2`, décision de persistence ADR, revue indépendante et protection effective de `main`.

**Verdict technique : `MEMORY_CHARACTERIZED`, `ARCH06_SQLITE_NOT_STARTED`, `G3=PENDING`.**
