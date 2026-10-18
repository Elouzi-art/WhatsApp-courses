# WhatsApp-Courses

**A Dockerized workflow for organizing course documents and uploading them to Google Drive.**

WhatsApp-Courses is an open-source Python application designed to simplify the organization of course documents received through messaging platforms. It currently provides an interactive workflow for uploading locally stored documents to a configurable Google Drive destination.

The project is designed to evolve toward an automated document-ingestion pipeline.

## Current Features

- **Google Drive integration** using the Google API Python client.
- **OAuth 2.0 authentication** with persistent token storage.
- **Configurable destination folder**: select an existing Google Drive folder or create a new one.
- **Custom course modules**: organize documents into categories such as UML, FRONT, EN, AGILE, GOV, MOBILE, and CRYPT.
- **Local staging directory**: place documents in an `incoming/` directory before processing.
- **Upload tracking**: successfully uploaded documents are moved to `uploaded/`.
- **Docker-based execution** with persistent configuration and data volumes.
- **Separation of application and user data** so credentials and course files do not need to be included in the container image.

## How It Works

1. Place course documents in the local `incoming/` directory.
2. Start the Docker container.
3. Configure Google Drive and course modules if needed.
4. Select the upload option and assign each document to a module.
5. The application creates the corresponding module folder in Google Drive and uploads the document.
6. Successfully uploaded files are moved to `uploaded/`.

## Technology Stack

- Python
- Docker
- Google Drive API
- Google OAuth 2.0

## Quick Start

Requirements: Docker Engine or Docker Desktop, a Google account, and OAuth client credentials for a Google Cloud project with the Google Drive API enabled.

```bash
git clone https://github.com/Elouzi-art/WhatsApp-courses.git
cd WhatsApp-courses

mkdir -p "$HOME/.config/whatsapp-courses"
mkdir -p "$HOME/.local/share/whatsapp-courses/incoming"
mkdir -p "$HOME/.local/share/whatsapp-courses/uploaded"

docker build -t whatsapp-courses:local .
```

Place your Google OAuth Desktop client file at:

```text
~/.config/whatsapp-courses/credentials.json
```

Start the application:

```bash
docker run --rm -it \
  --name whatsapp-courses \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1:8765:8765 \
  --mount "type=bind,source=$HOME/.config/whatsapp-courses,target=/config" \
  --mount "type=bind,source=$HOME/.local/share/whatsapp-courses,target=/data" \
  whatsapp-courses:local
```

**Important:** The repository URL above assumes that the repository will be published under this name. Adjust it if the actual GitHub repository name differs. See [GUIDE.md](GUIDE.md) for the complete setup, OAuth configuration, usage, and troubleshooting instructions.

## Roadmap

- [x] Dockerized interactive application
- [x] Google Drive OAuth authentication and folder selection
- [x] Configurable course modules
- [x] Local staging and successful-upload tracking
- [ ] Automated processing without interactive prompts
- [ ] Scheduled processing of the local incoming directory
- [ ] Integration with the official WhatsApp Business Cloud API
- [ ] Webhook-based reception of authorized incoming messages and document attachments
- [ ] Automatic media download, validation, and local staging
- [ ] Configurable end-to-end automation and improved logging

Future WhatsApp integration will depend on the capabilities and permissions of the official WhatsApp Business Platform. It is not currently implemented.

## Security

- Never commit OAuth credentials, access tokens, personal documents, or local configuration files.
- Keep credentials outside the Docker image.
- Restrict permissions on local configuration and token files.
- Use only accounts, messages, and documents you are authorized to access.
- Validate incoming files before processing them in an automated workflow.

## Documentation

- [Complete setup and configuration guide](GUIDE.md)

## Contributing

Contributions, bug reports, documentation improvements, and feature suggestions are welcome. Please open an issue before implementing major changes.

## License

The project license has not yet been selected. Licensing information will be added once a license is chosen.
