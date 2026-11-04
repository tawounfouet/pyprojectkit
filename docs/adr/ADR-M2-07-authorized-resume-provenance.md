# ADR-M2-07 - ResumeWorkItemQuery et provenance M1/M2

- **Statut** : PROPOSED - revue humaine obligatoire
- **Date** : 2026-11-04
- **WorkItem** : M2-10

## Problème
L'inbox M2-B retrouve un report après redémarrage mais ne reconstitue pas automatiquement le dossier de travail, les snapshots/handoffs et les limites de provenance.

## Décision candidate
- Introduire `ResumeWorkItemQuery` et `ResumeWorkItemView` immuable en M2, sans mutation ni migration SQLite 0004.
- Faire valider `RESUME` via `RegistryService.resume`, `TASK_VIEW` via `list_tasks` et `REPORT_READ` via `ReportInboxService.list_reports`, puis filtre owner/scope/classification dans la même `SqliteUnitOfWork` pour les métadonnées complémentaires.
- Exposer **IDs et statuts minimaux** de reçus, report, contrôle synthétique et revue humaine, jamais les tokens de session, le corps complet du brief ou une clé de mandat.
- `missing_sections` pour snapshot/handoff/review/verifier absents, `stale_sections` si `snapshot.task_versions` diffère de la version actuelle.
- `next_safe_action` n'est qu'une proposition. Cas `TEACHING` : proposition pédagogique, aucune commande de release.
- Une source `UNKNOWN` reste inconnue même si le report indique `SUCCEEDED`.
- Un nouveau processus peut lire selon ses droits de session sans reprovisionner de mandat pour cette **lecture historique** ; tout nouveau write M2-B réclame à nouveau un mandat host-side.

## Alternatives rejetées
- Reconstituer le mandat depuis `ExecutionReportDTO` : autorité usurpable.
- Relire des tables SQLite dans les scripts clients : contournement des readers protégés.
- Inventer un snapshot manquant ou des données de conversation : interdit.

## Limites
`latest_snapshot` et `latest_handoff` de M1 sont project-level et non nécessairement strictement task-level. La fraîcheur source Git réelle et la révocation de l'identité host ne sont pas garanties hors périmètre de lecture. L'API ne contient pas une archive entière des briefs.

## Vérification
Tests `RES-01..12`, lecture interprocessus, cross-owner/scope, non-écriture, absence et obsolescence explicites.
