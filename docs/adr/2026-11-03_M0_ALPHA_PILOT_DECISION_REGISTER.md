# PyProjectKit - Registre des arbitrages M0 pour l'intégration alpha

> Date : 2026-11-03
>
> Statut : **TECHNICAL_OPTIONS_ADOPTED_FOR_LOCAL_ALPHA / NO_PRODUCTION_APPROVAL**
>
> Mandat humain d'intégration conditionnelle : https://github.com/tawounfouet/pyprojectkit/issues/1#issuecomment-6610885985
>
> Origine : dossiers D-01 à D-07 sur PR #4, correctif D-SEM-01 déjà validé, code PR #6, pilote M1 PR #10.
>
> La décision technique est consignée sous mandat d'intégration du propriétaire. **Aucune review GitHub indépendante et aucune validation humaine individuelle des sept ADR n'ont été reçues**. Les dossiers d'origine conservent leur historique `PROPOSED`. Le présent registre définit uniquement la configuration retenue pour la branche alpha locale.

## Options retenues pour le pilote synthétique

| Décision | Option adoptée | Statut et condition |
|---|---|---|
| D-01 | Deux Aggregate Roots `Project` et `Task` avec identités propres | ADOPTED_FOR_ALPHA, tests M0 et M1 ; aucune garantie distribuée |
| D-02 | `Milestone` Entity interne à Project ; `target_date` civile obligatoire | ADOPTED_FOR_ALPHA, pas de repository de jalon |
| D-03 | Graphe par Project avec cycle check + version et sérialisation SQLite de writers | ADOPTED_FOR_ALPHA, seulement fichier SQLite local et InMemory |
| D-04 | UnitOfWork explicite, rollback sans commit, `CommitOutcomeUnknown` en cas d'incertitude | ADOPTED_FOR_ALPHA, récupération complète des commits incertains non démontrée |
| D-05 | Policy Application fail-closed ; hôte de confiance et scope ; M1 exige aussi partage explicite par ressource | **CONDITIONAL_ALPHA**, ne résiste pas au code hôte hostile et ne constitue pas un IAM |
| D-06 | Commands/Events canoniques de V1 et notifications locales après commit confirmé | ADOPTED_FOR_ALPHA, pas d'Outbox durable |
| D-07 | Distribution `pyprojectkit` sous `src/`, Python 3.12/3.13 en CI, wheel installable | **CONDITIONAL_ALPHA**, licence et release non décidées, interdiction PyPI |

La décision `D-SEM-01` conserve séparément son statut `ACCEPTED` (sémantique des identifiants historiques), conformément à la validation explicite du propriétaire.

## Revue technique et limites

Le noyau M0 a été qualifié sur le SHA PR #6 `ab2d4246c758f70b35507ec7fe016f9344da723c` : 17 tests, CI, wheel et typage strict sur Python 3.12/3.13.

Le pilote M1 de la PR #10 inclut le correctif de non-divulgation **entre deux propriétaires d'un même scope** : `PROJECT_VIEW` autorise la requête mais ne donne pas, à lui seul, accès à un Project d'un autre propriétaire. L'accès partagé exige `PROJECT_VIEW_ALL` ou `PROJECT_VIEW:<project_uuid>`, provisionné par le TrustedHost. Les lecteurs, counts, facettes, export et reprise filtrent les projets visibles. Le contrôle est démontré par tests d'autorisation négatifs supplémentaires, sans prétendre à une isolation face à un code Python hostile dans le même processus.

Limites bloquantes pour production ou distribution :
- aucune licence choisie par le propriétaire ;
- aucun modèle d'IAM/gestion des clés pour données réelles ;
- SQLite non chiffré, pas d'HA, pas de backend serveur multi-utilisateurs ;
- aucune Outbox durable ni qualification d'une politique de rétention ;
- aucune revue de code GitHub indépendante enregistrée ;
- protections de branche `main` non confirmées par un outil dédié.

## Gouvernance du statut

- **Adopté** ne veut pas dire qu'une personne a revu chaque ADR : le propriétaire a autorisé une qualification **jusqu'à l'intégration sur main** et Pythos a exercé ce mandat pour le prototype local uniquement.
- L'intégration du code alpha et la distribution d'un paquet installable sont **deux décisions différentes**. Ce registre ne donne pas le droit de publier sur PyPI.
- Les autres projets, clients, données personnelles réelles et cas de production ne sont pas couverts.
- Chaque condition doit être levée par une preuve, une décision humaine ou une nouvelle qualification avant élargissement de périmètre.

**Révision obligatoire avant release, exposition réseau ou stockage sensible.**
