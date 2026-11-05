# PyProjectKit G1 - Coffre chiffré hors dépôt et restauration indépendante

**Version :** 0.1.0, 2026-11-05. **Statut :** outil proposé et testé sur dépôts synthétiques. `G1=PENDING`.

## Pourquoi cet outil ?

Le workflow `legacy-g1-restore-drill.yml` a démontré l'extraction et la restauration **éphémères** de `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`. Le chiffrement et la conservation hors dépôt sont deux propriétés différentes. Ce script ne choisit pas le gardien et ne peut pas certifier qu'un stockage est indépendant, ni que les secrets présents dans l'historique ont été traités.

## Frontières et interdictions

- L'exécution réelle de `seal` est **bloquée par la gouvernance** tant que le gardien humain et la destination privée ne sont pas désignés et que les secrets historiques n'ont pas été examinés. Les commandes ci-dessous sont un runbook **pour un opérateur dûment autorisé**, pas une trace d'exécution.
- Aucun bundle, key file ou ciphertext ne doit être ajouté à Git, à une issue, aux Actions Artifacts, aux logs ou à cette conversation.
- Exécution uniquement sur un poste de confiance, dans un environnement isolé, avec les répertoires coffre et clé séparés physiquement ou administrativement. Pas de données réelles de tiers sans autorisation et politique de rétention.
- La clé est symétrique AES-256 de 32 octets. Si elle est perdue, l'archive est irrécupérable ; si elle est copiée avec le ciphertext, le chiffrement ne protège plus en cas de perte commune.
- L'enveloppe AES-256-GCM lie cryptographiquement le SHA du commit historique, l'arbre Git, le SHA du bundle, sa taille, l'horodatage et l'état de custody dans l'AAD. Toute modification du ciphertext ou des champs authentifiés échoue.
- La taille est volontairement bornée à 64 MiB et l'outil charge le bundle en mémoire. Pour une archive supérieure, **STOP**, adopter une solution streaming éprouvée. Les fichiers temporaires peuvent laisser des traces récupérables sur certains systèmes de fichiers : préférer un stockage temporaire chiffré ou une mémoire temporaire contrôlée.
- Les permissions POSIX 0700 (répertoires) et 0600 (clé et archives) sont exigées. Des symlinks et écrasements sont refusés.
- Un `git bundle` ne contient pas automatiquement issues, PR, protections, Actions, règles, secrets GitHub, sous-modules et objets Git LFS. Un dossier de métadonnées autonome et son contrôle sont nécessaires avant G1.

## Dépendances opérateur

Python 3.12+ et Git. Installer **hors du package runtime** : `python -m pip install 'cryptography>=45,<47'`. Tester cet outil hors ligne après installation.

## Exemple pour un opérateur autorisé uniquement

Les chemins sont des exemples. **Ne pas les réutiliser** sans contrôle des emplacements et désignation du gardien.

```bash
# Sur poste fiable ; sources dans un clone local complet.
# Créer les deux répertoires dans des emplacements contrôlés et DISTINCTS.
mkdir -m 700 -p /private/key-custody /private/encrypted-archive
python scripts/g1_encrypted_custody.py generate-key --key-file /private/key-custody/g1.key
python scripts/g1_encrypted_custody.py seal \
  --repository /private/pyprojectkit-clone \
  --baseline-sha a523d9c61c30ef41afe3bc9cf0723beafe3c2d38 \
  --output-dir /private/encrypted-archive \
  --key-file /private/key-custody/g1.key \
  --acknowledge-sensitive-history

# Copier le ciphertext ET son manifeste sur le stockage OFFSITE choisi.
# Puis, sur un AUTRE poste de restauration avec une clé récupérée séparément :
python scripts/g1_encrypted_custody.py verify \
  --archive-dir /private/restored-offsite-copy \
  --key-file /private/independent-key-custody/g1.key
```

**Note :** `seal` et `verify` retournent toujours `g1_gate=PENDING`, même en cas de succès cryptographique. L'outil n'enregistre pas la localisation d'un coffre réel, ne désigne pas un gardien et ne prétend pas gérer des clés dans un HSM/KMS. L'exemple contient une sauvegarde du seul commit et de ses ancêtres, pas toutes les références de `main`.

## Preuves pour une décision G1 future

1. Gardien et suppléant identifiés, droits d'accès documentés et expiration/rétention adoptée par l'autorité humaine.
2. Analyse des secrets et décisions de rotation/retrait ; validation de la classification des données.
3. Clé générée et sauvegardée séparément selon une politique approuvée, restauration de clé testée hors machine.
4. Copie chiffrée transférée vers un coffre privé indépendant avec ACL, immutabilité ou versionnement et durée de rétention.
5. Exercice `verify` exécuté **sur une copie depuis ce coffre** et sur un second poste ; vérifier SHA, arbre, `git fsck` et version du chiffrement.
6. Métadonnées GitHub nécessaires inventoriées et conservées sans publier des secrets.
7. Procès-verbal signé humainement avec contrôle indépendant applicable, `G1` prononcé explicitement ; `ARCH-02` toujours sous mandat séparé.

## Statuts

| Capacité | État visé par la PR | Ce qu'elle ne prouve pas |
|---|---|---|
| Chiffrement authentifié | Tests `AESGCM` sur Git synthétique | Aucune archive legacy réelle conservée |
| Restauration déchiffrée | Tests clone + fsck synthétiques | Aucune preuve depuis un coffre tiers |
| Non-divulgation | Aucun fichier secret dans Git/CI | Pas un audit exhaustif de l'historique |
| G1 | `PENDING` | Ni validation automatique, ni autorisation d'ARCH-02 |
| G2 | `PENDING` | Aucun reviewer indépendant ou AuthN réel |
