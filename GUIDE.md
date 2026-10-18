# GUIDE — WhatsApp-Courses

Ce guide explique comment installer, configurer et utiliser WhatsApp-Courses avec Docker et Google Drive.

## 1. Architecture

Le projet utilise trois emplacements principaux dans le conteneur :

| Chemin dans le conteneur | Rôle |
|---|---|
| `/app` | Code Python et dépendances |
| `/config` | Configuration Google Drive, credentials OAuth et jeton d'accès |
| `/data` | Documents entrants et documents déjà transférés |

Les données persistantes sont montées depuis la machine hôte. Supprimer le conteneur ne doit donc pas supprimer les données conservées dans ces répertoires.

## 2. Prérequis

- Linux, macOS ou Windows avec un environnement compatible Docker.
- Docker Engine ou Docker Desktop.
- Un compte Google disposant d'un accès à Google Drive.
- Un projet Google Cloud avec l'API Google Drive activée.
- Un client OAuth de type **Desktop app**.

## 3. Récupérer le projet

```bash
git clone https://github.com/Elouzi-art/WhatsApp-courses.git
cd WhatsApp-courses
```

Si le dépôt est privé ou si son nom change, utilise l'URL réelle du dépôt.

## 4. Configurer Google Cloud et OAuth

Si tu disposes déjà d'un projet Google Cloud configuré, vérifie ces éléments au lieu de recommencer toute la procédure.

1. Ouvre la [Google Cloud Console](https://console.cloud.google.com/).
2. Sélectionne ou crée un projet.
3. Active **Google Drive API** dans la bibliothèque des API.
4. Configure l'écran de consentement OAuth demandé par Google.
5. Crée un identifiant OAuth de type **Desktop app**.
6. Télécharge le fichier JSON des credentials.

Pour la procédure officielle, consulte la [documentation Google Drive API](https://developers.google.com/drive/api/guides/about-sdk).

Le fichier téléchargé doit être nommé `credentials.json`.

## 5. Préparer les répertoires persistants

Crée les répertoires utilisés par Docker :

```bash
mkdir -p "$HOME/.config/whatsapp-courses"
mkdir -p "$HOME/.local/share/whatsapp-courses/incoming"
mkdir -p "$HOME/.local/share/whatsapp-courses/uploaded"

chmod 700 "$HOME/.config/whatsapp-courses"
chmod 700 "$HOME/.local/share/whatsapp-courses"
```

Place le fichier OAuth téléchargé dans :

```text
~/.config/whatsapp-courses/credentials.json
```

Sur Linux, tu peux utiliser cette commande depuis le répertoire où se trouve le fichier téléchargé :

```bash
install -m 600 \
  "/chemin/vers/credentials.json" \
  "$HOME/.config/whatsapp-courses/credentials.json"
```

Remplace `/chemin/vers/credentials.json` par le chemin réel du fichier.

Le jeton OAuth généré par l'application sera conservé dans le répertoire de configuration. Ne publie jamais ces fichiers.

## 6. Construire l'image Docker

Depuis la racine du projet :

```bash
docker build -t whatsapp-courses:local .
```

Vérifie que l'image existe :

```bash
docker image ls whatsapp-courses
```

## 7. Lancer l'application

```bash
docker run --rm -it \
  --name whatsapp-courses \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1:8765:8765 \
  --mount "type=bind,source=$HOME/.config/whatsapp-courses,target=/config" \
  --mount "type=bind,source=$HOME/.local/share/whatsapp-courses,target=/data" \
  whatsapp-courses:local
```

Explications :

- `--rm` supprime le conteneur à la sortie, mais pas les données conservées dans les répertoires montés.
- `-it` permet d'utiliser le menu interactif.
- `--user "$(id -u):$(id -g)"` permet d'écrire dans les volumes avec l'identité de l'utilisateur hôte.
- `127.0.0.1:8765:8765` expose le port OAuth uniquement sur la boucle locale.
- `/config` conserve la configuration Google.
- `/data` conserve les documents entrants et traités.

Si le port `8765` est déjà utilisé, arrête le service qui l'occupe ou adapte le port hôte et la configuration OAuth en conséquence.

## 8. Première configuration

Dans le menu de l'application :

1. Choisis l'option de configuration Google Drive.
2. Si nécessaire, ouvre l'URL OAuth affichée dans ton navigateur et autorise l'accès demandé.
3. Sélectionne un dossier Google Drive existant ou crée un dossier de destination.
4. Vérifie la liste des modules proposés et adapte-la à tes cours.
5. Quitte ou reviens au menu principal selon les options affichées.

La configuration est conservée dans `/config`, donc elle reste disponible au prochain lancement.

## 9. Transférer des documents

Copie les documents à traiter dans :

```text
~/.local/share/whatsapp-courses/incoming/
```

Exemple :

```bash
cp "$HOME/Downloads/mon-cours.pdf" \
  "$HOME/.local/share/whatsapp-courses/incoming/"
```

Sur un système francophone, le dossier peut s'appeler `Téléchargements` plutôt que `Downloads`.

Vérifie les fichiers :

```bash
ls -lh "$HOME/.local/share/whatsapp-courses/incoming/"
```

Lance l'application et choisis l'option d'envoi des documents. Sélectionne ensuite le module correspondant.

Après un transfert réussi, le fichier doit être déplacé dans :

```text
~/.local/share/whatsapp-courses/uploaded/
```

Vérifie également le dossier de destination dans Google Drive.

## 10. Modifier les modules

Les modules sont des catégories configurables, par exemple :

```text
UML, FRONT, EN, AGILE, GOV, MOBILE, CRYPT
```

Adapte cette liste aux noms de tes cours. Évite les noms ambigus et garde une convention stable pour faciliter l'organisation.

L'application crée les sous-dossiers correspondants dans le dossier de destination Google Drive lorsqu'ils sont nécessaires.

## 11. Persistance et sauvegarde

Les données importantes se trouvent dans :

```text
~/.config/whatsapp-courses/
~/.local/share/whatsapp-courses/
```

Pour sauvegarder ces données, arrête d'abord l'application puis copie ces répertoires vers un emplacement sûr. Le répertoire de configuration contient des secrets OAuth : protège sa sauvegarde et ne la partage pas publiquement.

## 12. Dépannage

### Aucun fichier trouvé

Vérifie que les documents se trouvent dans le répertoire `incoming` de la machine hôte, et non dans le dossier du code source :

```bash
ls -lah "$HOME/.local/share/whatsapp-courses/incoming/"
```

### Erreur OAuth

- Vérifie la présence de `credentials.json`.
- Vérifie que Google Drive API est activée.
- Vérifie que le client OAuth est de type Desktop app.
- Vérifie les messages affichés dans le terminal.
- Si le jeton est révoqué, relance le processus d'autorisation selon les indications de l'application.

Ne supprime pas le jeton sans raison : cela peut nécessiter une nouvelle autorisation.

### Erreur de permission

Vérifie les droits sur les dossiers persistants et le propriétaire des fichiers. Évite de lancer systématiquement le conteneur en tant que `root`.

### Le port OAuth est occupé

Vérifie quel processus utilise le port :

```bash
ss -ltnp | grep ':8765'
```

Arrête le processus concerné ou adapte la configuration de port de manière cohérente.

### Le fichier n'apparaît pas dans Google Drive

Vérifie le résultat de l'opération dans le terminal, le dossier de destination configuré et le dossier `uploaded`. Ne considère pas un fichier comme transféré tant que l'application n'a pas confirmé le succès.

## 13. Roadmap : automatisation WhatsApp

L'application actuelle traite les documents déjà présents dans `incoming` et utilise un menu interactif. Elle ne récupère pas automatiquement les discussions WhatsApp.

L'évolution envisagée est la suivante :

1. Intégrer l'API officielle WhatsApp Business Cloud.
2. Recevoir les événements autorisés via un webhook HTTPS.
3. Identifier les messages contenant des documents.
4. Télécharger les médias autorisés et les enregistrer dans le répertoire local `incoming`.
5. Ajouter une tâche automatisée qui vérifie le répertoire toutes les 30 secondes.
6. Traiter les nouveaux fichiers sans interaction manuelle.
7. Enregistrer les résultats et éviter les transferts en double.

Cette évolution demandera du développement supplémentaire : le programme actuel est interactif, et une exécution périodique ne suffit pas à elle seule à le rendre entièrement automatique.

Consulte la documentation de la [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp/cloud-api/overview/) et des [webhooks WhatsApp](https://www.postman.com/meta/whatsapp-business-platform/folder/tduohwq/webhook-payload-reference).

## 14. Sécurité

- Ne publie jamais `credentials.json`, `token.json`, de jetons d'accès ou de données personnelles.
- N'ajoute pas de fichiers de cours au dépôt Git.
- Limite les permissions des dossiers contenant des secrets.
- Vérifie les fichiers reçus avant leur traitement automatique.
- Utilise uniquement des comptes et documents auxquels tu es autorisé à accéder.
- Pour une future automatisation, valide les signatures des webhooks et traite les événements de façon idempotente afin d'éviter les doublons.

## 15. Limites actuelles

- Le transfert nécessite actuellement une intervention dans le menu.
- Les documents doivent être placés localement dans `incoming`.
- La réception automatique depuis WhatsApp n'est pas encore implémentée.
- La tâche périodique de 30 secondes n'est pas encore implémentée.
- La licence du projet reste à choisir.
