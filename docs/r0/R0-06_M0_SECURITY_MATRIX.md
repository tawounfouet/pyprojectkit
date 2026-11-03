# R0-06 - Contrôles de sécurité minimaux pour M0

> Statut : PROPOSED / REVIEW | Owner de la politique : autorité humaine / hôte, à confirmer.
>
> Sources : 12 V2 §§4, 9-18, 22-35, 54 et 69 ; 08 V2 §§3, 9-12 ; 10 V2 §19 ; 07 V2 §9.

## Frontière de confiance

L'application hôte authentifie le principal ; PyProjectKit protège Commands/Queries via un contrat d'autorisation. Un `actor_id`, `scope` ou `mandate` fourni librement dans un payload ne suffit pas à prouver l'identité ou les permissions. Sans contexte fiable ou politique applicable, `DENY`.

M0 doit pouvoir s'exécuter sans moteur IAM, OAuth, PyAuthKit ou Pythos. Il ne promet pas l'isolation de processus contre du code Python hôte totalement fiable.

## Matrice d'accès minimale M0

| Opération | Ressource | Contrôle candidate obligatoire | Test négatif |
|---|---|---|---|
| `CreateProject` | scope de création | principal fiable + `PROJECT_CREATE` dans le scope autorisé | Actor inconnu / mauvais scope => aucun Project |
| `GetProject` / `ListProjects` | Project et liste | `PROJECT_VIEW`, filtrer avant retour/compte/pagination | Projet non visible ne fuite ni nom ni compteur |
| `PlanProject`, `StartProject`, `PutProjectOnHold`, `CompleteProject`, `CancelProject` | Project | permission d'action + membership/owner/context + expected version | Un rôle de lecteur ne change jamais statut |
| `CreateTask`, `GetTask`, `ListProjectTasks` | Task + Project parent | permission Task et droit de voir le Project parent | ID tâche deviné hors scope => réponse non révélatrice |
| `AssignTask`, `StartTask`, `CompleteTask` | Task | permission atomique + projet actuel + assignee/rôle si applicable + guards métier | Affecté sans droit => aucun changement |
| `AddTaskDependency` | Les deux Tasks + graphe de Project | droits des deux extrémités dans même projet/scope, invariant acyclique | Lien cross-scope => DENY sans révélation |
| `CreateMilestone`, `MarkMilestoneReached` | Project et Milestone enfant | droits Project/Milestone + statut/autorité valide | Jalon d'un projet tiers inaccessible |
| Événements et logs | Payload sortant | minimisation, filtrage et pas de secrets | Aucune donnée privée dans event, erreur ou trace |

Les noms de permissions atomiques exacts doivent être rapprochés de l'annexe A de 12 V2 et des commandes 08 V2. Cette matrice ne constitue pas une attribution de rôles opérationnelle.

## Règles de refus

1. `DENY` par défaut si sujet, permission, politique ou appartenance sont inconnus.
2. Une ressource invisible peut être représentée par `NOT_FOUND` ou un refus générique selon policy ; ne jamais révéler son existence par une erreur détaillée.
3. Les vues agrégées filtrent **avant** tout calcul.
4. Les exceptions et logs ne contiennent pas d'agrégats complets ni de secrets.
5. Un acteur ayant une Task assignée n'est pas automatiquement habilité à la lire ou à la muter.
6. Aucun report Pythos ne peut créer ou compléter une Task par simple déclaration.

## Points bloquants à décider avant code

- [ ] Contrat exact de `ActorContext` fourni par l'hôte et `AuthorizationPolicy.require(...)`.
- [ ] Permission stable pour ajout/suppression de dépendance, ou règle d'autorisation composée.
- [ ] Mode d'exécution de test avec policy explicite, sans bypass silencieux.
- [ ] Distinction `NOT_FOUND` / `PERMISSION_DENIED` et absence de divulgation.
- [ ] Cas de refus de lecture et écriture sous deux scopes synthétiques.

## Traçabilité

À ajouter au plan M0 : `SEC-M0-01` identité inconnue, `SEC-M0-02` refus query, `SEC-M0-03` refus command, `SEC-M0-04` dépendances cross-scope, `SEC-M0-05` non-divulgation, `SEC-M0-06` logs sans secrets. Ce sont des **IDs locaux de tests candidats**, non de nouveaux AC normatifs.
