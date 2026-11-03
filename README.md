# PyProjectKit

## Prototype M0 exécutable sur cette branche

**Branche d'implémentation en brouillon, non fusionnée.** Le noyau Python M0 est implémenté dans `src/pyprojectkit/`, avec une API applicative, des ports, une UoW InMemory, des tests et une CI Python 3.12/3.13. Le [guide du bootstrap](docs/bootstrap/README.md) et le [scénario de démonstration](examples/first_project.py) documentent l'installation et l'usage.

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python examples/first_project.py
```

**Attention** : ce prototype ne représente pas encore une release ni un verdict de qualification. Les décisions architecturales D-01..D-07, la licence et les gates R0/M0 restent à ratifier. Aucune publication PyPI ou fusion automatique n'est autorisée.

**Statut du référentiel canonique : R0 / REVIEW. Statut de cette branche : prototype M0 implémenté en PR.**

PyProjectKit vise un noyau Python réutilisable de gestion de projets, tâches, jalons et dépendances, suivi d'un registre de projets et d'une intégration optionnelle avec Pythos. L'architecture et les contrats restent **proposés** tant que les arbitrages n'ont pas été validés.

## Ordre de livraison

1. **R0 - Réconciliation :** audit du dépôt, alignement des spécifications V2, ADR, critères d'acceptation, décision humaine `Q-R0`.
2. **M0 - Domain Kernel :** première tranche métier exécutable et testée.
3. **M1 - Project Registry :** registre durable, observations, preuves, snapshots et reprise.
4. **M2 - Pythos Integration :** intégration optionnelle, mandats et rapports.
5. **C3 - Extensions :** fonctionnalités avancées déclenchées par des besoins démontrés.

## Gouvernance R0

- [État initial du dépôt](docs/r0/2026-11-03_REPOSITORY_BASELINE.md)
- [Registre des écarts](docs/r0/RECONCILIATION_REGISTER.md)
- [Première revue de cohérence V2](docs/r0/2026-11-03_INITIAL_V2_CONSISTENCY_AUDIT.md)
- [Index des ADR](docs/adr/README.md)
- [Gate de passage Q-R0](docs/r0/Q-R0_GATE.md)
- [Pilotage de la roadmap](docs/ROADMAP_TRACKING.md)

**Règle de preuve :** une spécification n'est pas une implémentation. Un `GO` ou une qualification exige des critères vérifiés sur des références exactes et l'approbation de l'autorité habilitée.

Le dépôt ne doit pas accueillir de données confidentielles de clients, d'employeurs ou de projets personnels. Les spécifications V2 sources restent en `REVIEW` tant que leur baseline n'est pas acceptée.

## Documents sources

- `13_PYPROJECTKIT_IMPLEMENTATION_ROADMAP.md` (version proposée, 2026-11-02)
- `14_PYPROJECTKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md` (version proposée, 2026-11-03)
- Spécifications métier PyProjectKit V2 `00`, `04` à `12`, convention Py*Kit et overlay PyProjectKit.

L'inventaire et la publication des versions documentaires canoniques dans ce dépôt seront décidés durant R0. Aucune publication PyPI ni réalisation M0 n'est affirmée ici.
