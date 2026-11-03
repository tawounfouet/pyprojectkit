# R0-04 / R0-05 / R0-06 - Tableau de revue des sept décisions M0

> Date : 2026-11-03
>
> Statut : **READY_FOR_HUMAN_REVIEW / NOT_APPROVED**
>
> Autorité : propriétaire humain du projet. Une approbation doit référencer les IDs et les réserves ; un simple commit ou une PR en brouillon n'est pas un consentement d'architecture.

## Périmètre proposé, options et verdicts

| Décision | Dossier | Option recommandée | Vérification essentielle | Statut |
|---|---|---|---|---|
| D-01 | [Project/Task AR](../adr/proposals/D-01_PROJECT_TASK_AGGREGATE_BOUNDARIES.md) | Deux AR séparés avec coordination inter-AR | Créer Task dans Project valide, clôturer sous policy, pas de God Aggregate | PROPOSED |
| D-02 | [Milestone](../adr/proposals/D-02_MILESTONE_OWNERSHIP_AND_DATES.md) | Entity dans Project et `target_date` exigée | Date cible, `reached_at`, ProjectRepository, Projet sans jalon possible | PROPOSED |
| D-03 | [Graph concurrency](../adr/proposals/D-03_DEPENDENCY_GRAPH_CONCURRENCY.md) | Graph snapshot versionné, CAS/verrou par Project | Refus cycle et write skew sous deux transactions | PROPOSED |
| D-04 | [UnitOfWork](../adr/proposals/D-04_UNIT_OF_WORK_AND_FAILURE_SEMANTICS.md) | UoW locale explicite, rollback sans commit, issue inconnue distincte | Multi-repository atomique, aucun événement de succès sur échec | PROPOSED |
| D-05 | [Autorisation M0](../adr/proposals/D-05_APPLICATION_AUTHORIZATION_M0.md) | Policy injectée, hôte établit le principal, fail-closed | Commands **et** Queries, autorisation des deux Tasks d'une dépendance | PROPOSED |
| D-06 | [API et Events](../adr/proposals/D-06_PUBLIC_COMMANDS_AND_DOMAIN_EVENTS.md) | Command/Event canoniques V1 + dispatch local post-commit | Noms stables, succès uniquement après commit | PROPOSED |
| D-07 | [Packaging Python](../adr/proposals/D-07_PYTHON_PACKAGING_AND_COMPATIBILITY.md) | `src/` minimal, dépendances optionnelles, `>=3.12` candidat | Wheel/sdist installables, CI SHA exact, aucune licence inventée | PROPOSED |

**Décision déjà actée, hors des sept** : [D-SEM-01](../adr/D-SEM-01_V1_V2_RULE_IDENTIFIER_COMPATIBILITY.md), `ACCEPTED` le 2026-11-03, concerne la compatibilité des six IDs V1 et quatre nouvelles règles V2. Cette acceptation n'étend pas son autorité aux décisions ci-dessus.

## Trois réserves prioritaires à arbitrer explicitement

1. **D-03 / concurrence** : une implémentation InMemory séquentielle suffit à démontrer la règle de cycle, mais pas une garantie multi-writer. Décider la garantie M0 promise et la stratégie `compare-and-swap` / verrou. Rejeter tout faux PASS sous concurrence.
2. **D-05 / sécurité** : définir les permissions M0 exactes, en particulier `AddTaskDependency` (`TASK_EDIT` provisoire ou `DEPENDENCY_CREATE`) et le contrat de refus non-divulgant. Les guards ne peuvent pas être abandonnés à un adapter HTTP.
3. **D-07 / distribution** : `>=3.12` n'est pas une vérité mesurée ; choisir une matrice de support, la licence et la façade publique. Aucun `LICENSE` ni release implicites.

## Points de convergence documentés

- D-01, D-02, D-04 et D-06 reprennent des directions largement cohérentes V1/V2 ; **ceci ne vaut pas approbation**.
- D-03 et D-05 exigent des garanties de non-régression explicites avant code.
- D-07 doit trancher l'arborescence physique M0 (bootstrap 14) vs structure macro évolutive (vision 00). Le choix de l'architecture physique ne doit pas diluer les frontières du domaine.

## Revue et décision

Pour chaque D-XX, consigner :

| Champ | Format |
|---|---|
| Verdict humain | ACCEPT / REVISE / REJECT / DEFER |
| Option | A/B/C avec portée et exceptions |
| Owner | propriétaire humain ou délégataire explicitement habilité |
| Référence | URL du commentaire de décision ou compte rendu validé |
| Date | date UTC/CET précise |
| Conséquences | changements dans 00, 05 à 12, 13, 14 et tests |
| Preuves futures | tests à exécuter sur SHA de M0 |

Aucun statut `ACCEPTED` ne sera déduit d'une absence d'objection ou d'une revue documentaire seule. La validation des 7 décisions n'est **pas équivalente** au GO de `Q-R0`, qui exige aussi la baseline canonique et les autres critères.

## Suite attendue après approbation

1. Appliquer les décisions dans les spécifications V2 canoniques, harmoniser le glossaire et l'index ADR.
2. Réviser la matrice de tests, l'overlay d'apprentissage et la tranche verticale M0.
3. Réaliser la revue finale Q-R0 avec les preuves et réserves exactes, puis statuer `GO / CONDITIONAL GO / NO-GO`.
4. Seulement après autorisation : engager `BOOT-01` et ses contrôles d'installation.
