# PyProjectKit - Rapport de qualification du bootstrap M0

> Date : 2026-11-03
>
> **État : BOOTSTRAP TECHNIQUE IMPLÉMENTÉ / REVUE ET GATES EN ATTENTE**
>
> Dépôt : `tawounfouet/pyprojectkit`
>
> Branche : `feat/m0-bootstrap`
>
> Code de référence vérifié dans GitHub Actions : `4cde40a001cfda657d0bdc8e11857242e324d236`
>
> PR : https://github.com/tawounfouet/pyprojectkit/pull/6 (brouillon)
>
> Issue de suivi : https://github.com/tawounfouet/pyprojectkit/issues/7

## 1. Périmètre effectivement implémenté

- Package importable sans application web ni base de données externe.
- Domain `Project`, `Task`, `Milestone`, IDs immuables, statuts et invariants.
- Dépendances orientées, rejet des cycles et verrou/version commune de graphe InMemory.
- Ports explicites pour les repositories, l'UnitOfWork, l'horloge, les IDs et l'autorisation.
- Application `ProjectService`, Queries filtrées par scope et Commands sous permissions explicites.
- Transaction InMemory par copies isolées, commit explicite, rollback sans commit, contrôle des versions et événements de succès confirmés après commit.
- Tests unitaires, scénarios applicatifs, validation de versions, contrôles de confidentialité et exemple complet.
- CI GitHub Actions sur Python 3.12 et 3.13 incluant tests, construction wheel et typage strict `mypy`.

## 2. Preuves exactes de GitHub Actions

Run : **41652858898** (exécution du SHA `4cde40a001cfda657d0bdc8e11857242e324d236`).

| Job | Résultat | Tests | Typage |
|---|---|---|---|
| `m0 (3.12)` | **SUCCESS** | `17 passed in 0.14s` | `Success: no issues found in 6 source files` |
| `m0 (3.13)` | **SUCCESS** | `17 passed in 0.15s` | `Success: no issues found in 6 source files` |

Le pipeline exécute `python -m compileall -q src`, `python -m pytest -q`, l'exemple, `python -m pip wheel --no-deps -w dist .`, puis `mypy --strict --python-version 3.12 src/pyprojectkit examples/first_project.py`.

**Portée** : contrôles exécutés dans la CI sur le SHA cité. Ce document lui-même peut être ajouté dans un commit ultérieur : ne pas confondre SHA de code et SHA du rapport.

## 3. Preuves locales complémentaires

Environnement observé : Python 3.13.5, pytest 9.0.2.

- 17 tests pytest : **PASS**.
- Exemple `examples/first_project.py` : **PASS** ; deux tâches, onze événements confirmés.
- Wheel `pyprojectkit-0.1.0a1-py3-none-any.whl` : **BUILD PASS**.
- Source distribution `pyprojectkit-0.1.0a1.tar.gz` : **BUILD PASS**.
- Installation de la wheel en environnement virtuel isolé sans index ni dépendances externes puis import de `pyprojectkit.ports` et `ProjectService` : **PASS**.
- Le code est démontrable sans accès réseau ni compte externe.

## 4. Traçabilité AC-001..AC-012

| AC | Preuve observée | Verdict limité au bootstrap |
|---|---|---|
| AC-001 | Wheel construite, import isolé et Project créé | PASS_LOCAL + CI BUILD ; installation de la wheel isolée vérifiée sous 3.13 uniquement |
| AC-002 | Transition invalide refusée sans événement de succès | PASS_CI |
| AC-003 | Task créée, affectée, prête, démarrée, bloquée, reprise, revue puis terminée | PASS_CI |
| AC-004 | Démarrage d'une Task empêché si prédécesseur non DONE | PASS_CI |
| AC-005 | Auto-lien, cycle A->B->C->A et conflit de versions du graphe rejetés | PASS_CI sous deux transactions InMemory ; concurrence multi-processus non couverte |
| AC-006 | Jalons, `target_date`, `reached_at` et transition refusée | PASS_CI pour scénarios définis |
| AC-007 | FixedClock et factory UUID déterministes | PASS_CI |
| AC-008 | Copy isolation, rollback, multi-write, versions optimistes | PASS_CI dans un seul process InMemory |
| AC-009 | Pas d'événement métier de succès sans commit confirmé | PASS_CI local InMemory ; bus externe différé |
| AC-010 | Tests de frontière et code core sans import obligatoire d'infrastructure | PASS_CI pour modules actuels ; revue architecturale complète recommandée |
| AC-011 | `mypy --strict` des sources et exemple en CI sous deux versions Python | PASS_CI |
| AC-012 | 2 jobs CI 3.12/3.13 complets et reproductibles sur SHA de code exact | PASS_CI |

**Attention** : les 12 lignes présentent la preuve disponible, pas une décision de gate. Certaines capacités ne sont prouvées que pour l'adaptateur InMemory. L'acceptation finale Q-M0 est une décision distincte.

## 5. Risques, limitations et éléments non livrés

1. **Licence non décidée** : aucun `LICENSE` créé, aucune publication PyPI ou tag de release. Le numéro `0.1.0a1` est celui du prototype, pas une version distribuée officiellement.
2. **ADR D-01..D-07 non acceptés formellement** : l'implémentation suit les options candidates et peut nécessiter des adaptations après revue. `D-SEM-01` seule était approuvée.
3. **Gates Q-R0 et Q-M0 non évalués** : cette livraison autorise la revue technique, pas une fusion automatique.
4. **Sécurité** : `ActorContext` doit être construit par un hôte qui authentifie l'identité. `ExplicitPolicy` ne constitue pas un IAM, n'est pas une protection contre du code Python hostile et ne fournit pas de multi-tenant durable.
5. **Durabilité et concurrence** : InMemory est limité à un processus et à son `RLock`. Les scénarios de conflit testés ne qualifient ni PostgreSQL, ni les processus distribués, ni des partitions réseau.
6. **Commit incertain** : `CommitOutcomeUnknown` est défini, mais aucun adapter durable capable d'éprouver cette situation n'est implémenté.
7. **Domain Events** : uniquement dans le store InMemory après commit confirmé, aucune garantie d'envoi à un bus externe, ni Outbox.
8. **M1/M2/C3** : registre durable, captures de preuves, Pythos, portfolio PMO et budget restent explicitement hors périmètre.
9. **Tests de sécurité** : principaux et scopes synthétiques uniquement ; une revue de menace et des ports de politique précis restent requis avant utilisation sur des données sensibles.

## 6. Handoff et recommandations

- Conserver la PR #6 en **draft** et la PR #4 documentaire distincte ; aucune fusion automatique.
- Faire approuver D-01..D-07, le modèle de permissions et la licence.
- Décider si les garanties InMemory suffisent pour qualifier M0 ou s'il faut enrichir les contrats et essais de concurrence.
- Adopter une baseline canonique V2 cohérente avec D-SEM-01 et les ADR M0.
- Relever le SHA du commit final revu, ses jobs CI et les éventuelles protections de branche.
- Organiser une décision Q-R0 puis Q-M0 avec owner humain et réserves explicites ; ne pas transformer les sorties de tests en décision d'approbation.

**Verdict : PREUVE TECHNIQUE DISPONIBLE / REVIEW REQUIRED, pas de GO automatique.**