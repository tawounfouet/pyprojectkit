# R0-09 - Proposition du premier vertical slice M0

> Statut : **PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION**
>
> Sources : Roadmap 13 M0-01..18, Bootstrap 14 §§1, 10, 18, 24-25 et annexe D, exigences `AC-001..012`.
>
> Objectif : réduire la première démonstration à un scénario reproductible. Ceci n'autorise pas `BOOT-01` et n'est pas un ticket de développement commencé.

## Résultat observable minimal

Un environnement Python isolé et autorisé peut :

1. construire/importer la distribution `pyprojectkit` sans SQL, web ou Pythos ;
2. créer un Project sans Task puis deux Tasks sous son `ProjectId` ;
3. ajouter `Task B depends_on Task A`, sans cycle ;
4. refuser `Task A depends_on Task B` ; persistance du graphe antérieur intacte ;
5. ouvrir une UoW, ne pas appeler `commit()` et vérifier le rollback ;
6. provoquer une exception avant commit et vérifier aucun changement Project/Task ;
7. confirmer que `ProjectCreated` et `TaskDependencyAdded` n'ont été observés qu'après commit réussi ;
8. démontrer refus d'un accès non autorisé sur Project/Task et absence de fuite ;
9. lancer tests, typing, build, import smoke et rapport sur SHA exact.

**Hors portée** : ProjectRegistry durable M1, Observation/Evidence/Verification M1, OperatingBrief/ExecutionReport M2, PMO/Agile/Budget C3, Outbox externe, intégrations réelles clients ou employeurs, PyPI/release.

## Ordre d'exécution candidat

| Séquence | Résultat concret | Conditions |
|---|---|---|
| BOOT-01 | Package importable et distribution installable dans venv | D-07 validée, licence examinée |
| BOOT-02 | IDs typés, Clock déterministe, errors, séparation des couches | D-01/06/07 approuvées |
| BOOT-03 | `CreateProject`, `ProjectRepository` InMemory, cycle minimal | D-01/04/05 |
| BOOT-04 | `CreateTask` + Project visible, une Task sous un Project | D-01/05 |
| BOOT-05/06 | Jalon puis graphe validé sans cycle | D-02/03 |
| BOOT-07/08 | UoW partagée, optimistic concurrency, conflits | D-03/04 |
| BOOT-09 | Events internes après commit | D-06/04 |
| BOOT-10/11 | Tests AC et négatifs, rapport evidence et handoff | Les précédents |

## Conditions d'entrée formelles

- [ ] `Q-R0` donne explicitement `GO` ou `CONDITIONAL GO` valide.
- [ ] D-01..D-07 acceptés ou réserves non critiques définies avec owner et échéance.
- [ ] D-SEM-01 corrigée dans la baseline approuvée.
- [ ] Identité dépôt/branch/SHA, politique de visibilité et secrets confirmés.
- [ ] Matrice d'autorisations M0 finalisée.
- [ ] Une seule tranche M0 active à la fois, mandat humain et critères de rollback documentés.

## Scénarios Given / When / Then minimaux

```gherkin
Scenario: projet sans tâche
  Given un dépôt in-memory vide et un principal autorisé
  When CreateProject est committée
  Then le Project est lisible par son ProjectId
  And aucune Task n'est nécessaire pour sa création

Scenario: cycle de dépendances
  Given deux Tasks A et B du même Project
  And B dépend de A
  When AddTaskDependency demande que A dépende de B
  Then l'opération est rejetée avec erreur métier stable
  And le graphe persistant est inchangé
  And aucun événement de succès n'est diffusé

Scenario: mutation sans commit
  Given une UnitOfWork contenant une mutation
  When la UnitOfWork se ferme sans commit
  Then aucune mutation n'est visible depuis une nouvelle lecture

Scenario: refus de lecture
  Given une Task non visible par le principal
  When GetTask est exécutée
  Then aucune donnée ni indication sensible de son existence n'est divulguée
```

## Definition of Done du vertical slice (pas de Q-M0 raccourci)

- Test end-to-end du scénario de démonstration sur distribution installée.
- Révision du code sur SHA exact, import, typing, build et tests négatifs.
- Politique d'autorisation exécutée sous identités synthétiques.
- Aucun secret ni donnée réelle privée.
- Limites documentées : InMemory ≠ base durable, event local ≠ livraison distribuée.
- `AC-001..AC-012` restent à vérifier pour **Q-M0 complet**, même si la tranche de départ n'en couvre qu'un sous-ensemble.

## Délégation Pythos

Le mandat d'implémentation doit préciser branche, permissions d'écriture, état attendu, rollback, fichiers autorisés et exclusions. Le compagnon peut proposer le code et les tests, pas certifier seul un `GO` ou publier automatiquement.
