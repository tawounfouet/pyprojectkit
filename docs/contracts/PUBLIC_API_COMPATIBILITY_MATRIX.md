# ARCH-03 - Contrats publics et compatibilité observable

> Référence de comparaison : legacy `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`, noyau VS01 branché sur main `dd8ec1c945ece80362f2c009ad56493fa855825f`.

| Surface | API M0/M1/M2 historique | Nouveau chemin | HD-05 | Compatibilité |
|---|---|---|---|---|
| Distribution Python | `pyprojectkit` et entrée CLI `pyprojectkit` | `pyprojectkit_next` additionnel dans la même wheel | `PRESERVE` M0 | Aucun renommage ni remplacement de la distribution |
| Identités | `ProjectId.value: UUID` | `ProjectId.value: str`, `from_uuid()` et `to_uuid()` | `PRESERVE` sémantique | `BREAK_WITH_NOTICE` de signature si remplacement futur, **NON AUTORISÉ** |
| Services | `pyprojectkit.service.ProjectService` avec méthodes historiques | `pyprojectkit_next.application.ProjectService` avec commandes dédiées | `PRESERVE` sémantique | API non interchangeable |
| Permissions | `ExplicitPolicy` avec grants par action | `OwnerScopePolicy`, `ActorContext(subject_id, allowed_scopes)` | `PRESERVE` sécurité | `PARTIAL` : pas de RBAC équivalent et aucun hôte authentifiant dans la librairie |
| Refus | `NotFound` et `AccessDenied` selon surfaces | `NotFound` neutre pour ressource cachée/absente | `PRESERVE` non-divulgation | Contrat d'exception modifié dans VS01, à versionner avant consommation externe |
| Events | `DomainEvent(name, aggregate_id, occurred_at, actor_id)` | Version d'agrégat ajoutée et labels parfois différents | `PRESERVE` propriété post-commit | `PARTIAL`, pas de compatibilité binaire |
| Repository/UoW | Dépôt mutable et `InMemoryUnitOfWork` historique | Entités gelées, `InMemoryDatabase.unit_of_work` | `PRESERVE` atomicité | Tests de propriétés plutôt que type/API stricts |
| M1 SQLite/CLI | `pyprojectkit.m1.*`, migrations `0001..0003` | Aucun adapter VS01 durable | `DEFER` | Imports historiques conservés dans la wheel, **pas remplacés** |
| M2 Pythos | `pyprojectkit.m2.*` | Absent du nouveau package | `DEFER` | Pas de délégation ni d'approbation automatique |

**Règle de passage :** les consommateurs externes restent non inventoriés : aucun ne doit être migré par défaut. Une future dépréciation exige versioning, inventaire des consommateurs, compatibilité des exceptions et contrats de sécurité, tests par client et décision explicite. La coexistence de deux packages dans la wheel est temporaire et **additive**.
