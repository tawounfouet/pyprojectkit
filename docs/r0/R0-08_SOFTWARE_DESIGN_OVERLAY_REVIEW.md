# R0-08 - Revue de l'overlay Software Design & Learning

> Date : 2026-11-03
>
> Statut : REVIEW_COMPLETE_FOR_M0_SCOPE / ADOPTION_PENDING
>
> Sources : `PYPROJECTKIT_SOFTWARE_DESIGN_LEARNING_OVERLAY.md` §§22-27, `PYKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md` §§26, 29, 36-45, specs PyProjectKit 00/04..12 V2, dossier D-01..D-07.

## Constat principal

La convention commune insiste sur : **nom du concept métier avant pattern**, DDD et SoC lorsque justifiés, alternatives simples, tests comme preuves, distinction entre architecture proposée et code exécuté. L'overlay PyProjectKit §24.2 exige explicitement M0 : Project/Task cohérents, dépendances acycliques avec concurrence, Repository/UoW testés, Domain Events et erreurs, CI et un consommateur réel.

Ces critères **convergent** avec les sept arbitrages candidats D-01..D-07 ; l'overlay n'autorise aucun nouveau type d'agrégat ni la publication d'un package sans preuve.

## Crosswalk vers les ADR candidats de l'overlay

| Ancien identifiant overlay | Sens | Dossier de décision actuellement propriétaire | Résolution à ce stade |
|---|---|---|---|
| `PJ-OVL-ADR-001` | Task séparée de Project | D-01 | OPTION A PROPOSED |
| `PJ-OVL-ADR-002` | Milestone interne à Project | D-02 | OPTION A PROPOSED |
| `PJ-OVL-ADR-003` | Persistance des dépendances | D-03 | OPTION A PROPOSED |
| `PJ-OVL-ADR-004` | ProjectRegistryEntry | M1 / ADR-PJ-RM-07 | DEFERRED |
| `PJ-OVL-ADR-005` | Snapshot/Event Sourcing | M1 / ADR-PJ-RM-09 | DEFERRED |
| `PJ-OVL-ADR-006` | WorkItem classe mère ? | D-01 / D-06 | Ne pas imposer classe en M0 |
| `PJ-OVL-ADR-007` | Pythos optionnel | M2 / ADR-PJ-RM-11 | DEFERRED |
| `PJ-OVL-ADR-008` | Outbox | D-06 pour M0 ; M1/M2 si livraison fiable requise | Pas obligatoire en M0 |
| `PJ-OVL-ADR-009` | Project closure policy | D-01 | À définir par scope |
| `PJ-OVL-ADR-010` | Autorité d'approbation | D-05 et gouvernance R0 | Policy humaine distincte du test |
| `PJ-OVL-ADR-011` | Sources contradictoires | M1 / dossier de provenance | DEFERRED |
| `PJ-OVL-ADR-012` | Persistence M1 | M1 / ADR-PJ-RM-07 | DEFERRED |
| `PJ-OVL-ADR-013` | Scope vs Tenant | D-05 minimum M0 ; M1 approfondi | Contracter sans forcer SaaS |
| `PJ-OVL-ADR-014` | Cycle d'approbation | M1 / gouvernance | DEFERRED |

## Vérifications d'adéquation de la convention

- **SoC / DIP** : séparation Domain / Application / Ports / Adapters dans D-01, D-04, D-07 ; ports répondent à un use case, pas à un diagramme.
- **DDD** : deux Aggregate Roots ciblés, `Milestone` interne, `Dependency` Value Object, pas d'AR `WorkItem` universel.
- **Tests / evidence** : D-03 prévoit tests de cycle et concurrence ; D-04 commit/rollback ; D-05 autorisations et non-divulgation ; D-06 événements postcommit ; D-07 packaging + CI.
- **KISS / YAGNI** : pas de persistance durable M1, pas d'Event Sourcing/Outbox obligatoire, pas d'IAM intégré ni d'intégration Pythos exigée.
- **Gouvernance** : une décision `ACCEPTED` est un acte humain sourcé ; un test `PASS` concerne un code SHA exact, pas une simple spécification.
- **Apprentissage** : chaque dossier comporte problème, alternatives, compromis et scénarios à implémenter ; les noms de patterns ne remplacent pas les noms du domaine.

## Écarts et points d'attention

1. **R0-01** : absence de vérification locale, protections de `main` et visibilité des sources canoniques. Le dépôt est public ; ne pas charger de cas pilotes réels privés.
2. **D-03** : contrat de concurrence réellement testable pour `DependencyGraphPort`, non seulement un algorithme DFS.
3. **D-05** : permission `AddTaskDependency` encore provisoire et policy M0 à statuer.
4. **D-07** : licences et versions Python non décidées ; source 00 V2 et bootstrap 14 divergent sur le découpage physique.
5. **M1/M2** : éviter de faire glisser preuve, continuité et Pythos dans les objets M0.
6. **D-SEM-01** : décision de compatibilité documentaire acceptée, mais copie normative 07 V2 non encore fusionnée dans une baseline approuvée.

## Proposition de statut d'overlay

**`ADOPTED_WITH_PENDING_M0_ADR` (recommandation, NON DECIDEE)** : conserver la méthode de conception et les fitness functions, puis aligner l'overlay après décision humaine D-01..D-07. Le statut de la convention `ADOPTED / EXTENDED / DEVIATED / NOT_APPLICABLE` reste à prononcer par l'autorité du projet.

## DoD R0-08

- [x] Confronter les ADR candidats de l'overlay aux sept décisions M0.
- [x] Identifier les exigences de preuve et éviter les dédoublements.
- [x] Identifier les éléments M1/M2/C3 à ne pas faire entrer dans M0.
- [ ] Faire adopter la posture et les éventuelles déviations par le propriétaire humain.
- [ ] Propager les décisions retenues dans le document overlay canonique et la baseline.
- [ ] Référence et SHA approuvés ; `Q-R0` encore `NOT_ASSESSED`.

**Verdict : revue préparatoire M0 effectuée, adoption finale de l'overlay en attente.**
