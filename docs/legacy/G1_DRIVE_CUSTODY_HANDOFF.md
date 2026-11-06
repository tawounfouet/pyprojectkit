# G1 - Décision de coffre Google Drive et gardien

> Décision explicite du propriétaire du 6 novembre 2026.
> Statut : `DRIVE_FOLDER_CREATED / OWNER_ONLY_PERMISSIONS_VERIFIED / NO_ARCHIVE_TRANSFER`.
> **G1=PENDING**, **G2=PENDING**, **ARCH-02=BLOCKED**.

## Décisions actées

- Destination retenue : **Google Drive privé** pour la copie Git *déjà chiffrée* par l'utilitaire `scripts/g1_encrypted_custody.py`.
- Gardien principal : **propriétaire du projet PyProjectKit**.
- Clé : **support distinct de Google Drive** et du dépôt GitHub ; aucun mot de passe, clé ou secret dans ce fichier.
- Aucun transfert d'une archive réelle n'a été autorisé par cette décision. Le transfert exige un audit local préalable et un protocole d'opération validé.

## Vérification de préparation

Un dossier dédié a été créé à la racine de l'espace Drive personnel. L'API de métadonnées a indiqué : `shared=false`, une permission `user/owner`, aucune permission `anyone`, `group` ou `domain`. **L'identifiant et l'URL du dossier restent hors du dépôt public** ; les permissions doivent être revérifiées juste avant et après une éventuelle copie.

Le dossier ne prouve pas que le contenu d'une future archive sera chiffré côté client ni que l'environnement du gardien est sécurisé. Les réglages de partage ne remplacent pas un chiffrement authentifié indépendant.

## Procédure opérationnelle à venir, non exécutée

1. Exécuter `g1_history_secret_preflight.py` dans un clone complet sur une machine approuvée, hors CI, et vérifier manuellement les alertes. Révoquer ou faire tourner tout secret effectivement compromis.
2. Vérifier l'intégrité de la référence legacy ; confirmer politique d'objets historiques, LFS éventuel et métadonnées GitHub nécessaires.
3. Générer une clé AES-256 sur le poste approuvé et la conserver séparément via un gestionnaire de secrets ou support hors Drive ; organiser les accès de secours et la récupération.
4. Chiffrer localement le bundle avec AES-256-GCM, conserver le manifeste et le ciphertext, **jamais le bundle en clair**.
5. Avant transfert, contrôler à nouveau que le dossier Drive n'est pas partagé. Déposer **uniquement le ciphertext** et son manifeste non sensible, après autorisation distincte. Vérifier les permissions des fichiers uploadés.
6. Récupérer la copie depuis Drive sur un second environnement approuvé, fournir la clé par le canal séparé et restaurer le commit/tree exact ; conserver uniquement un rapport d'intégrité non sensible.
7. Faire prononcer G1 par l'autorité humaine, puis instruire G2 avec une revue distincte.

## STOP immédiat

Ne pas déposer le bundle brut, clé AES, phrase de passe, tokens, logs de secrets, rapports sensibles, captures de données client ou base SQLite réelle sur Drive. Ne pas considérer l'existence d'un dossier privé comme `G1=GO`. La protection de `main` est une action séparée de l'issue GitHub #19.
