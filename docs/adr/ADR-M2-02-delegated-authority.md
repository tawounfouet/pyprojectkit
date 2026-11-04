# ADR-M2-02 - Autorité de mandat et vérification M2-A

- Date : 2026-11-04
- Statut : PROPOSED / revue humaine requise
- Tranche : M2-A, M2-03

## Problème
Un payload d'agent ne peut définir son acteur, son scope, ses permissions ou la validité d'un mandat.

## Décision candidate
- L'instance `TrustedHost` M1 reste la racine d'identité des lecteurs et du vérificateur M2.
- Provisionnement hors payload via `MandateStorePort` ; `InMemoryMandateStore` uniquement pour fixtures locales de confiance.
- Contrôle `BRIEF_BUILD` explicite, puis intersection avec `PROJECT_VIEW` et `TASK_VIEW`.
- Délégué fixe `pythos` défini par l'hôte, pas par la Query.
- Comparaison stricte acteur, scope, projet, travail, mode et référence cible.
- `AUDIT` ne fonctionne qu'en `A0`; A4/A5 rejetés, aucun droit de mutation présent dans M2-A.
- Expiration, suspension, révocation ; relecture autoritative avant retour du DTO.
- Réévaluation des permissions M1 et de la visibilité à la fin de la projection.
- Tout échec de source de mandat est refusé `fail closed`.

## Alternatives
- Signature ou JWT maison : refusé, le pilote n'a pas besoin d'un nouvel IAM.
- Identité dans la demande de brief : rejetée.
- Autorisation par seul `authority_level` : rejetée.

## Limites
`TrustedHost` M1 ne fournit pas de révocation globale de session par l'application ; M2-A revalide les permissions effectivement émises. Pas de garantie d'atomicité avec un acteur externe après remise, ni d'isolation face au code Python hostile dans le même processus. Le consommateur doit contrôler de nouveau l'autorité au moment de toute action future.

## Preuves exigées
Tests forgery, cross-scope, other-owner, révocation en lecture, source indisponible, contexte expiré, aucune mutation.
