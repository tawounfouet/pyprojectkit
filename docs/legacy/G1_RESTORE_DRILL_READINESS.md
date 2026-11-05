# ARCH-02 / G1 - Exercice de restauration Git éphémère

> Nature : précontrôle technique reproductible ; **pas** une archive sous garde.
> Base de référence legacy : `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`.
> G1 : `PENDING` tant que conservation indépendante, chiffrement, gardien et preuve hors runner ne sont pas attestés.

## Quel problème est traité ?

La simple présence de l'historique dans GitHub ne démontre pas qu'un `git bundle` est complet, intègre et restaurable. La tâche `g1-precheck` exécute un contrôle dans un runner GitHub Actions à accès Git en lecture seule :

1. Checkout de l'historique complet (`fetch-depth: 0`).
2. Contrôle de présence et de nature du commit historique exact.
3. Clone local isolé, création d'une référence locale au commit historique et génération d'un `git bundle` dans un dossier temporaire.
4. Vérification du bundle, restauration dans un **second dépôt** et comparaison du commit et de la racine de l'arbre Git.
5. `git fsck --full`, empreinte SHA-256 du bundle, puis destruction du dossier temporaire en fin de script.
6. Affichage d'un bilan JSON réduit, ne contenant aucun fichier ni secret du dépôt.

Les tests Python construisent leurs propres dépôts Git synthétiques et vérifient les refus de SHA absent, SHA non canonique et clone superficiel.

## Frontière de sécurité

- **Aucun bundle ni archive de l'historique ne doit être téléversé dans les artifacts ou les logs GitHub**, en particulier avant une revue des secrets historiques et le choix du coffre privé chiffré.
- Le token GitHub Actions a `contents: read` et `persist-credentials: false`.
- Les refs créées sont locales au clone de travail du runner. Aucune branche, tag ni release distant n'est modifié par ce précontrôle.
- Le contrôle n'exécute pas de données client, de migration ni de suppression de legacy.
- Les éventuels sous-modules, éléments LFS ou métadonnées GitHub hors du dépôt (issues, protections, règles, releases, Actions, secrets) ne sont **pas** sauvegardés par un simple bundle. Leur inventaire et leur plan de conservation doivent rester séparés.

## Conditions restantes pour un G1 formel

- Désignation effective d'un gardien humain et d'une destination privée chiffrée (HD-03) ; règles d'accès, rétention et clés.
- Inventaire des secrets et examen de l'historique, avant tout transfert de contenu Git.
- Production **en dehors des CI publiques** d'une véritable sauvegarde conservée avec vérification indépendante et récupération après rotation/perte de clé.
- Conservation des métadonnées GitHub nécessaires (issues/PR, réglages, gates et statut des checks) avec une politique propre.
- Procès-verbal de restauration indépendante, SHA manifest, décision et revue humaine selon la politique applicable.

**Conclusion :** `EPHEMERAL_GIT_RESTORE_VERIFIED` prouvera la faisabilité technique de l'extraction/restauration dans la CI seulement. Il ne signifie jamais `G1=GO`, `ARCH-02=EXECUTED`, `G2=APPROVED` ou droit de retirer les sources legacy.
