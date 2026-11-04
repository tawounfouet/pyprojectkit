# ADR-M2-06 - Frontières des pilotes M2-C

- **Statut** : PROPOSED - revue humaine obligatoire
- **Date** : 2026-11-04
- **WorkItems** : M2-08, M2-09, M2-11
- **Source** : 21_PYPROJECTKIT_M2C_IMPLEMENTATION_PLAN.md

## Problème
Une démonstration agentique sur PySRMKit peut confondre un vrai dépôt et une fixture, ou faire passer un report `QUALIFIED` pour une qualification de source.

## Décision candidate
- Les pilotes sont orchestrés par `tests/` et `examples/`, hors du domaine M0 et sans ajout de `WorkItem` Aggregate Root.
- P1 : dépôt Git **local éphémère** de fixture `synthetic-pysrmkit`, SHA obtenu par `git rev-parse HEAD`, arbre et fichiers vérifiés avant/après. Aucun dépôt privé PySRMKit ni hook réseau.
- P2 : `TEACHING`, autre scope et owner, référence `PROJECT_REVISION`, critères pédagogiques et reviewer distincts. Pas de gates logiciels G0-G7.
- `FakePythosAdapter` uniquement, mode `AUDIT/A0`; aucune capacité de shell, merge, tag, publish, delete ou réseau passée au producteur.
- Report toujours une **déclaration** ; aucun `assessment PASS` M1 tiré d'une source synthétique.
- `PRIVATE` et tout contenu personnel réel restent hors mandat.
- SEC-07/08 notés `NOT_APPLICABLE_NO_TOOL` pour la commande externe inexistante : absence de surface testée, pas de refus d'une API imaginaire.

## Alternatives non retenues
- Pilote directement sur le vrai PySRMKit : trop d'autorisations, données et dépendances non explicitées.
- Inclusion des politiques P1/P2 dans `domain.py` : couplage et spécialisation injustifiés.
- Interprétation de `QUALIFIED` comme PASS : interdit.

## Preuves attendues
`tests/test_m2c_pilots.py`, `tests/test_m2c_security_a.py`, `tests/test_m2c_security_b.py`, `examples/m2c_pilots_demo.py`, CI sur SHA exact.

**Limite** : un audit de fixture ne qualifie pas le vrai dépôt ou un vrai modèle Pythos.
