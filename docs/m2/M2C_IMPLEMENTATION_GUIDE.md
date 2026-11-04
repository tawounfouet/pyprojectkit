# M2-C - Guide de pilotes, reprise et qualification Q-M2

> Date : 2026-11-04  
> Source : `21_PYPROJECTKIT_M2C_IMPLEMENTATION_PLAN.md`  
> Statut : IMPLEMENTED_SYNTHETIC_LOCAL / HUMAN_GATE_PENDING  
> Périmètre : fixtures fictives uniquement, sans Pythos réel, données clients ni publication.

## 1. Architecture et séparation des responsabilités

- Le core `Project/Task` et ses transitions restent dans M0.
- Les contrôles d'identité, propriétaire, scope, snapshots/handoffs restent M1.
- M2-A produit `OperatingBriefDTO` à partir de lecteurs M1 et d'un mandat hôte.
- M2-B conserve `ExecutionReportDTO` **déclaré**, reçu d'émission, inbox atomique et évaluation synthétique séparée.
- M2-C ajoute `ResumeWorkItemQuery` (reader protégé avec provenance) et `AcceptanceEvidence/QualificationDossier` (manifest non autoritatif). Aucun nouveau `WorkItem` Aggregate Root ni migration 0004.
- `FakePythosAdapter` n'utilise aucun LLM ni SDK, n'exécute aucune commande et ne possède aucun droit de merge, publication ou approbation.

## 2. Pilotes exacts

### Pilote P1, PySRMKit synthétique

Le script crée un dépôt Git éphémère `synthetic-pysrmkit` avec des fichiers de fixture non sensibles. Il récupère le SHA réel `git rev-parse HEAD` et l'arbre `HEAD^{tree}`, et compare le dépôt avant et après le parcours. Le résultat `QUALIFIED` de FakePythos n'est qu'un statut déclaré. La vérification synthétique, même PASS, ne devient pas `RegistryService.verify_status=PASS`.

### Pilote P2, non logiciel

Le script crée un projet `TEACHING` sous un autre scope et un autre propriétaire. La référence `PROJECT_REVISION` et la prochaine action sont pédagogiques. Une revue de programme peut être créée en `PENDING`, sans gates G0-G7, package, tag ni approbation de release.

## 3. Exécuter les démonstrations

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/m2c_pilots_demo.py
python -m mypy --strict --python-version 3.12 src/pyprojectkit examples/first_project.py examples/m2c_pilots_demo.py
python -m pip wheel --no-deps -w dist .
```

L'exemple déclenche deux processus Python : le producteur de la fixture puis une invocation `--resume` sans aucune copie du `InMemoryMandateStore`. Une lecture historique autorisée est possible, mais une nouvelle émission/ingestion réclamerait un mandat valide provisionné par l'hôte.

## 4. Lecteur ResumeWorkItemQuery

Entrée : `VerifiedActor`, `project_id` et `WorkItemRef(kind="TASK")` existant. Le lecteur impose `RESUME`, `PROJECT_VIEW`, `TASK_VIEW` et `REPORT_READ`, vérifie scope et owner via M1, et lit seulement des métadonnées M2.

Sortie immuable `ResumeWorkItemView` : identifiants de projet/tâche, statut/version courants, source du snapshot/handoff, reçus et report ids, statut de vérification locale, revue humaine, `missing_sections`, `stale_sections`, `next_safe_action` et provenance.

- Un snapshot absent est `missing`; si sa version de Task diffère du présent, il est `stale`.
- `latest_snapshot` et `latest_handoff` restent des informations à l'échelle du projet, pas une vérité task-level certifiée.
- Une source indisponible renvoie `UNKNOWN`, jamais un PASS M1 ni une décision de publication.
- Le texte d'un handoff/prompt ne déclenche aucune action.
- Une consultation ne recrée aucun mandat, report ou événement métier.

## 5. Matrice sécurité SEC-01..30

La qualification comprend trente scénarios de refus, de non-divulgation et de robustesse. Les tests `SEC-07` et `SEC-08` sont **NOT_APPLICABLE_NO_TOOL** pour les API de merge/publish/priorité non exposées : leur absence est inspectée, pas un refus imaginaire d'une commande réelle.

Les autres tests couvrent expiration, suspension, révocation, owner/scope, PRIVATE, A4/A5, faux `brief_id`, SHA et Task divergents, collisions et replays, crash, ACK perdu, faux token, `QUALIFIED` non probant, champs inconnus, secrets, prompt injection, counts/list, payload borné, temps, mode, SoD, source UNKNOWN, append-only, projection obsolète, permissions.

## 6. Q-M2 : 11 AC et approbation indépendante

Le manifeste `AcceptanceEvidence` n'est pas un contrôle automatique de la vérité GitHub. Il exige un SHA 40 caractères, une source CI déclarée, des tests, un environnement et des limites. `build_qualification_dossier` valide la présence unique d'AC-027..037, compte PASS/FAIL/PARTIAL/non évalués et produit une recommandation **non autoritative**.

Même avec 11 PASS locaux, `human_gate=PENDING` et `adoption_decision=NOT_GRANTED`. Le reviewer doit examiner les preuves, accepter ou refuser explicitement les risques, puis autoriser un périmètre défini avant toute suite.

### Gaps restants d'autorité

- **AC-031 PARTIAL** : aucune véritable surface de commande de merge/publish/delete/priorité à tester, bien qu'aucune autorité A4/A5 ne soit accessible dans ce pilote.
- **AC-034 PARTIAL** : séparation des fonctions testée, mais gate Q-M2, gate G5 et approbation indépendante d'un artefact réel non réalisés.
- ADR-M2-01..08 : PROPOSED. La CI n'approuve pas les ADR.
- Les tests n'attestent pas un vrai repo PySRMKit ni un vrai provider CI/LLM.

## 7. Handoff et décisions

- M2-C code/CI local synthétique : à qualifier sur le SHA final.
- Q-M2 : revue indépendante, adoption `NOT_GRANTED`.
- M2-A #16, M2-B #17 et M2-C #18 sont des PR empilées non fusionnées.
- Aucun accès à des données PRIVATE, réelles clients/employeur/étudiants, aucun merge, release ni publication.
- Toute intégration à Pythos réel doit faire l'objet d'un **nouveau mandat**, d'un contrat d'API vérifié, d'une sandbox et d'une politique de données.

Le prochain acte sûr est une revue humaine des ADR, des deux AC partiels, des preuves CI et des risques. Pas de promotion automatique d'une branche par l'agent.
