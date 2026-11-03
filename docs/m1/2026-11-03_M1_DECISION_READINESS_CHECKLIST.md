# M1 - Checklist de passage du cadrage vers VS-M1-01

> Statut : `DESIGN_READY_FOR_REVIEW / IMPLEMENTATION_NOT_STARTED`
>
> Références : [plan M1](../implementation/15_PYPROJECTKIT_M1_IMPLEMENTATION_PLAN.md), [registre de décisions](../decisions/2026-11-03_M1_PERSISTENCE_SECURITY_DECISION_REGISTER.md), [qualification M0](../qualification/2026-11-03_M0_TECHNICAL_QUALIFICATION_CONSOLIDATION.md).

## A. Éléments décidés

- [x] SQLite via `sqlite3` retenu pour le pilote local.
- [x] Repositories et UoW conservés derrière les ports existants.
- [x] Schéma/migrations versionnés avec checksums, UUID et FK explicites.
- [x] Graph et Aggregate optimistes sous transactions ; tests à deux processus exigés.
- [x] Principal fiable établi par hôte et `ContextScope` stable.
- [x] Deny-default par ressource, Queries filtrées avant agrégation.
- [x] Données synthétiques par défaut, aucune garantie de stockage sensible approuvée.

## B. Conditions de démarrage de code restant à satisfaire

- [ ] Enregistrer l'autorisation de réalisation explicite de `VS-M1-01` si elle est donnée ultérieurement.
- [ ] Fixer la référence du code de base pour la PR d'implémentation et la stratégie de non-régression M0.
- [ ] Examiner les conflits de D-01..D-07 non ratifiés avec les trois ADR M1.
- [ ] Vérifier les règles de protection de branche et les contraintes de visibilité d'une base locale.
- [ ] Choisir le contrat exact de `VerifiedActorContext`, permissions et politique `NotFound` non-divulgante.
- [ ] Valider les préconditions de licence/redistribution pour le package, sans publication.

## C. Scénarios Gherkin prioritaires

```gherkin
Scenario: reprise dans un second processus
  Given une base SQLite vide migrée et un acteur vérifié autorisé
  When le premier processus crée un Project et deux Tasks puis confirme la transaction
  And le processus s'arrête complètement
  Then un second processus peut relire le même Project, les Tasks et leurs versions
  And les permissions sont appliquées au nouveau contexte vérifié

Scenario: confinement entre scopes
  Given deux scopes S1 et S2 et un Project privé dans S2
  When un acteur de S1 interroge GetProject, ListProjects, counts et pagination
  Then aucune donnée ou statistique issue de S2 n'est révélée
  And un scope transmis par le payload ne confère aucun droit

Scenario: dépendances sous concurrence SQL
  Given deux Tasks A et B dans un Project
  When deux processus tentent simultanément A depends on B et B depends on A
  Then au plus un lien contradictoire est committé
  And aucun cycle n'est enregistré
  And un conflit cohérent est rapporté pour l'autre transaction

Scenario: rollback
  Given une UnitOfWork SQLite avec un changement Project et Task
  When le use case quitte sans commit
  Then aucune modification n'est visible après réouverture
```

## D. Conditions de preuve par tranche

| Tranche | Résultat vérifiable | Gate |
|---|---|---|
| VS-M1-01 | SQLite + scope + restart/process + rollback/concurrence | Preuves M1-A, pas Q-M1 |
| VS-M1-02 | Observations et Evidence immutables, refus faux PASS | AC-016..021 |
| VS-M1-03 | Snapshot/Handoff/NextAction sans mémoire de chat | AC-015/022 |
| VS-M1-04 | Cinq familles et portefeuille sécurisé | AC-013..026 + Q-M1 |

**Ni la rédaction de cette checklist ni les ADR ne constituent une exécution des tests.**
