# ARCH-03 - Périmètre autorisé et capacités différées

| Capacités | Décision HD | État | Conséquence technique |
|---|---|---|---|
| M0 Project/Task, graphes et UoW Memory | `PRESERVE` | Implémentation VS01 additive qualifiable | Ne pas substituer les imports legacy |
| Sécurité Owner + Scope | `PRESERVE` comme invariant | InMemory et policy expérimentale | `ActorContext` n'est pas une preuve d'AuthN ; hôte fiable obligatoire |
| M1 Registry/SQLite | `DEFER` | Code historique intact ; pas de nouveau SQLite | ARCH-06 nécessite gate et lignée de migrations séparée |
| M2 Mandats Pythos et inbox | `DEFER` | Code historique intact ; aucun runtime agent réel nouveau | Q-M2 AC-031/034 et revue restent ouverts |
| ProjectHub / WorkItemView | Hors VS01 | Non implémenté | ARCH-07 via adapter entrant distinct |
| Données réelles | HD-06 synthétique uniquement | Interdites pour VS01 | Pas de lecture, copie ou migration des bases existantes |
| Archivage legacy | HD-11 hors G0-04 | NON EXÉCUTÉ | G1 sans preuve ; aucun retrait du legacy |
| Release/version PyPI | Hors périmètre | NON AUTORISÉ | Licence explicite sélectionnée, texte encore inconnu |

Le prochain dossier ARCH-06 peut préparer des tests de contrat en RED tant que G2 demeure PENDING. Il ne doit pas déclarer une persistance qualifiée ni déclencher une migration sans son mandat de gate.
