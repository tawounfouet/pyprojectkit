# ARCH-06 - Contrat expérimental de reprise après résultat de commit ambigu

> Statut : `SIMULATOR_VERIFIED / MEMORY_ONLY / NOT_SQLITE / G3_PENDING`.
> Références : plan ARCH-06/ARCH-07, §5.6 et `RS-AC-09`; `11_PYPROJECTKIT_ERROR_MODEL_AND_FAILURE_SEMANTICS_V2.md`; `ARCH06_PERSISTENCE_CONTRACT_V1_CANDIDATE.md`.
> Implémentation : `src/pyprojectkit_next/recovery.py` ; tests : `tests/test_arch06_ambiguous_commit_simulation.py`.

## 1. Problème traité

Une commande peut être validée par le support puis perdre son accusé de réception. Le client ne doit **ni supposer un rollback, ni annoncer un succès sans preuve, ni retenter aveuglément une écriture non idempotente**. `IdempotencyConflict` (sous-classe de `Conflict`, code `IDEMPOTENCY_CONFLICT`) signale une réutilisation de clé avec intention divergente ; `CommitOutcomeUnknown` (code `COMMIT_OUTCOME_UNKNOWN`) signifie qu'aucun résultat sûr n'a été établi pour l'appelant. Ces deux erreurs sont distinctes.

Ce module n'est pas lié au `UnitOfWork` de production, ne réalise aucune transaction SQLite et ne constitue **pas** une outbox durable. Son journal est volatil et mono-processus. Il matérialise seulement un comportement de référence pour une future adaptation, sans promettre de disponibilité après redémarrage.

## 2. Contrat testable

| Référence | Comportement requis | Preuve actuelle |
|---|---|---|
| `C06-09.1` | L'intention comprend `operation_id`, `actor_id`, `scope` et empreinte canonique de la commande et de ses événements | Tests de validation et de fingerprint |
| `C06-09.2` | La même clé avec la même empreinte renvoie le même reçu et ne duplique pas les événements | Replay idempotent, test concurrent |
| `C06-09.3` | La même clé avec un payload ou un plan d'événements différent provoque `IdempotencyConflict` | Tests de collision et code stable |
| `C06-09.4` | Un défaut avant commit n'est pas présenté comme un rollback certain | `INDETERMINATE` sans reçu, aucun retry automatique |
| `C06-09.5` | Après validation avec ACK perdu, une réconciliation positive renvoie le reçu exact | Failpoint `AFTER_COMMIT_BEFORE_ACK` |
| `C06-09.6` | La consultation d'une intention inconnue n'affirme pas que l'opération est absente | `INDETERMINATE`, `safe_to_retry=False` |
| `C06-09.7` | Les collisions d'opérations sont isolées par sujet et scope | Trois identités logiques distinctes |
| `C06-09.8` | Un état ambigu ne peut être écrasé par un nouveau payload ou une nouvelle soumission aveugle | Tests de garde sur intentions inconnues |

La fonction `CommitIntent.bind()` calcule SHA-256 à partir des octets canoniques de la commande et de la liste ordonnée des noms d'événements, avec un séparateur de version et des préfixes de longueur. **Le producteur doit construire la représentation canonique de la commande** ; le hash ne constitue pas une signature ni une preuve d'authentification. `actor_id` et `scope` restent fournis par un hôte attesté, non par un client non fiable.

## 3. Fenêtres de panne et réponses

| Injecteur | Mutation dans le simulateur | Réponse de la tentative | Réconciliation |
|---|---|---|---|
| `NONE` | État et reçu consignés une fois | `CommitReceipt` | `COMMITTED` |
| `BEFORE_COMMIT` | Pas de mutation, intention marquée incertaine | `CommitOutcomeUnknown` | `INDETERMINATE` ; pas de replay automatique |
| `AFTER_COMMIT_BEFORE_ACK` | État et reçu consignés dans une section critique mémoire | `CommitOutcomeUnknown` | `COMMITTED` avec reçu original |
| Intention jamais observée | Aucune preuve | Aucune tentative | `INDETERMINATE` et non « FAILED » |

Le simulateur ne fournit **aucune** preuve positive de `NOT_COMMITTED`. Une absence de reçu ne suffit pas. Un futur backend durable devra définir une transaction qui enregistre ensemble les mutations, l'intention, son reçu et les événements/outbox, puis une API d'interrogation autorisée après redémarrage. Un opérateur ne peut pas forcer `safe_to_retry=True` dans ce simulateur.

## 4. Décisions encore ouvertes pour SQLite et G3

- Rétention et purge des intentions : **non implémentées**. Décider durée, politique de reprise après expiration et namespace inter-tenant.
- Persistance des reçus et des événements dans **la même transaction durable** : **non implémentée**.
- Résultat `NOT_COMMITTED` définitivement prouvé par le backend : **non implémenté**.
- Crash au milieu d'un COMMIT SQLite, blocage, reconnexion interprocessus et réconciliation après redémarrage : **non testés**.
- Autorisation par un hôte réel et non-divulgation des informations sur les intentions d'autres propriétaires : **hors périmètre du simulateur**.
- Intégration du port `UnitOfWork.commit()` au mécanisme d'intentions : **non effectuée**, décision de contrat à prendre sous les gates G1/G2.
- La commande publique M0 n'expose pas encore d'identifiant d'intention ; ne pas déclarer l'idempotence globale du noyau.

**Verdict : oracle synthétique de `RS-AC-09` préparé ; critère `RS-AC-09=NOT_QUALIFIED_SQLITE`, `G3=PENDING`.**
