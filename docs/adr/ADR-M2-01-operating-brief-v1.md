# ADR-M2-01 - Contrat OperatingBriefDTO v1

- Date : 2026-11-04
- Statut : PROPOSED / revue humaine requise
- Tranche : M2-A, M2-01
- Source : 17_PYPROJECTKIT_M2A_IMPLEMENTATION_PLAN.md

## Contexte
Pythos a besoin d'une description transportable d'une intervention autorisée. Les objets M0/M1 et les décisions humaines ne doivent pas migrer dans un DTO mutable.

## Décision candidate
- DTO immuable (frozen dataclass), hors du domaine, version `1.0`, sérialisation JSON stable avec clés triées.
- Refus des versions et champs inconnus, doublons JSON, valeurs non typées, dates sans timezone.
- Maximum 16 KiB, 32 éléments par liste, SHA complet si `GIT_COMMIT`.
- Date limite <= fin du mandat et TTL maximum 20 minutes.
- `allowed_actions` contient des permissions de lecture, jamais un octroi d'autorité.
- `WorkItemRef(kind=TASK)` référence une tâche existante sans nouvelle source de vérité.
- Le brief contient une projection minimale et n'exporte ni historique brut ni documents privés.

## Alternatives
- Pydantic/JSON Schema : écarté pour le pilote sans dépendance externe ; publication éventuelle d'un schéma stable reportée.
- Copie directe des objets M1 : rejetée (fuite et couplage).
- Enregistrement persistant des briefs : reporté à un besoin M2-B prouvé.

## Conséquences et limites
Contrat stable pour le pilote local synthétique. Pas d'API de compatibilité v2 ni de signature cryptographique, aucune protection contre du code Python hostile in-process.

## Preuves exigées
Round-trip, sérialisation canonique, invalidités/versions/limites, test d'import sans Pythos, CI sur SHA exact.
