# M2-A - Guide du pilote Authorized Brief (VS-M2-01)

> Document d'implémentation, 4 novembre 2026
> Périmètre : M2-01 à M2-03, données synthétiques, aucune exécution Pythos
> Sources : `17_PYPROJECTKIT_M2A_IMPLEMENTATION_PLAN.md`, ADR-M2-01/02/05 (proposés)

## 1. Interfaces réalisées

- `pyprojectkit.m2.contracts`: `OperatingBriefDTO` v1.0, `WorkItemRef`, `ExactTargetReference`, `UnsupportedContractVersion`.
- `pyprojectkit.m2.mandates`: `DelegationMandate`, `MandateStorePort`, `InMemoryMandateStore`, `MandateVerifier`.
- `pyprojectkit.m2.application`: `BuildBriefRequest`, `BuildAuthorizedOperatingBrief`.
- `examples/m2_authorized_brief_demo.py`: parcours minimal reproductible.

Toutes les interfaces M2 sont facultatives. Le domaine M0 n'importe pas M2, Pythos, un SDK LLM ni un fournisseur IAM.

## 2. Séquence réelle

1. Un `TrustedHost` M1 authentifie un `VerifiedActor` pour un scope existant.
2. L'hôte provisionne un mandat local de démonstration, borné à un acteur, un délégué, un projet, un `TaskId`, un mode et une révision exacte.
3. `MandateVerifier` exige `BRIEF_BUILD`, `PROJECT_VIEW` et `TASK_VIEW`. Le destinataire configuré est `pythos`, jamais le texte de la Query.
4. `RegistryService.get_registry` et `list_tasks` appliquent leurs protections M1 (scope, propriétaire/partage et classification).
5. La Query sélectionne seulement les attributs de la tâche utile. Aucun historique, observation, contenu d'evidence, URI ou export M1 brut n'est repris.
6. L'état visible et le mandat sont relus avant restitution ; une révocation ou une modification concurrente observée échoue.
7. Le DTO versionné est validé et retourné au consommateur. Aucun outil n'est exécuté.

## 3. Contrat et limites

- `schema_version="1.0"`, dataclass immuable, JSON trié et encodage UTF-8.
- Versions/champs inconnus, dates naïves, clés dupliquées et valeurs incorrectes sont refusés.
- Limite de 16 384 octets, 32 éléments maximum par liste, champs texte bornés.
- La révision `GIT_COMMIT` requiert un SHA 40 caractères hexadécimaux. Sa présence dans GitHub n'est **pas** vérifiée par M2-A.
- Le brief expire au plus tard 20 minutes après sa création, sans dépasser le mandat.
- `allowed_actions` n'inclut que `PROJECT_VIEW` et `TASK_VIEW`; c'est une **description** de droits effectifs, non un jeton utilisable.
- Les niveaux `A4`/`A5` et toute mutation externe restent hors M2-A.
- Pour `AUDIT`, le niveau `A0` est obligatoire.

### Frontière de sécurité

`InMemoryMandateStore` doit être alimenté exclusivement par l'hôte de confiance. Le package n'isole pas du code Python hostile exécuté dans le même processus, ne chiffre pas SQLite et ne garantit ni la confidentialité de contenus arbitraires inscrits dans un titre de tâche ni une atomicité inter-systèmes. **Fixtures synthétiques uniquement**.

La revalidation préalable à la remise du brief ne se substitue pas à un contrôle au moment d'une action ultérieure. Un consommateur Pythos ne peut pas faire d'une copie de brief une capacité exécutable autonome.

## 4. Exemple

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/m2_authorized_brief_demo.py
python -m mypy --strict --python-version 3.12 src/pyprojectkit
python -m pip wheel --no-deps -w dist .
```

L'exemple met en place `TrustedHost`, un projet `PACKAGE`, une tâche M0 persistée, un mandat `AUDIT/A0`, puis produit un JSON de brief. Il ne lance aucun modèle ni commande externe.

## 5. Correspondance des critères

| AC | Couverture obtenue dans M2-A | Limite |
|---|---|---|
| AC-027 | Brief v1, mandat, projection M1, tests synthétiques | Adoption définitive et audit humain encore requis |
| AC-035 | Contrôle lecture cross-scope / cross-owner | Pas de validation globale des chemins M2-B/C |
| AC-031 | Aucune permission merge/publish/delete dans M2-A | Pas de preuve d'exécution Pythos distante |
| AC-032 | Refus de cible ou révision divergente | Pas de réception d'ExecutionReport |
| AC-030 | Query AUDIT pure en lecture | Pilote audit intégral reporté à M2-C |

## 6. Handoff vers M2-B

- **M2-04** : introduire le contrat `ExecutionReportDTO` sans transformer un résultat d'agent en fait métier.
- **M2-05** : concevoir l'inbox idempotente SQLite et ses migrations par ADR propre.
- **M2-06** : vérification indépendante de source et approbation humaine séparée.
- **M2-07** : crash/retry/reprise et non-double-compte.

`M2-A` ne crée pas de migration 0003, de statut agent ni de `WorkItem` Aggregate Root. Toute exploitation hors du pilote synthétique nécessite une qualification et un mandat distincts.
