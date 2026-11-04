# ADR-M2-08 - Manifeste Q-M2 et gate humain

- **Statut** : PROPOSED - revue humaine obligatoire
- **Date** : 2026-11-04
- **WorkItem** : M2-12

## Contexte
Les statuts de tests, les déclarations agentiques, les preuves d'un commit et l'autorisation humaine d'adopter un pilote sont des faits distincts.

## Décision candidate
- `AcceptanceEvidence` contient un AC `027..037`, un code SHA Git 40 caractères, un lien vers CI, des nœuds de tests, un environnement, résultats observés, limites et risques.
- `build_qualification_dossier` refuse les AC manquants/dupliqués et les SHA discordants. Il sépare `assessed_count`, `passed_count`, `failed_count`, `partial_count` et `unassessed_count`.
- Un PASS n'est pas déduit de la simple présence d'une méthode de test. Le rapport doit être complété depuis des résultats CI **effectivement vérifiés**.
- Un AC bloquant `PARTIAL`, `FAIL` ou `NOT_EXECUTED` produit `NO_GO_RECOMMENDED` pour l'autorisation globale, sans effacer les preuves partielles.
- Une matrice de onze AC tous PASS peut produire `TECHNICAL_PASS_REPORTED`, jamais un `GO` humain.
- `human_gate=PENDING` et `adoption_decision=NOT_GRANTED` sont des constantes du calcul de dossier. Une future décision réelle doit être consignée par un mécanisme et une autorité distincts, hors du DTO agent et de la CLI.
- Tests sur deux versions Python, wheel isolée, suites M0/M1/M2-A/B/C et SHA du candidat identifiés.
- Aucune fusion de branche, publication PyPI, exploitation d'un dépôt réel ni promotion automatique.

## Limites
Le lien GitHub et le SHA fournis au manifeste sont des références, pas une vérification cryptographique ni une attestation externe. La revue indépendante humaine et l'acceptation des risques demeurent à obtenir.

## Preuves
`tests/test_m2c_qualification.py`, rapport de qualification sur CI exact, observations de gates et décision humaine explicitement en attente.
