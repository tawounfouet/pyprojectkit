# PyProjectKit - Consolidation de qualification technique M0

> Date : 2026-11-03
>
> **Verdict : TECHNICAL_SCOPE_VERIFIED_FOR_INMEMORY / FORMAL_Q_M0_NOT_ASSESSED**
>
> Dossier de revue : [PR #6](https://github.com/tawounfouet/pyprojectkit/pull/6) (DRAFT, non fusionnée)
>
> SHA exact de la PR testé : `ab2d4246c758f70b35507ec7fe016f9344da723c`
>
> CI : GitHub Actions run `41653259680`
>
> Mandat de consolidation : https://github.com/tawounfouet/pyprojectkit/issues/8#issuecomment-6607173475
>
> Historique : [rapport BOOT-11 sur PR #6](https://github.com/tawounfouet/pyprojectkit/blob/feat/m0-bootstrap/docs/qualification/BOOTSTRAP_REPORT.md)
>
> **Règle de preuve** : `TECHNICAL_SCOPE_VERIFIED` ne vaut ni `Q-M0=GO`, ni `Q-R0=GO`, ni approbation de publication.

## 1. Vérification indépendante des preuves de CI

L'exécution GitHub Actions `41653259680` correspond au commit `ab2d4246c758f70b35507ec7fe016f9344da723c`, dernier HEAD inspecté de la PR #6 à la date de cette consolidation.

| Contrôle | Python 3.12 | Python 3.13 | Portée |
|---|---|---|---|
| Job `m0` | SUCCESS | SUCCESS | Actions, SHA ci-dessus |
| Tests pytest | **17 passed** | **17 passed** | Test suite M0 |
| `mypy --strict` | Success, 6 source files | Success, 6 source files | Typage sur sources et exemple |
| `pip wheel` | Wheel `0.1.0a1` construite | Wheel `0.1.0a1` construite | Build par environnement |
| Exemple headless | Job CI SUCCESS | Job CI SUCCESS | Pas de service distant obligatoire |

Détails observés dans les logs : tests 3.12 `17 passed in 0.11s`, 3.13 `17 passed in 0.08s`, mypy `Success: no issues found in 6 source files` dans les deux cas. **Ces résultats sont ceux du run référencé, pas de M1.**

Reproduction locale supplémentaire dans l'environnement de travail actuel (Python 3.13.5) : `PYTHONPATH=src python -m pytest -q` retourne **17 passed in 0.07s** ; `PYTHONPATH=src python examples/first_project.py` exécute le scénario avec deux Tasks et onze événements confirmés. Un lancement sans installation ni `PYTHONPATH=src` échoue logiquement à l'import du package ; cela ne réfute pas la preuve d'installation wheel de BOOT-11. **`mypy` n'est pas installé dans cet environnement de travail actuel**, donc son verdict est fondé sur les logs GitHub, pas sur une nouvelle exécution locale.

## 2. Traçabilité consolidée AC-001 à AC-012

| AC | Évidence à date | Classification prudente |
|---|---|---|
| AC-001 | Package importable, wheel construite sous CI ; installation wheel isolée décrite localement sous 3.13 | **VERIFIED_FOR_PROTOTYPE**, matrice wheel isolée 3.12 à compléter |
| AC-002 | Transition Project invalide et absence d'event succès, tests CI | **VERIFIED_INMEMORY** |
| AC-003 | Cycle Task, assignation/états et refus terminal, tests CI | **VERIFIED_INMEMORY** |
| AC-004 | Prérequis Task non terminé bloque démarrage, tests CI | **VERIFIED_INMEMORY** |
| AC-005 | Rejet de cycle et conflits de révision, tests CI | **VERIFIED_INMEMORY**, pas de concurrence SQL |
| AC-006 | Jalons `target_date`, `reached_at`, transition refusée | **VERIFIED_INMEMORY** |
| AC-007 | Clock et IDs déterministes, tests CI | **VERIFIED_INMEMORY** |
| AC-008 | UoW, copie isolée, rollback, version, transaction multi-écritures | **VERIFIED_INMEMORY**, non durable |
| AC-009 | Event de succès seulement après commit InMemory confirmé | **VERIFIED_INMEMORY**, pas d'Outbox |
| AC-010 | Core sans import obligatoire de frameworks/web/SQL | **VERIFIED_FOR_CURRENT_MODULES** |
| AC-011 | `mypy --strict` valide sur 3.12/3.13, six fichiers | **VERIFIED_CI** |
| AC-012 | Deux jobs CI verts sur le SHA de PR #6 | **VERIFIED_CI** |

**Règle** : ne pas transformer `VERIFIED_INMEMORY` en `VERIFIED_SQL`, `SECURITY_APPROVED` ou `Q-M0 GO`.

## 3. Lecture du code M0 et écarts de sécurité à ne pas masquer

Les ports M0 exposent `ActorContext(actor_id: str, scope: str)` et une `AuthorizationPolicy.require(actor, permission)`. L'exemple `ExplicitPolicy` vérifie `actor_id` contre un ensemble de permissions et utilise la valeur `scope` pour limiter la visibilité des Projects. **Ce n'est pas une authentification de l'acteur ni une autorisation objet/ressource vérifiée**. Sa sécurité dépend entièrement de la qualité du contexte fourni par l'hôte.

Il faut pour M1 :
- principal vérifié par un adaptateur hôte de confiance ;
- `ScopeId` canonique et relation projet/portée persistante ;
- policy tenant compte d'action, ressource et scope, deny-default ;
- Queries filtrées avant comptes, pagination, facettes, exports, journaux ;
- absence d'élévation par `assignee_id` ;
- contrôles 2 acteurs/2 scopes en accès négatif et 2 politiques différenciées ;
- données synthétiques tant que les règles de confidentialité ne sont pas qualifiées.

L'absence d'IAM et de chiffrement au repos est une **limite bloquante pour usage sur données réelles sensibles**, pas pour les fixtures synthétiques du pilote.

## 4. Lacunes techniques M0 et écarts de gouvernance

1. **Branche** : PR #6 toujours en brouillon, pas intégrée à `main` à la date examinée.
2. **Baseline documentaire** : PR #4 de réconciliation R0 encore en brouillon.
3. **D-SEM-01** : acceptée pour la compatibilité documentaire ; D-01..D-07 encore non ratifiés individuellement.
4. **Licence** : non décidée ; aucune permission de distribution publique du package ne découle du build.
5. **Événements** : notifications locales InMemory après commit ; aucune livraison durable sur crash.
6. **CommitOutcomeUnknown** : contrat d'erreur existant, non démontré avec un adapter SQL.
7. **Concurrence** : graphe et AR protégés dans un seul processus sous `RLock` ; pas de test à deux processus sur base partagée.
8. **Sauvegarde/reprise** : M0 ne persiste pas au redémarrage, précisément l'objet du M1.
9. **Permissions et scopes** : ActorContext minimal, policy démonstrative ; aucune certification sécurité.
10. **Protection GitHub `main` et signatures** : non vérifiées ici ; ne pas présumer que le repo les impose.

## 5. Décision de qualification et effet sur M1

**QUAL-M0-TECH-01** : le **prototype technique M0** est suffisamment éprouvé pour servir de **base de comparaison expérimentale** à une suite de contrats `InMemory` vs `SQLite` dans M1-A, à condition de conserver les limites de sécurité et de ne pas réutiliser une vérité prétendument durable.

**AUTORISÉ dans le périmètre documentaire** :
- architecture et spécification du pilote M1, ADR-M1-01/02/03 ;
- préparation des fixtures synthétiques et scénarios VS-M1-01 ;
- préparation d'une suite de tests de compatibilité, sans introduire des données réelles.

**NON AUTORISÉ par ce verdict** :
- fusion PR #4/#6/#9, release/tag/PyPI ;
- production, stockage partagé sensible ou utilisation multi-tenant réelle ;
- attribution de `Q-R0 GO`, `Q-M0 GO` ou `Q-M1 GO` ;
- élargissement silencieux de la garantie SQL à partir du seul M0.

## 6. Conditions de sortie pour la qualification formelle Q-M0

- [ ] D-01..D-07 validés ou réserves enregistrées avec le responsable humain.
- [ ] Baseline V2 M0 et ADR cohérents, référence Git acceptée.
- [ ] Licence et mode de publication décidés, sans diffusion implicite.
- [ ] Sécurité minimale revérifiée contre les garanties revendiquées en M0.
- [ ] Politique de branches et checks sur le SHA candidat confirmés.
- [ ] Matrice AC et limites approuvées par l'autorité habilitée.
- [ ] Gate `Q-M0` enregistré distinctement avec `GO / CONDITIONAL GO / NO-GO` et champ de décision humaine.

**Verdict de cette revue : `M0_TECHNICAL_BASELINE_EVIDENCED`, `Q-R0=NOT_ASSESSED`, `Q-M0=NOT_ASSESSED`.**
