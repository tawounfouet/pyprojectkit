# ADR-M2-04 - Vérification indépendante et revue humaine M2-B

> Date : 2026-11-04
> Statut : **PROPOSED / validation humaine requise**
> Source : `19_PYPROJECTKIT_M2B_IMPLEMENTATION_PLAN.md`
> Tranche : M2-06, pilotes synthétiques.

## Problème
`ExecutionReportDTO` est une déclaration d'un producteur qui peut annoncer `SUCCEEDED` ou `QUALIFIED` sans disposer de preuves. Une vérification source et une approbation humaine sont deux actes indépendants.

## Décision proposée et code du pilote
- Le service `ReportInboxService.receive` n'applique **aucune transition** M0, n'enregistre aucun `VerificationAssessment PASS` ni une approval.
- `ReportGovernanceService.request_verification` exige `VERIFY_REQUEST`, `ASSESS`, `WRITE_ASSESSMENT`, accès à la preuve et `REPORT_READ`. Un `IndependentEvidenceVerifier` est appelé sur la référence et la révision **exactes**. `UNKNOWN` pour source indisponible, et `PASS` ne peut résulter d'une source déclarée indisponible.
- `FakeIndependentEvidenceVerifier` est un **oracle déterministe provisionné hors du rapport**, utile pour les tests d'orchestration. Un PASS synthétique n'atteste aucune CI GitHub ou source réelle.
- Le résultat technique du pilote est conservé dans `m2_verifications` et une **observation** M1 append-only. Il ne crée jamais un historique M1 `assessment PASS`, car `RegistryService.verify_status` interpréterait ce PASS comme qualifiant. L'intégration ultérieure d'un vérificateur réellement autoritatif exigera un nouveau contrat pour produire un `VerificationAssessment` M1 valide.
- Résultat M2 et observation M1 sont committés ensemble, sans changer les états de tâche/projet.
- `request_human_decision` crée uniquement `PENDING`; une commande séparée `decide_human_request` exige `HUMAN_DECIDE`, `APPROVE`, `WRITE_DECISION` et une identité différente du demandeur et du receveur du report.
- La décision `APPROVED` est une **revue du report M2**, pas une publication, un merge, la clôture d'une Task ou le franchissement automatique du gate G5. Un record M1 `decision` est écrit, pas `approval` de publication.
- Toute lecture reste conditionnée par `REPORT_READ`, `PROJECT_VIEW`, `TASK_VIEW`, scope/owner et `INTERNAL`.

## Alternatives rejetées
- Convertir `reported_status=QUALIFIED` en `PASS` : interdit.
- Utiliser la même identité Pythos pour demander et approuver : interdit.
- Approuver automatiquement une publication après des tests : hors M2-B et hors mandat.
- Appeler un vrai fournisseur CI sans port testable : différé jusqu'aux pilotes M2-C.

## Tests, réserves et adoption
Contrôles négatifs : source indisponible, révision différente, absence de permissions, auto-approbation, double décision et absence de mutation M0. Les politiques de séparation des fonctions plus fines et les vrais connecteurs de preuve exigent une validation humaine ultérieure.

**Statut** : candidat technique, non approbation globale Q-M2.
