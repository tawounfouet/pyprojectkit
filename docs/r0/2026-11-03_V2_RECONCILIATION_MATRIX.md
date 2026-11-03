# R0-02 - Matrice de réconciliation V2, revue structurée M0

> Version de travail : 2026-11-03 | Statut : REVIEW / NOT_APPROVED
>
> Référentiel : documents PyProjectKit 00 (besoin, exigences, vision), 04 à 12 V2, overlay, roadmap 13 et bootstrap 14.
>
> Portée : contrats nécessaires au M0. Le corpus V1 historique n'a pas été audité dans son intégralité.
>
> Cette matrice décrit la cohérence documentaire, **pas** la conformité du code, un audit exhaustif ni une décision d'architecture acceptée.

## Méthode de classement

- **COHERENT_PROPOSED** : plusieurs textes V2 soutiennent la même option, sans approbation.
- **NOMENCLATURE_GAP** : deux noms concurrents existent ; choisir le nom public et documenter les alias.
- **DECISION_REQUIRED** : choix ou frontière de garantie à approuver pour le M0.
- **DEFERRED** : décision ne bloquant pas le premier noyau, à préserver sans l'implémenter.
- **NOT_VERIFIED** : données sources ou comportement hors de la vérification réalisée.

## Matrice CURRENT / TARGET / GAP / DECISION / EVIDENCE

| GAP | CURRENT dans le corpus V2 | TARGET M0 | Classification | Proposition d'arbitrage et statut |
|---|---|---|---|---|
| GAP-01 | 05 §9.3 et 07 §9.3 : `Task` AR M0 ; `WorkItem` langage commun. 08 `APP-V2-008` refuse un deuxième AR sans besoin | Une tâche opérationnelle, identité stable ; `WorkItem` comme concept transversal | COHERENT_PROPOSED | Pas d'AR `WorkItem` en M0 ; **PROPOSED** |
| GAP-02 | 05 §§8-11, 06 §3.2 et 10 §14 : deux AR `Project`/`Task`, `Milestone` interne à Project, `Dependency` VO/lien | Frontières cohérentes, contrôle inter-AR dans l'Application | COHERENT_PROPOSED + DECISION_REQUIRED | Décider les frontières et le placement du lien via ADR candidats ; **PENDING** |
| GAP-03 | 07 §10 `APP-DEP-001`, 10 §15, 11 §16 : graphe acyclique mais race possible sous écritures concurrentes | Aucun cycle ni double écriture partielle sur adapter revendiquant concurrence sûre | DECISION_REQUIRED | Port de graphe versionné par projet candidat ; garantir par tests selon adapter ; **PENDING** |
| GAP-04 | 08 §7, 10 §17, 11 §17 : UoW explicite, sortie sans commit annule ; issue de commit inconnue distincte du rollback | Un même contrat UoW local et ses échecs, avec InMemory isolé | COHERENT_PROPOSED + DECISION_REQUIRED | Choisir signatures minimales et tests de contrat ; **PENDING** |
| GAP-05 | 08 §11.4 : `PutProjectOnHold` ou `PauseProject` ; 07 §8.2 : `PauseProject`; 09 §10 : `ProjectPutOnHold` héritage V1 ; 08 §11.7 évoque `TaskReadied`, 09 §11 retient `TaskMarkedReady` | Un nom canonique par Command/Event ; aliases historiques seulement s'ils sont requis | NOMENCLATURE_GAP | Candidats : `PutProjectOnHold` / `ProjectPutOnHold`, `MarkTaskReady` / `TaskMarkedReady`. **PENDING** |
| GAP-06 | 12 §4, §§13-17 : ActorContext fiable, permissions projet, guard Command/Query M0. 07/08 : scopes et décisions avant mutation ; M1 élargit les vues | Minimum M0 fail-closed testable, sans IAM intégré ni Pythos obligatoire | DECISION_REQUIRED | Matrice M0 par opération et politique de ressource invisible ; **PENDING** |
| GAP-07 | 05 §8-9 et 07 §§8-9 : ProjectStatus et TaskStatus distincts ; 08 §2 : `DONE != VERIFIED`; 09 §3 : audit/event/report distincts | Glossaire, noms de transitions, état métier ≠ état de qualification | COHERENT_PROPOSED + NOMENCLATURE_GAP | Voir `R0-03_DOMAIN_GLOSSARY.md` ; **REVIEW** |
| GAP-08 | Vision 00 §métadonnées : Python 3.12+ cible historique ; 14 §8 : `requires-python >=3.12` et `0.1.0a1` illustratifs ; licence indécise | Baseline Python/packaging minimale décidée avant BOOT-01 | DECISION_REQUIRED | `>=3.12` candidat à confirmer, pas de version ou licence publiées implicitement ; **PENDING** |
| GAP-09 | Familles d'identifiants ADR concurrentes : `ADR-06-*`, `ADR-07-*`, `ADR-APP-*`, `ADR-PJ-10-*`, `ADR-ERR-V2-*`, `SEC-ADR-V2-*`, `ADR-PJ-RM-*` | Index canonique par **décision**, avec alias vers références historiques, sans dupliquer l'arbitrage | DECISION_REQUIRED | Voir `R0-10_ADR_CROSSWALK.md` ; **REVIEW** |
| GAP-10 | Requirements 00 §34 : `AC-001..012` M0 ; 13 §8 et §15 : gate complet ; 14 §1 : premier scénario, non qualification totale | Distinguer vertical slice de démonstration et gate final `Q-M0` | COHERENT_PROPOSED | `AC-001..012` restent nécessaires à Q-M0 ; mapping en `R0-07_M0_ACCEPTANCE_TRACEABILITY.md` |

## Deux points de précision supplémentaires

**DATE-01 - Milestone.** 07 §11 `INV-MILE-002` exige une date cible au M0 ; 09 §13 représente `due_at?` dans un payload d'événement *illustratif*. Ce n'est pas la preuve d'un contrat d'entité optionnel. Il faut fixer l'information obligatoire dans la Command et l'événement, et distinguer `target_date` de `due_at` selon la granularité temporelle. Classification : `NOMENCLATURE_GAP`, à couvrir dans l'ADR de contrat M0.

**AUTH-01 - Critères M0.** Les AC-001..012 ne comportent pas un AC explicite « refus de lecture/commande hors scope », alors que 12 §4 l'exige pour M0 et 10 §19 possède `CT-10-M0-12`. Il faut **ajouter un test de sécurité transversal** sans falsifier ou renuméroter le texte normatif des AC. Classification : `TRACEABILITY_GAP`.

## Décisions bloquantes proposées avant BOOT-01

1. Baseline et noms publics minimaux : GAP-05/07/08.
2. Modèle de domaine et frontières : GAP-02.
3. Transaction locale / graphe / échecs : GAP-03/04.
4. Contrôles d'autorisation M0 : GAP-06.
5. Gate, tests, preuves et approbation : GAP-09/10/ AUTH-01.

## Ce qui reste à faire pour fermer R0-02

- [ ] Effectuer la comparaison intégrale avec la V1, documenter les changements historiques qui affectent M0.
- [ ] Vérifier identifiants d'erreurs et l'intégralité des événements/vues publics du premier vertical slice.
- [ ] Faire accepter ou refuser les décisions structurantes ; un alignement documentaire ne vaut pas validation.
- [ ] Incorporer les décisions retenues dans les sources canoniques M0.
- [ ] Vérifier les documents sources publiables après revue de confidentialité.

## Critère de preuve

Une décision contient un owner, une date et une référence d'approbation explicite. Un résultat de test contient un SHA, l'environnement et le contrôle réellement exécuté. Aucune valeur `PASS`, `GO`, `QUALIFIED` ou `ACCEPTED` n'est attribuée ici.
