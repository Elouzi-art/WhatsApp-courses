# WhatsApp-Courses — User Guide

This guide explains how to configure, run, and troubleshoot WhatsApp-Courses on a Linux system using Docker.

## Table of Contents

- [1. Overview](#1-overview)
- [2. Requirements](#2-requirements)
- [3. Project Setup](#3-project-setup)
- [4. Configure Google Drive API](#4-configure-google-drive-api)
- [5. Configure Persistent Storage](#5-configure-persistent-storage)
- [6. Build the Docker Image](#6-build-the-docker-image)
- [7. Run the Application](#7-run-the-application)
- [8. First-Time Authorization](#8-first-time-authorization)
- [9. Configure the Destination and Modules](#9-configure-the-destination-and-modules)
- [10. Upload Course Documents](#10-upload-course-documents)
- [11. Data Persistence](#11-data-persistence)
- [12. Troubleshooting](#12-troubleshooting)
- [13. Security Recommendations](#13-security-recommendations)
- [14. Current Limitations](#14-current-limitations)

## 1. Overview

WhatsApp-Courses is a Dockerized Python application that helps organize course documents and upload them to Google Drive.

The current workflow is interactive:

1. Place documents in a local staging directory.
2. Launch the application.
3. Configure the Google Drive destination and course modules.
4. Select documents for upload through the terminal menu.
5. Store successfully uploaded documents in a separate local directory.

The application keeps its configuration and user data outside the Docker image using persistent bind mounts.

**Important:** automatic WhatsApp message retrieval, scheduled processing, and WhatsApp Business Cloud API integration are not currently implemented.

## 2. Requirements

Before starting, ensure that you have:

- Linux, macOS, or another Docker-compatible environment.
- Docker Engine or Docker Desktop.
- A Google account.
- A Google Cloud project with the Google Drive API enabled.
- OAuth 2.0 credentials for a Desktop application.
- Git, if you intend to clone the repository.

Check that Docker is available:

```bash
docker --version
docker info
```

If `docker info` fails, verify that the Docker service is running and that your account has permission to access the Docker daemon.

## 3. Project Setup

Clone the repository:

```bash
git clone https://github.com/Elouzi-art/WhatsApp-courses.git
cd WhatsApp-courses
```

If the repository has a different URL, replace the example above with the actual repository URL.

Verify the expected project files:

```bash
ls -la
```

The project should include files such as:

```text
Dockerfile
main.py
requirements.txt
.dockerignore
.gitignore
.env.example
README.md
GUIDE.md
```

The `assets/` directory may contain the README banner and other project images.

## 4. Configure Google Drive API

The application uses Google's OAuth 2.0 authorization flow to access Google Drive.

### 4.1 Create a Google Cloud project

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project or select an existing one.
3. Open **APIs & Services → Library**.
4. Search for **Google Drive API**.
5. Enable the API for your project.

### 4.2 Configure the OAuth consent screen

Configure the OAuth consent screen according to Google's current instructions.

If the application is in testing mode, add your Google account as a test user when required.

The available configuration options depend on the account type and the Google Cloud project settings.

### 4.3 Create OAuth credentials

1. Open **APIs & Services → Credentials**.
2. Create an OAuth client ID.
3. Select **Desktop app** as the application type.
4. Download the JSON credentials file.

The downloaded file is commonly named `client_secret_....json`. Rename it to:

```text
credentials.json
```

Do not share this file or commit it to Git.

## 5. Configure Persistent Storage

Create the host directories used by the Docker container:

```bash
mkdir -p "$HOME/.config/whatsapp-courses"
mkdir -p "$HOME/.local/share/whatsapp-courses/incoming"
mkdir -p "$HOME/.local/share/whatsapp-courses/uploaded"
```

Restrict access to the configuration directory:

```bash
chmod 700 "$HOME/.config/whatsapp-courses"
chmod 700 "$HOME/.local/share/whatsapp-courses"
```

Move the OAuth credentials file to:

```text
~/.config/whatsapp-courses/credentials.json
```

For example, if the downloaded file is in your Downloads directory:

```bash
install -m 600 \
  "$HOME/Downloads/credentials.json" \
  "$HOME/.config/whatsapp-courses/credentials.json"
```

Adjust the source path if your downloaded file has a different name or location.

The expected host directory layout is:

```text
~/.config/whatsapp-courses/
├── credentials.json
├── token.json       # Created or updated by the OAuth flow
└── config.json      # Application configuration

~/.local/share/whatsapp-courses/
├── incoming/
└── uploaded/
```

The token and application configuration are generated or updated by the application as needed.

## 6. Build the Docker Image

From the project root, build the image:

```bash
docker build -t whatsapp-courses:local .
```

Verify that the image exists:

```bash
docker image ls whatsapp-courses
```

If the build fails, check the Dockerfile, `requirements.txt`, and the build output before continuing.

## 7. Run the Application

Launch the application with persistent host directories:

```bash
docker run --rm -it \
  --name whatsapp-courses \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1:8765:8765 \
  --mount "type=bind,source=$HOME/.config/whatsapp-courses,target=/config" \
  --mount "type=bind,source=$HOME/.local/share/whatsapp-courses,target=/data" \
  whatsapp-courses:local
```

### What the command does

| Option | Purpose |
|---|---|
| `--rm` | Removes the container after it exits |
| `-it` | Enables interactive terminal input |
| `--name` | Assigns a recognizable container name |
| `--user` | Runs the process using the current host user's UID and GID |
| `--publish` | Binds the OAuth callback port to localhost |
| `--mount` | Persists configuration and data on the host |

The port mapping uses `127.0.0.1`, which restricts the published callback port to the local machine.

**Note:** the application is interactive, so keep the terminal open while using it.

## 8. First-Time Authorization

When no valid OAuth token is available, the application initiates the Google authorization flow.

1. Start the container.
2. Read the authorization URL displayed in the terminal.
3. Open that URL in a browser on the same machine.
4. Sign in to the intended Google account.
5. Review and approve the requested permissions.
6. Complete the authorization flow and return to the application terminal.

The application uses a local callback on port `8765`. If the callback fails, verify that the port is not already occupied and that the browser is running on the same machine where the container is running.

The authorization token is stored in the mounted configuration directory so that it can be reused on subsequent launches, subject to token validity and Google's authorization policies.

## 9. Configure the Destination and Modules

Use the application's interactive menu to configure the Google Drive destination.

Depending on the available menu options, you can:

- Select an existing Google Drive folder.
- Create a destination folder.
- Configure course modules.
- Save your configuration.
- Return to the menu to upload documents or update settings.

Example module categories include:

```text
UML
FRONT
EN
AGILE
GOV
MOBILE
CRYPT
```

These are examples, not mandatory categories. Adapt them to your curriculum.

## 10. Upload Course Documents

### 10.1 Add files to the staging directory

Copy documents into:

```text
~/.local/share/whatsapp-courses/incoming/
```

For example:

```bash
cp "$HOME/Downloads/example.pdf" \
  "$HOME/.local/share/whatsapp-courses/incoming/"
```

Check that the file is present:

```bash
ls -lh "$HOME/.local/share/whatsapp-courses/incoming/"
```

### 10.2 Start the application

Launch the Docker container using the command in [Section 7](#7-run-the-application).

### 10.3 Select the upload option

Use the interactive menu to choose the document upload operation. Follow the prompts to assign each document to the appropriate module.

The application uses the configured Google Drive destination and module structure to organize uploaded documents.

### 10.4 Verify the result

After a successful upload, the application moves the processed document to:

```text
~/.local/share/whatsapp-courses/uploaded/
```

Check the directory:

```bash
ls -lh "$HOME/.local/share/whatsapp-courses/uploaded/"
```

If no documents appear in `incoming/`, the application has nothing to process. Add a test document before selecting the upload option.

## 11. Data Persistence

The Docker container can be removed after use without removing files stored in the mounted host directories.

| Host path | Container path | Description |
|---|---|---|
| `~/.config/whatsapp-courses/` | `/config` | OAuth credentials, token, and application configuration |
| `~/.local/share/whatsapp-courses/incoming/` | `/data/incoming` | Documents waiting to be processed |
| `~/.local/share/whatsapp-courses/uploaded/` | `/data/uploaded` | Documents successfully uploaded |

The container's writable layer is temporary when using `--rm`. Files that need to survive container removal must be stored in the mounted directories.

## 12. Troubleshooting

### Docker permission errors

Check:

```bash
docker info
```

Verify that the Docker daemon is running and that your user has permission to access it.

### Missing OAuth credentials

Check that the credentials file exists:

```bash
ls -l "$HOME/.config/whatsapp-courses/credentials.json"
```

Ensure that the file contains the OAuth client configuration downloaded from Google Cloud.

### OAuth callback failure

Check whether the port is already in use:

```bash
ss -ltnp | grep ':8765'
```

If another process is using the port, stop it if appropriate before restarting the application.

The callback also requires a browser that can reach the local machine's callback address. Remote or containerized browser setups may need additional configuration.

### Google Drive API errors

Verify that:

- The Google Drive API is enabled in the correct project.
- You authorized the intended Google account.
- The account has access to the destination folder.
- The OAuth consent screen and test-user settings permit your account to authorize the application.
- The token has not been revoked or invalidated.

If reauthorization is necessary, stop the application and follow the application's supported token renewal or reauthorization process. Do not delete credentials or tokens indiscriminately.

### No documents found

Check the incoming directory:

```bash
find "$HOME/.local/share/whatsapp-courses/incoming/" \
  -maxdepth 1 -type f -printf '%f\n'
```

Ensure that your files are directly inside `incoming/` and that the host directory is correctly mounted to `/data`.

### Permission errors on mounted files

The container runs with the current host user's UID and GID. Check file ownership and directory permissions:

```bash
id
ls -ld "$HOME/.local/share/whatsapp-courses"
ls -ld "$HOME/.local/share/whatsapp-courses/incoming"
ls -ld "$HOME/.local/share/whatsapp-courses/uploaded"
```

Correct permissions for the intended user rather than making sensitive directories world-writable.

## 13. Security Recommendations

- Never commit `credentials.json`, `token.json`, or files containing private configuration.
- Never include personal course documents in the public repository or container image.
- Keep OAuth files in directories with restricted permissions.
- Do not publish the OAuth callback port to all network interfaces unless there is a specific, understood requirement.
- Review Google OAuth permissions before granting access.
- Test uploads with non-sensitive documents first.
- Before introducing automated ingestion, validate file types, file sizes, and untrusted content.

## 14. Current Limitations

The current implementation provides an interactive Google Drive upload workflow.

The following capabilities remain planned rather than implemented:

- Automatically reading WhatsApp conversations.
- Receiving WhatsApp documents through webhooks.
- Downloading WhatsApp attachments automatically.
- Processing incoming documents on a fixed schedule.
- Running the complete pipeline without interactive prompts.

Future WhatsApp functionality should use the official WhatsApp Business Platform and respect its permissions, policies, and access limitations.

For project updates and contribution information, see the [README](README.md).
