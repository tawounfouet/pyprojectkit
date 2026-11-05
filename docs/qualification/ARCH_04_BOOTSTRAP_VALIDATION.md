# ARCH-04 - Qualification du bootstrap expérimental

> Baseline observée avant changement : `dd8ec1c945ece80362f2c009ad56493fa855825f` | `main` contient `pyprojectkit` et `pyprojectkit_next` sans suppression du legacy.

| Critère | État technique au périmètre additif | Preuve / limite |
|---|---|---|
| `A04-AC-01` | `PARTIAL` | Branche initiale VS01, PR #22 fusionnée ; pas de branche rewrite après G1 |
| `A04-AC-02` | `PARTIAL` | Les fichiers legacy sont conservés. Aucune archive indépendante G1 ni branche ARCH-02 vérifiée |
| `A04-AC-03` | `PASS_SCOPED` | `pyprojectkit_next` n'importe pas Django, SQLite, PostgreSQL, runtime Pythos |
| `A04-AC-04` | `PASS_SCOPED` | Wheel isolée et import `pyprojectkit_next` dans la CI VS01 réussie sur baseline ; revérification exigée au nouveau HEAD |
| `A04-AC-05` | `PASS_SCOPED` | Nouveau test `test_arch04_domain_and_application_import_fitness` AST, interdiction de dépendance des couches coeur |
| `A04-AC-06` | `PASS_SCOPED` | Python 3.12/3.13, pytest, mypy strict au SHA GitHub final |
| `A04-AC-07` | `PARTIAL` | README + docs et matrice de compatibilité ; version de release et licence texte toujours non fixées |
| `A04-AC-08` | `PASS` | Rapports et documentation interdisent de déclarer parité M0/M1/M2 entière |

L'architecture est **Bootstrapped et testable** sous package additionnel, non une refonte ayant retiré le legacy. La qualification technique ne transforme pas automatiquement G1/G2 en décisions humaines.
