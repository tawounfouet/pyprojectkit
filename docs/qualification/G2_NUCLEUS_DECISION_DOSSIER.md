# G2 - NUCLEUS : dossier de décision soumis, non signé

> Statut officiel : `G2=PENDING` | Recommandation non autoritative : `CONDITIONAL_TECHNICAL_READY` | Date : 2026-11-05.

## Objet de décision

Qualifier **uniquement** le noyau InMemory additif `pyprojectkit_next`, sa première vertical slice Project/Task, les tests et les ports. Aucun remplacement des APIs legacy, aucune persistance durable, aucun accès production, aucune publication, aucun archivage implicite.

## Tableau des preuves

| Groupe | Position technique | Preuve ou réserve |
|---|---|---|
| ARCH-03 | Matrice PAR-00..10 créée, classification fidèle | `docs/contracts/M0_M1_M2_BEHAVIORAL_PARITY_MATRIX.md` |
| ARCH-04 | Bootstrap additive présent, wheel installable, CI multi-Python | `docs/qualification/ARCH_04_BOOTSTRAP_VALIDATION.md` ; CI à HEAD exact |
| ARCH-05 | Noyau mémoire et cas métier testés | `docs/qualification/ARCH_05_VS_REBOOT_01_IMPLEMENTATION_REPORT.md` |
| Non-divulgation | Correctif sur ressource cachée/absente et tests négatifs | `tests/test_reboot_g2_security_contract.py` |
| Legacy | Sources historiques conservées, tests M0/M1/M2 à rejouer | Baseline `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38` et HEAD cible après merge |
| Sécurité d'entrée | **PARTIAL** | `ActorContext` est constructible par un appelant : vrai host vérifiant non implémenté |
| G1 | **BLOCKED** | Pas de bundle/restauration indépendante attestée |
| Governance | **BLOCKED** | Reviewer G2 indépendant non nommé ; propriétaire seul mainteneur, HD-08 reporte ce contrôle |
| Main protection | **BLOCKED** | `main` non protégée, rulesets vides au dernier contrôle |
| Releases | **BLOCKED** | Licence précise non adoptée, pas de publication PyPI |

## Conclusions strictes

- `RB-AC-01..06` et `08` possèdent des tests ciblés sur la slice ; `07` demeure partiel, `09` exige la CI du SHA courant, `10` exige le dossier de preuve et une validation formelle. Les valeurs détaillées sont dans le rapport ARCH-05.
- Le caractère expérimental du noyau n'annule pas la nécessité de préserver M0 (`HD-05=PRESERVE`) et la répartition M1/M2 différés.
- `PAR-04/05` sont partiels, `PAR-06..10` différés ; une réussite du test différentiel M0 ne démontre pas toutes les API publiques.
- Les PR techniques et CI ne donnent ni `G1=GO`, ni `G2=GO`, ni `G3=GO`, ni autorisation d'ARCH-02.

## Décision humaine à enregistrer séparément

| Champ | Valeur |
|---|---|
| Autorité décisionnaire | `À DÉSIGNER / NON SIGNÉ` |
| Reviewer indépendant | `REPORTÉ (HD-08)` |
| Avis indépendant | `PENDING` |
| G2 validé | `NON` |
| Handoff ARCH-06 | Contrats de tests RED / analyse possible ; **code SQLite non autorisé par ce dossier** |
| Date et signature | `AUCUNE` |

## Conditions avant une clôture G2 effective

1. Rejouer CI complète et VS01 au SHA final avec résultats `success`, artefacts et logs.
2. Corriger ou accepter formellement les limites `SEC-RB-01/04/10/12`, `RB-AC-07/10`, avec ownership et scope exact.
3. Tester une restauration de l'archive legacy indépendante, assigner un gardien, obtenir G1 valide (hors périmètre ARCH-03..05).
4. Mettre en place ou obtenir une exception formelle de protection de `main` ; corriger issue #19.
5. Conduire la revue G2 selon la gouvernance adoptée, sans Pythos signé comme reviewer humain indépendant.

**Verdict documentaire de Pythos :** dossier prêt pour examen, gate **PENDING**. Tout `GO_LIMITED_NUCLEUS` serait une décision humaine future et bornée, sans substitution ou release.
