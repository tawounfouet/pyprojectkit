# ADR-M1-03 - ContextScope, identité fiable et autorisation fail-closed

> Statut : **ACCEPTED_FOR_M1_LOCAL_PILOT** - décision technique déléguée, 2026-11-03
>
> Mandat : https://github.com/tawounfouet/pyprojectkit/issues/8#issuecomment-6607173475
>
> Sources : plan M1 section 5 et 12/16, spécification 12 V2, M0 `ports.ActorContext`, `service.ExplicitPolicy` et `ProjectService`.
>
> **Avertissement** : décision d'architecture de défense, non audit de sécurité ni attestation de protection effective.

## 1. Fait observé dans M0

M0 expose `ActorContext(actor_id: str, scope: str)` via `ports.py`. L'`ExplicitPolicy` démonstrative autorise les permissions selon `actor_id` et vérifie le `scope` dans les objets Project. Cette construction suppose que **l'hôte établit l'identité et la portée** : un client qui pourrait choisir arbitrairement son `ActorContext` serait susceptible d'usurper un autre scope. L'absence de fuite dans des tests synthétiques n'est donc pas une preuve de séparation multi-tenant.

M1 ajoute Registry, EvidenceRef, Observation, Assessment, Decision, Snapshot, Handoff et Portfolio. Les agrégats et projections doivent appliquer une autorisation au moins aussi forte que celle des Projects sous-jacents.

## 2. Alternatives

| Option | Évaluation | Choix |
|---|---|---|
| A. Principal vérifié par l'hôte + `ContextScope` typé + `AuthorizationPolicy` injectée et deny-default | Protège l'Application CLI/API/Notebook, sans imposer un fournisseur IAM | **RETENUE pour M1** |
| B. Vérifier uniquement au niveau HTTP ou CLI | Autres points d'entrée non protégés, Queries potentiellement révélatrices | Rejetée |
| C. Confiance dans un `scope` ou `actor_id` provenant du payload | Usurpation de scope triviale | Rejetée |
| D. Imposer PyAuthKit/IAM complet en M1 | Couplage inutile pour un pilote hors réseau ; future intégration possible via adapter | Différée |

## 3. Décisions de sécurité M1

**DEC-M1-SEC-01 - Principal fiable** : `ActorContext` M0 reste reconnu comme base de compatibilité, mais un `VerifiedActorContext` ou équivalent est construit par un **trusted host adapter** après authentification/validation hors payload. Les consommateurs ne doivent pas considérer un contexte librement construit par une entrée utilisateur comme une preuve d'identité. Toute Query et Command reçoit le contexte vérifié à la frontière Application.

**DEC-M1-SEC-02 - ScopeId canonique** : introduire `ScopeId` immuable et `ContextScope` persisté (owner, classification et policy ref), avec relation explicite entre Project et Scope. Ne pas traiter le paramètre CLI `--scope` ou une chaîne du client comme une habilitation.

**DEC-M1-SEC-03 - Autorisation objet/permission** : port `AuthorizationPolicy.require(subject, action, resource_ref, scope)` ou DTO équivalent. Une vérification globale `actor_id -> permission` seule est insuffisante. Guards sur les parents et sur les enfants à accès potentiellement plus restrictif. Au minimum :

| Ressource | Actions initiales à protéger |
|---|---|
| Project / Task / Milestone / Dependency | VIEW, CREATE, EDIT, COMPLETE, ASSIGN et mutation de lien |
| RegistryEntry / ExternalReference | READ, LINK, EDIT, LIST |
| Observation / Claim / EvidenceRef | READ, APPEND, VERIFY, LINK |
| VerificationAssessment / ReconciliationCase | READ, ASSESS, RESOLVE |
| Decision / Approval | READ, PROPOSE, APPROVE, REVOKE si applicable |
| Snapshot / Handoff / NextAction | READ, CAPTURE, EXPORT |
| Portfolio | LIST, COUNT, FILTER, EXPORT |

Le catalogue des codes publics devra être stabilisé lors de M1-04 ; ces noms d'action sont un **contrat d'intention**, pas une API Python déjà implémentée.

**DEC-M1-SEC-04 - Fail-closed et non-divulgation** : identité absente, scope inconnu, policy absente, permission indéterminée, échec d'évaluation ou ressource invisible => refus. Pour un objet caché, l'API publique doit utiliser une réponse non révélatrice (ex. `NotFound` générique) sans différencier absence réelle et interdiction par les détails, temps ou métadonnées accessibles.

**DEC-M1-SEC-05 - Filtrage avant agrégation** : Queries et Readers filtrent les ressources autorisées **avant** `COUNT`, facettes, tri, pagination, `total_pages`, suggestions, NextAction, snapshots et exports. Les liens vers des références externes héritent des permissions propres et du parent autorisé.

**DEC-M1-SEC-06 - Gouvernance des données** : fixtures entièrement synthétiques par défaut ; classification, rétention, suppression, backup/restore et export selon policy, sans contournement par des logs. Une base SQLite en clair sur disque n'est **pas validée** pour des données réelles sensibles en l'absence d'une politique explicite de chiffrement et de gestion des accès/clefs.

## 4. Stratégie de compatibilité avec M0

1. Conserver les signatures Python publiques M0 tant qu'une migration explicite n'est pas décidée ; introduire une couche de composition ou un objet verified context adapté.
2. Faire varier la policy selon l'hôte/scope, pas selon un flag global `allow_all`.
3. Les tests de conformité M0 continuent sur les acteurs synthétiques de démonstration ; ils ne deviennent pas des tests IAM.
4. L'application M1 ne doit pas exiger PyAuthKit, FastAPI, Django ni un service externe. Un adapter authentifié pourra être branché ensuite.
5. L'affectation d'une Task ne confère pas automatiquement de permission sur ses données ou sur le Project.

## 5. Menaces et scénarios négatifs prioritaires

- **Usurpation** : `actor_id`/scope changés dans la requête ou la CLI ne donnent aucun accès.
- **IDOR** : requête `GetTask(id)` ou `GetEvidence(id)` d'un autre scope renvoie un refus non révélateur.
- **Déduction d'existence** : `COUNT`, page 2, cursors, facettes, `filter=client` et export ne révèlent pas de ressources cachées.
- **Délégation indue** : `Task.assignee_id` ne crée pas un rôle d'approbation.
- **Permissions enfant** : une EvidenceRef privée reste invisible même pour un acteur autorisé à voir le Project parent si la policy l'interdit.
- **Corrélation** : logs, timestamps, nom de fichier backup, identifiant externe et Domain Events ne divulguent ni secret ni existence cross-scope.
- **Données contradictoires** : une observation cachée ne peut provoquer un `VERIFIED` apparent ou être citée dans un rapport visible.
- **Changement de policy** : une Query/cursor/reader ancien n'utilise pas implicitement une permission périmée.
- **Deux politiques différentes** : même use case M1 exécuté dans deux contextes avec des règles de validation différentes, sans changer le coeur.
- **Fail-close** : composant de policy non disponible => refus explicite, sans fallback permissif.

## 6. Preuves requises avant toute utilisation sur données réelles

| Test candidat | Vérification |
|---|---|
| `SEC-M1-01` | Auth context non vérifié refusé |
| `SEC-M1-02` | Même `actor_id`, scope changé dans payload, permissions inchangées |
| `SEC-M1-03` | Get/Query/List cross-scope sans indication d'existence |
| `SEC-M1-04` | Counts, facettes, tri, pages et cursors ne divulguent rien |
| `SEC-M1-05` | Enfants plus privés que le parent |
| `SEC-M1-06` | No disclosure en erreurs, exports, backups et logs |
| `SEC-M1-07` | Policy absente/inconnue/exception => fail-closed |
| `SEC-M1-08` | Permissions d'approval, observation et verification distinctes |
| `SEC-M1-09` | Deux policies de scope substituables (AC-026) |
| `SEC-M1-10` | SQLite pilot/CLI/Reader appliquent les mêmes règles que l'application M0 |

## 7. Limites et condition de révision

L'ADR ne fournit pas de sécurité contre du code local hostile ayant accès au processus ou au fichier SQLite ; celle-ci requiert isolation OS, coffre de secrets, chiffrement/gestion des clefs et threat model adaptés. Aucun `SEC-M1-*` n'a été exécuté à cette étape.

**Décision : ACCEPTED_FOR_M1_LOCAL_PILOT** pour le modèle de sécurité, avec **veto** sur ingestion de données réelles et sur production tant que tests/contrôles/mandats ne sont pas qualifiés.
