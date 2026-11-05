# G1 - Précontrôle local des secrets dans l'historique Git

> **Nature** : outil local de détection et de triage, pas un certificat de sécurité ni une autorisation d'archiver.
> **Code** : `scripts/g1_history_secret_preflight.py`.
> **Baseline historique** : `a523d9c61c30ef41afe3bc9cf0723beafe3c2d38`.
> **Gate** : `G1=PENDING`, `ARCH-02=BLOCKED` jusqu'à conservation indépendante et décision humaine.

## Risque traité

Le contrôle G1 éphémère prouve que le bundle Git est restaurable. L'outil de custody AES-256-GCM prépare une copie chiffrée. Aucun de ces deux résultats n'établit que l'historique ne contient pas de credentials ou de clés privées. Or un secret compromis reste sensible même dans une archive chiffrée, particulièrement au moment du déchiffrement ou lors du transfert.

Le nouveau précontrôle examine **les commits et blobs atteignables depuis le SHA historique**. Les motifs détectés comprennent les en-têtes de clés privées PEM, certains formats de tokens GitHub, AWS, OpenAI et Slack, ainsi que des affectations de variables sensibles. Les correspondances sont des **signaux non confirmés**, parfois des faux positifs.

Il ne publie **jamais** une valeur de secret, un extrait de source, un chemin de fichier ou l'identifiant d'un objet Git. Le rapport agrégé contient seulement des compteurs par famille, le SHA de la baseline et l'état des limites de scan. Il est écrit dans un répertoire local privé (0700) avec permissions de fichier 0600, hors du dépôt Git.

## Utilisation sur un poste approuvé

Préconditions : clone complet du dépôt sur une machine de confiance ; aucun transfert vers un service inconnu, aucun upload d'archive et aucune clé dans le dépôt. Le scan n'est pas lancé automatiquement par GitHub Actions sur l'historique réel : la CI ne teste que des dépôts synthétiques.

```bash
umask 077
mkdir -p "$HOME/.pyprojectkit-g1-audit"
chmod 700 "$HOME/.pyprojectkit-g1-audit"
python scripts/g1_history_secret_preflight.py \
  --repository /chemin/vers/clone-complet/pyprojectkit \
  --baseline-sha a523d9c61c30ef41afe3bc9cf0723beafe3c2d38 \
  --private-report "$HOME/.pyprojectkit-g1-audit/history-audit.json"
```

Le chemin `/chemin/vers/clone-complet/pyprojectkit` est un exemple à remplacer localement. Un fichier de rapport déjà présent n'est jamais écrasé. Le stdout ne contient que l'état de traitement, sans compteurs ni valeurs.

## Interprétation

- `PATTERNS_DETECTED_REVIEW_REQUIRED` : signal de risque détecté ; examen humain privé indispensable, rotation/révocation des credentials confirmés auprès des fournisseurs compétents.
- `NO_PATTERN_HITS_NOT_A_CLEAN_BILL` : aucun motif couvert n'a été détecté ; **cela ne prouve pas l'absence de secrets**.
- `oversized_objects_not_scanned > 0` : inspection incomplète des objets volumineux ; traitement distinct nécessaire avant décision G1.
- Échec Git, historique superficiel, quota, format incorrect : aucune preuve de scan valide. Rejouer localement après correction.

Les résultats d'un audit ne sont pas une autorisation automatique d'ARCH-02. Aucun compteur ne doit être copié avec des extraits ou des identifiants exploitables dans une issue publique.

## Limites explicites

Ce scan ne couvre **pas** les refs historiques non atteignables de la baseline, les reflogs, données non suivies, objets LFS externes, sous-modules, secrets GitHub Actions, credentials de la plateforme, métadonnées GitHub (issues/PR), stockage externe et formats de secrets qui ne correspondent pas aux regex intégrées. Il ne détecte pas nécessairement tous les secrets et peut générer des faux positifs. L'historique réellement embarqué par un bundle doit correspondre au commit et à la politique d'inclusion déclarés.

## Critères de suite G1

1. Effectuer l'audit hors GitHub Actions et conserver uniquement le rapport agrégé dans un espace privé.
2. Faire examiner en privé les catégories suspectes et documenter les rotations si nécessaire.
3. Nommer effectivement le gardien, la destination et la politique de rétention des copies.
4. Créer ensuite, sous mandat d'archivage explicite, la copie chiffrée indépendante avec clé séparée, et tester sa restauration depuis cette copie.
5. Obtenir une décision G1 humaine traçable. La CI synthétique ne peut signer ni G1 ni G2.

**Ne jamais déposer la clé, le bundle, le ciphertext, des tokens ou des extraits de secrets dans le dépôt, les artefacts CI ou les issues.**
