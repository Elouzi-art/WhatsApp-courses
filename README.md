# WhatsApp-Courses

<p align="center">
  <img src="assets/WhatsApp-Courses%20README%20Dashboard.png" alt="WhatsApp-Courses project dashboard" width="100%">
</p>

<p align="center">
  <strong>A Dockerized workflow for organizing course documents and uploading them to Google Drive.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Google%20Drive-API-4285F4?logo=googledrive&logoColor=white" alt="Google Drive API">
  <img src="https://img.shields.io/badge/Status-in%20development-orange" alt="In development">
</p>

WhatsApp-Courses is an open-source Python application designed to simplify the organization of course documents. It currently provides an interactive workflow for uploading locally stored documents to a configurable Google Drive destination.

The project is designed to evolve toward an automated document-ingestion pipeline, with potential integration with the official WhatsApp Business Cloud API.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Google Drive Configuration](#google-drive-configuration)
- [Usage](#usage)
- [Docker Hub](#docker-hub)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Security](#security)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Docker Image

WhatsApp-Courses is distributed as a Docker image through Docker Hub.

- **Docker Hub:** [elouzi09/whatsapp-courses](https://hub.docker.com/r/elouzi09/whatsapp-courses)
- **Image:** `elouzi09/whatsapp-courses`
- **Tags:** `latest`, `0.1.0`

Pull the image:

```bash
docker pull elouzi09/whatsapp-courses:latest
```

You can also use a specific version:

```bash
docker pull elouzi09/whatsapp-courses:0.1.0
```

See the [Quick Start](#quick-start) section for configuration and execution instructions.


## Features

- **Google Drive integration** using the Google API Python client.
- **OAuth 2.0 authentication** with persistent token storage.
- **Configurable destination folder**: select an existing Google Drive folder or create a new one.
- **Custom course modules**: organize documents into categories such as `UML`, `FRONT`, `EN`, `AGILE`, `GOV`, `MOBILE`, and `CRYPT`.
- **Local staging directory**: place documents in `incoming/` before processing.
- **Upload tracking**: successfully uploaded documents are moved to `uploaded/`.
- **Docker-based execution** with persistent configuration and data volumes.
- **Separation of application and user data**: credentials and course files remain outside the container image.

## How It Works

1. Place course documents in the local `incoming/` directory.
2. Start the Docker container.
3. Configure Google Drive and course modules if needed.
4. Select the upload option from the interactive menu.
5. Assign each document to the appropriate course module.
6. The application creates or uses the corresponding module folder in Google Drive and uploads the document.
7. Successfully uploaded documents are moved to `uploaded/`.

> **Current limitation:** document processing and uploads are initiated through the interactive application. Automatic WhatsApp message retrieval and scheduled processing are not yet implemented.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Docker | Containerized execution |
| Google Drive API | Folder management and document uploads |
| Google OAuth 2.0 | User authentication |
| Persistent bind mounts | Configuration and file storage |

## Prerequisites

- Docker Engine or Docker Desktop.
- A Google account.
- A Google Cloud project with the Google Drive API enabled.
- OAuth 2.0 credentials for a **Desktop application**.
- Git, to clone the repository.



## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Elouzi-art/WhatsApp-courses.git
cd WhatsApp-courses
```

Replace the repository URL if your published GitHub repository uses a different name.

### 2. Create persistent directories

```bash
mkdir -p "$HOME/.config/whatsapp-courses"
mkdir -p "$HOME/.local/share/whatsapp-courses/incoming"
mkdir -p "$HOME/.local/share/whatsapp-courses/uploaded"

chmod 700 "$HOME/.config/whatsapp-courses"
chmod 700 "$HOME/.local/share/whatsapp-courses"
```

These directories store OAuth configuration, incoming documents, and successfully uploaded files outside the container.

### 3. Configure Google OAuth

Place your downloaded OAuth Desktop client credentials at:

```text
~/.config/whatsapp-courses/credentials.json
```

Keep this file private. Do not commit it to Git.

### 4. Build the Docker image

```bash
docker build -t whatsapp-courses:local .
```

### 5. Start the application

```bash
docker run --rm -it \
  --name whatsapp-courses \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1:8765:8765 \
  --mount "type=bind,source=$HOME/.config/whatsapp-courses,target=/config" \
  --mount "type=bind,source=$HOME/.local/share/whatsapp-courses,target=/data" \
  whatsapp-courses:local
```

The application starts in your terminal. During the initial OAuth authorization, follow the URL displayed by the application and complete the Google authentication process.

The configuration and token are stored in the persistent host directory, so they can be reused across container restarts.

## Google Drive Configuration

On the first launch, use the interactive menu to:

1. Authenticate with your Google account.
2. Select an existing Google Drive destination folder or create one.
3. Configure your course modules.
4. Save your settings.

Example module categories:

```text
UML, FRONT, EN, AGILE, GOV, MOBILE, CRYPT
```

Adapt these categories to your own courses and organizational needs.

## Usage

### Add documents

Copy your course documents into:

```text
~/.local/share/whatsapp-courses/incoming/
```

### Upload documents

Start the container and choose the upload option from the menu. Follow the prompts to assign documents to their respective modules.

### Find uploaded documents

After a successful upload, documents are moved to:

```text
~/.local/share/whatsapp-courses/uploaded/
```

### Persistent storage

| Host path | Container path | Purpose |
|---|---|---|
| `~/.config/whatsapp-courses/` | `/config` | OAuth credentials, token, and application configuration |
| `~/.local/share/whatsapp-courses/incoming/` | `/data/incoming` | Documents waiting to be processed |
| `~/.local/share/whatsapp-courses/uploaded/` | `/data/uploaded` | Successfully uploaded documents |

## Docker Hub

The Docker image is intended to be published under the following repository:

**Image:** `elouzi09/whatsapp-courses`

Pull the latest published version:

```bash
docker pull elouzi09/whatsapp-courses:latest
```

Run the downloaded image using the same persistent mounts:

```bash
docker run --rm -it \
  --name whatsapp-courses \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1:8765:8765 \
  --mount "type=bind,source=$HOME/.config/whatsapp-courses,target=/config" \
  --mount "type=bind,source=$HOME/.local/share/whatsapp-courses,target=/data" \
  elouzi09/whatsapp-courses:latest
```

Docker Hub: [elouzi09/whatsapp-courses](https://hub.docker.com/r/elouzi09/whatsapp-courses)

The image must be pushed to Docker Hub before these commands will work for other users.

## Project Structure

```text
WhatsApp-courses/
├── assets/
│   └── WhatsApp-Courses README Dashboard.png
├── config/              # Local configuration; do not commit secrets
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── README.md
└── GUIDE.md              # Detailed documentation
```

The `config/` directory shown above is local configuration, not a directory that should contain committed OAuth credentials. Runtime configuration is persisted in the mounted `/config` directory.

## Roadmap

- [x] Dockerized interactive application
- [x] Google Drive OAuth authentication
- [x] Destination folder selection
- [x] Configurable course modules
- [x] Local staging and successful-upload tracking
- [ ] Automated processing without interactive prompts
- [ ] Scheduled processing of the incoming directory
- [ ] Integration with the official WhatsApp Business Cloud API
- [ ] Webhook-based reception of authorized messages and document attachments
- [ ] Automatic media download, validation, and local staging
- [ ] Improved logging and error handling
- [ ] Optional web interface for monitoring

Future WhatsApp integration will depend on the capabilities, permissions, and requirements of the official WhatsApp Business Platform. It is not currently implemented.

## Security

- Never commit OAuth credentials, access tokens, personal documents, or private configuration files.
- Keep credentials outside the Docker image.
- Restrict access to directories containing credentials and tokens.
- Use only accounts, messages, and documents you are authorized to access.
- Validate incoming files before processing them in an automated workflow.
- Keep dependencies and the base image updated.

## Documentation

See [GUIDE.md](GUIDE.md) for detailed setup instructions, OAuth configuration, application usage, and troubleshooting.

## Contributing

Contributions, bug reports, documentation improvements, and feature suggestions are welcome.

1. Open an issue to describe a bug or proposed improvement.
2. Fork the repository.
3. Create a feature branch.
4. Submit a pull request with a clear description of your changes.

Please open an issue before implementing major changes.


