# D-07 - Version Python, packaging et interface de distribution M0

> Statut : PROPOSED / NOT APPROVED | Revue R0, 2026-11-03
>
> Mapping : `ADR-PJ-RM-04`, `ADR-PJ-10-15`, `BOOT-01 / M0-01`.

## Problème

Le noyau doit être importable et installable sans infrastructure ; il ne faut pas créer une API trop large ni annoncer une compatibilité Python ou une licence qui n'ont pas été qualifiées. La vision 00 V2 et le bootstrap 14 proposent deux découpages de dossier différents, qui doivent être rapprochés avant BOOT-01.

## Choix structurants

**A - RECOMMANDEE POUR REVIEW :** packaging `src/`, module `pyprojectkit`, domaines dépendant seulement du standard library et des propres ports, `pyproject.toml` standard, tests sur un wheel/sdist isolé. Définir une façade publique minimale puis la stabiliser par tests. Choisir `requires-python >=3.12` **comme cible candidate** uniquement si la matrice de compatibilité et les consommateurs le confirment.

**B :** arborescence de la vision 00 V2 par domaines fonctionnels `core/projects/work/milestones/...` dès M0. Avantage conceptuel ; risque de packages prématurés ou de dépendances circulaires.

**C :** arborescence du bootstrap 14 `domain/application/ports/adapters` dès M0. Plus simple à qualifier, mais les domaines `projects` et `tasks` ne doivent pas être fusionnés par commodité.

**Arbitrage proposé :** retenir C comme squelette *physique initial*, tout en préservant les bounded contexts et la séparation des modules `projects.py`, `tasks.py`, `dependencies.py`. L'arborescence 00 représente une *vision d'évolution*, pas une obligation de créer les dossiers M1/C3 au bootstrap.

## Contrat minimal BOOT-01 à approuver

- Distribution `pyprojectkit` et code `src/pyprojectkit` sous licence **à décider et documenter**. Ne pas écrire un faux fichier LICENSE.
- Compatibilité de départ `>=3.12` **proposée**, non encore validée ; matrice de CI à fixer selon environments de consommateurs réels.
- Version de pré-release candidate `0.1.0a1` mentionnée dans le plan ; ni tag, ni release, ni PyPI sans gate de publication distinct.
- API Python core et petits Value Objects accessibles sans base de données, réseau, FastAPI, Django, SQLAlchemy, drivers DB ou Pythos.
- `Clock` et `IdFactory` injectables pour les tests déterministes.
- `README`, tests et exemples de création Project installables depuis une distribution construite ; module importable sans extras.
- Lint, typage, tests unitaires et de contrat, build et test de distribution en CI **sur le SHA inspecté**.
- Aucun secret ni artefact confidentiel dans le dépôt public.

## Options ouvertes qui bloquent la stabilisation

| Sujet | Orientation candidate | Preuve / décision attendue |
|---|---|---|
| Python minimum | `>=3.12` | Environnements consommateurs et CI 3.12/3.13 ou autre matrice retenue |
| Nom de package | `pyprojectkit` | Contrat d'import et distribution à confirmer |
| Structure | `src/pyprojectkit/{domain,application,ports,adapters}` | Architecture fitness imports, coûts de refactor |
| Licence | Indéterminée | Choix explicite du propriétaire, puis fichier exact |
| Version | `0.1.0a1` candidate | Convention de release et gate `Q-M0` |
| Façade publique | Petite API de Project/Task et Commands | Premier consommateur et tests typés |

## Cas de test pour Q-M0

1. Installer wheel/sdist dans un environnement vierge sur chaque version Python supportée.
2. Importer et créer un Project sans réseau ni base de données.
3. Interdire les imports externes infrastructure/frameworks dans `domain`.
4. Typage des exemples publics et vérification des dépendances.
5. CI verte à SHA exact, documentation des outils et de leurs versions.
6. Ne pas publier ni taguer automatiquement à la suite d'une CI verte.

## Sources et limites

`00_PROJECT_VISION_AND_ARCHITECTURE_V2 §58, §66`; `00_REQUIREMENTS_ANALYSIS_V2 §NFR-001, §34`; `14_IMPLEMENTATION_BOOTSTRAP_PLAN §§7-8, 18, 21, 24`. Les noms et la matrice n'ont pas encore été approuvés ; les snippets historiques ne sont pas un code exécutable.

## Décision

**Option A avec squelette C recommandée pour M0 ; PROPOSED.** Aucun `pyproject.toml`, build, CI ni test de compatibilité n'est créé par ce document.
