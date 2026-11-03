# D-05 - Autorisation applicative minimale et isolation M0

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-10`, `SEC-ADR-V2-001..004`, `SEC-ADR-V2-013`, `ADR-PJ-10-13`.
>
> Portée : M0 uniquement ; le modèle de `ContextScope` multi-contextes complet appartient à M1.

## Problème

Un moteur Python headless peut être consommé directement depuis un CLI, un service ou un notebook. Un contrôle situé uniquement dans une API HTTP ne protège pas les autres points d'entrée. Les Queries et les Readers peuvent divulguer l'existence d'un Project ou d'une Task même sans mutation.

## Alternatives

**A - RECOMMANDEE :** l'hôte authentifie le principal ; une frontière de composition construit un `ActorContext` / `AuthorizationContext` fiable. L'Application exige une `AuthorizationPolicy` injectable avant les Commands et Queries protégées et refuse par défaut toute décision absente ou indéterminée.

**B :** contrôle limité à FastAPI/Django ; le core suppose les appels fiables. Inacceptable pour des consommateurs embarqués et pour la prévention des accès cross-scope.

**C :** construire un IAM complet dans PyProjectKit M0. Hors périmètre, introduirait une dépendance injustifiée à PyAuthKit ou à un fournisseur.

## Règles candidates

- Les attributs de confiance (`actor_id`, permissions, scope, mandat) ne sont pas autorisés simplement parce qu'ils apparaissent dans le payload client.
- `DENY` si identité inconnue, policy absente, ressource hors scope, permission inconnue, mandat expiré ou évaluation impossible.
- `CreateProject` requiert `PROJECT_CREATE` sur le scope autorisé ; `StartProject` requiert `PROJECT_START`, `CompleteTask` `TASK_COMPLETE`.
- Les `GetProject`, `ListProjects`, `GetTask` et listes filtrent avant de retourner une ligne, un identifiant, un total ou un curseur.
- `AddTaskDependency` exige l'autorisation sur les deux Tasks et le Project ; `TASK_EDIT` est la permission **provisoire** du document 12, tandis que `DEPENDENCY_CREATE` reste à arbitrer.
- Refus public `NOT_FOUND` ou réponse générique non-divulgante selon policy ; journal interne minimal, non public, et sans secrets.
- Une affectation `Task.assignee` n'est **pas** une autorisation implicite.
- L'implémentation InMemory ne peut pas contourner des contrôles que la variante SQL appliquerait.

## Preuves d'autorisation futures

`SEC-M0-01` : principal non vérifié => DENY.

`SEC-M0-02` : Get/List hors scope => aucun résultat, compte ou identifiant sensible.

`SEC-M0-03` : Command interdite => aucun effet ni Domain Event de succès.

`SEC-M0-04` : dépendance impliquant une Task cross-scope => refus non-divulgant.

`SEC-M0-05` : ressource invisible => pas de fuite via les erreurs/pagination.

`SEC-M0-06` : logs/événements => redaction des champs privés.

## Points de décision réservés

1. API exacte `AuthorizationPolicy.evaluate(request)` et DTO fiable construit par l'hôte.
2. Table atomique des permissions M0, notamment dépendances.
3. Politique de non-divulgation : `PERMISSION_DENIED` vs `NOT_FOUND`.
4. Adaptateur de test explicitement autorisé ou non, jamais un allow-all silencieux.
5. Modèle de scope M0 sans imposer dès maintenant la gouvernance multi-tenant M1.

## Sources

`12 V2 §§4, 7, 12-20, 54, 66-68`; `08 V2 §§6-7`; `10 V2 §41`; `11 V2 §57`; `R0-06_M0_SECURITY_MATRIX.md`.

## Décision

**Option A recommandée ; PROPOSED.** Revue humaine nécessaire pour les droits et le comportement de refus. Aucun contrôle de sécurité exécuté sur un package M0.
