# R0-02 - Proposition de remédiation des collisions d'identifiants V1/V2

> Statut : PROPOSED / NOT_APPLIED_TO_CANONICAL_SPEC
>
> Date : 2026-11-03
>
> Source de preuve : [audit direct des V1/V2](2026-11-03_V1_V2_DIRECT_SOURCE_AUDIT.md)
>
> Cible éventuelle : `07_PYPROJECTKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES_V2.md`, après approbation.

## Principe de compatibilité

Un identifiant `INV-*` ou `BR-*` déjà présent dans la V1 ne peut désigner une nouvelle propriété incompatible sans décision explicite de migration. Les nouvelles règles V2 reçoivent des codes distincts. La compatibilité ne signifie pas qu'une API publiée existe : les contrats sont pour l'instant documentaires.

## Patch conceptuel proposé, sans changement silencieux du document 07 V2

### A. Section 11 - Livrables

Remplacer les définitions concurrentes de `BR-DELIV-001/002` par :

```text
BR-DELIV-001    Un livrable ne peut être accepté que si ses critères obligatoires sont satisfaits.
BR-DELIV-002    Une validation finale peut exiger une Approval selon la policy.
INV-DELIV-V2-001  Un livrable référence un Project ou Milestone identifiable et autorisé.
```

`INV-DELIV-V2-001` est un **nouvel identifiant candidat**, pas une règle historique V1.

### B. Section 12 - Affectations

Rétablir les sens V1 en les complétant par les exigences de portée V2 :

```text
BR-ASSIGN-001    Une Task ne peut être affectée qu'à un membre admissible et résolu dans le scope autorisé.
BR-ASSIGN-002    L'admissibilité peut être déterminée par une policy de membership/rôle du Project.
BR-ASSIGN-003    Une affectation terminée conserve sa date unassigned_at lorsque son historique est géré.
BR-ASSIGN-V2-001  M0 admet au plus un assigné actif par Task ; la multi-assignation est différée.
BR-ASSIGN-V2-002  Une affectation autorisée ne contourne pas les statuts terminaux de la Task.
```

Les codes `BR-ASSIGN-V2-001/002` sont des **candidats de V2**. Les effets de `unassigned_at` sur la version sans entité d'affectation historique doivent être explicités avant M0 : ne pas promettre un historique non persistant.

### C. Section 12 - DateRange

```text
INV-DATE-001      Toute période ordonnée respecte start <= end lorsque les bornes sont présentes.
INV-DATE-002      Une période vide n'est permise que si son contrat métier l'autorise explicitement.
INV-DATE-V2-001   Les bornes d'une période utilisent des types et granularités temporelles compatibles.
```

La nouvelle exigence V2 de compatibilité temporelle reçoit `INV-DATE-V2-001` sans effacer la règle historique V1 des périodes vides.

## Impacts sur les autres documents et tests

| Cible | Action requise si approuvée |
|---|---|
| 07 V2 corps et annexe A | Aligner les deux zones, interdire la double signification pour un même ID |
| 08 V2 Commands/Use Cases | Vérifier `AssignTask`, `CreateMilestone` et `AcceptDeliverable` conditionnel |
| 09 V2 Domain Events | Vérifier que `TaskAssigned` et `TaskUnassigned` ne déclarent pas un succès après échec |
| 10 V2 Repositories/UoW | Clarifier garantie de conservation de l'historique d'affectation selon la capacité disponible |
| 11 V2 Error Model | Garder `AuthorizationError`, `InvalidAssignment`, `InvalidDateRange` et rollback contextualisés |
| 12 V2 Security | Confirmer admissibilité et permissions : une affectation n'est jamais l'octroi d'accès |
| R0-07 | Ajouter des tests négatifs pour chaque ID conservé et nouveau |

## Critères d'acceptation de la correction documentaire

- [ ] L'autorité humaine accepte ou révise les significations et les nouveaux codes.
- [ ] Toute référence `BR-ASSIGN-001..003`, `BR-DELIV-001/002` et `INV-DATE-002` porte un sens unique dans le corps et les annexes.
- [ ] La différence `admissibility` / `authorization` est explicitée.
- [ ] Les variantes V1 ne sont pas qualifiées comme API Python déjà publiée.
- [ ] La matrice AC et les scenarios négatifs reflètent les changements.
- [ ] Les documents canoniques ne sont modifiés qu'après revue et décision tracée.

**Décision : PENDING.** Ne pas confondre ce patch candidat avec une migration approuvée.
