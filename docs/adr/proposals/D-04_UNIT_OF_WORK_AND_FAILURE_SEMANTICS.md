# D-04 - UnitOfWork, commits incertains et échecs

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-05`, `ADR-PJ-10-01..04`, `ADR-APP-05`, familles d'erreurs `ADR-ERR-V2-*`.

## Problème

`Project`, `Task` et graphe peuvent être touchés dans un même use case. Faire un `save()` ne doit pas équivaloir à valider. La commande doit distinguer refus métier, conflit, panne confirmée et **issue inconnue du commit**.

## Options

**A - RECOMMANDEE :** UoW explicite synchrone, scope transactionnel local documenté, `ProjectRepository` / `TaskRepository` / `DependencyGraphPort` partageant la même transaction lorsque l'atomicité est revendiquée ; `commit()` appelé au plus une fois pour le succès.

**B :** chaque repository commite implicitement. Risque de projet enregistré sans tâche, cycle ou événement correspondant ; refusé comme candidat M0.

**C :** orchestration distribuée transactionnelle GitHub/CI/SQL et services. Hors périmètre M0, ne pas simuler de garantie ACID globale.

## Contrat proposé

- `with uow:` crée une frontière dont l'état de sortie est déterminé ; sans appel explicite à `commit()`, rollback.
- Exception avant commit => rollback, aucune publication de succès.
- Échec *confirmé* du commit => rapport d'échec ; ne pas publier le succès.
- Timeout ou rupture de connexion pendant commit => `CommitOutcomeUnknown` ; ne présumer ni réussite ni annulation, ni rejouer à l'aveugle.
- Les agrégats retournés par le repository sont isolés du stockage ; mutation d'une copie sans `save()`/commit ne modifie pas la vérité.
- `expected_version` explicitement utilisé pour les garanties de concurrency des deux AR.
- Le buffer d'événements reste attaché à la transaction et non à une notification réseau envoyée précommit.
- Les erreurs techniques restent distinctes des exceptions d'invariant ; messages publics ne divulguent pas de secrets.

## Cas de test contractuels

1. `get` puis mutation sans commit : aucune persistance.
2. Ajout de Project et Task dans la même UoW puis exception : aucun des deux visibles après sortie.
3. `save` sur version périmée : conflit, pas de lost update.
4. Deux mutations réussies de même use case : un seul commit logique observé.
5. Simulation de `CommitOutcomeUnknown` : demande de réconciliation, aucun faux résultat DONE et aucun retry automatique.
6. `DomainEvent` après commit confirmé seulement ; panne du dispatcher postcommit n'annule pas rétrospectivement l'écriture.

## Port et code

La signature de référence `__enter__ / __exit__ / commit / rollback` figure dans `10 V2 §17`; aucun extrait n'est ici une API Python exécutable. Les migrations SQL et une Outbox ne sont pas des conditions d'entrée M0.

## Sources

`08 V2 §7`; `09 V2 §§7-8`; `10 V2 §§11-19,36-39`; `11 V2 §§17-23`; `DEEP_DIVE_UNIT_OF_WORK_CONCEPT_THEORIE_APPLICATIONS_ET_PYPROJECTKIT.md`.

## Décision

**Option A recommandée ; PROPOSED**, avec contrat de rollback, incertitude et tests négatifs. Aucune garantie runtime n'est qualifiée.