# ARCH-03/04/05 - Inventaire des 28 sous-WorkItems du plan

> États techniques du périmètre additif, **pas** décisions de gates. Aucun `TECHNICAL_DONE` n'est un avis humain indépendant.

| WorkItem | Statut | Motif |
|---|---|---|
| `A03-01` | `PARTIAL` | baseline Git figée, G1 non prouvé |
| `A03-02` | `TECHNICAL_DONE` | oracles M0 + scénarios |
| `A03-03` | `PARTIAL` | owner/scope démontrés, vraie AuthN non livrée |
| `A03-04` | `TECHNICAL_DONE` | PAR-06..09 classés DEFERRED |
| `A03-05` | `PREPARED` | frontières ProjectHub non implémentées |
| `A03-06` | `TECHNICAL_DONE` | fixtures synthétiques exécutables |
| `A03-07` | `TECHNICAL_DONE` | matrice API publique documentée |
| `A03-08` | `PREPARED` | revue technique Pythos non indépendante |
| `A04-01` | `PARTIAL` | branche VS01/PR historique existantes, pas de G1 rewrite |
| `A04-02` | `BLOCKED` | legacy non retiré car G1 absent |
| `A04-03` | `TECHNICAL_DONE` | package additif minimal |
| `A04-04` | `TECHNICAL_DONE` | wheel et Python 3.12/3.13 |
| `A04-05` | `TECHNICAL_DONE` | CI pytest et mypy strict |
| `A04-06` | `TECHNICAL_DONE` | fitness AST |
| `A04-07` | `PARTIAL` | README/compat mais pas version de release |
| `A04-08` | `PREPARED` | rapport technique sans revue humaine |
| `A05-01` | `TECHNICAL_DONE` | IDs, clock, erreurs |
| `A05-02` | `TECHNICAL_DONE` | Project et transitions |
| `A05-03` | `TECHNICAL_DONE` | Task, progression, affectation |
| `A05-04` | `TECHNICAL_DONE` | graphes et prérequis |
| `A05-05` | `TECHNICAL_DONE` | ports et UoW |
| `A05-06` | `TECHNICAL_DONE` | adapter InMemory + CAS |
| `A05-07` | `PARTIAL` | policy scoped, host AuthN absent |
| `A05-08` | `TECHNICAL_DONE` | Commands/Queries VS01 |
| `A05-09` | `PARTIAL` | événements après commit côté use cases, pas invariants d event port 1:1 |
| `A05-10` | `TECHNICAL_DONE` | tests RB et SEC et démo |
| `A05-11` | `TECHNICAL_DONE` | PAR statut truthful |
| `A05-12` | `PREPARED` | dossier G2 non signé |

- Les sous-WorkItems A04-01/02 ne sont pas équivalents au bootstrap **rewrite** prévu : la solution livrée est additive, et cela protège le legacy tant que l'archive G1 n'est pas faite.
- `TECHNICAL_DONE` = code ou contrat réellement existant, à confirmer en CI au nouveau SHA.
- `PREPARED` = livrable préparable/documentaire sans validation indépendante.
- `PARTIAL` = preuve partielle ou limite identifiée.
- `BLOCKED` = prérequis G1/autorité manquant.
- **Total : 28 WorkItems** (8 + 8 + 12).
