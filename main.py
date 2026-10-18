
import json
import os
import shutil
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path(os.getenv("APP_DATA_DIR", "/data"))
CONFIG_DIR = Path(os.getenv("APP_CONFIG_DIR", "/config"))
OAUTH_PORT = int(os.getenv("OAUTH_PORT", "8765"))

INCOMING_DIR = DATA_DIR / "incoming"
UPLOADED_DIR = DATA_DIR / "uploaded"

CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
CLIENT_FILE = CONFIG_DIR / "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/drive"]


# ============================================================
# File system and JSON helpers
# ============================================================

def prepare_directories():
    """Create application directories if they do not exist."""
    for directory in (INCOMING_DIR, UPLOADED_DIR, CONFIG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def read_json(path):
    """Read a JSON file. Return None if it is missing or invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path, data):
    """Write JSON atomically and restrict permissions where possible."""
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(path)

    try:
        path.chmod(0o600)
    except OSError:
        pass


# ============================================================
# Google OAuth and Drive API
# ============================================================

def authenticate():
    """
    Reuse a saved OAuth token or authorize Google Drive.

    The OAuth callback server listens inside the container.
    Docker must publish OAUTH_PORT to the host loopback interface.
    """
    credentials = None

    # Load an existing token.
    if TOKEN_FILE.is_file():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES,
            )
        except (ValueError, OSError):
            credentials = None

    # Refresh an expired token when possible.
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as exc:
            print(f"Could not refresh Google token: {exc}")
            credentials = None

    # Start the authorization flow if necessary.
    if not credentials or not credentials.valid:
        if not CLIENT_FILE.is_file():
            raise RuntimeError(
                f"OAuth client file not found: {CLIENT_FILE}\n"
                "Place your Google OAuth Desktop client JSON at that path.\n"
                "Enable the Google Drive API in your Google Cloud project."
            )

        redirect_uri = f"http://127.0.0.1:{OAUTH_PORT}/"

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE),
            SCOPES,
        )
        flow.redirect_uri = redirect_uri

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )

        callback = {"path": None}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)

                if parsed.path != "/" or not parsed.query:
                    self.send_response(404)
                    self.end_headers()
                    return

                callback["path"] = self.path

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8",
                )
                self.end_headers()

                self.wfile.write(
                    b"<!doctype html><html><body>"
                    b"<h2>Google authorization received.</h2>"
                    b"<p>You can return to the WhatsApp-Courses terminal.</p>"
                    b"</body></html>"
                )

            def log_message(self, format_string, *args):
                # Avoid logging OAuth callback URLs and authorization codes.
                pass

        print("\nOpen this URL in a browser on your host computer:\n")
        print(auth_url)
        print(f"\nWaiting for Google authorization on port {OAUTH_PORT}...")
        print("Complete the authorization in your browser.")

        try:
            server = HTTPServer(
                ("0.0.0.0", OAUTH_PORT),
                CallbackHandler,
            )
        except OSError as exc:
            raise RuntimeError(
                f"Cannot listen on OAuth port {OAUTH_PORT}. "
                "Check the Docker port mapping and whether the port is in use."
            ) from exc

        deadline = time.monotonic() + 300

        try:
            while (
                callback["path"] is None
                and time.monotonic() < deadline
            ):
                remaining = deadline - time.monotonic()
                server.timeout = max(1, min(10, remaining))
                server.handle_request()
        finally:
            server.server_close()

        if callback["path"] is None:
            raise RuntimeError(
                "Google authorization timed out after five minutes. "
                "Run the setup option again."
            )

        authorization_response = (
            redirect_uri.rstrip("/") + callback["path"]
        )

        flow.fetch_token(
            authorization_response=authorization_response
        )
        credentials = flow.credentials

    # Persist the token for subsequent runs.
    write_json(TOKEN_FILE, json.loads(credentials.to_json()))

    return build(
        "drive",
        "v3",
        credentials=credentials,
    )


# ============================================================
# Google Drive folders
# ============================================================

def escape_query(value):
    """Escape strings used in Google Drive query expressions."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def list_folders(service, parent_id="root"):
    """List folders directly inside a Google Drive parent folder."""
    folders = []
    page_token = None

    while True:
        response = service.files().list(
            q=(
                f"'{parent_id}' in parents and "
                "mimeType = 'application/vnd.google-apps.folder' and "
                "trashed = false"
            ),
            fields="nextPageToken, files(id, name)",
            orderBy="name",
            pageSize=100,
            pageToken=page_token,
        ).execute()

        folders.extend(response.get("files", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            return folders


def choose_destination(service):
    """Let the user select an existing folder or create a new one."""
    while True:
        folders = list_folders(service)

        print("\nGoogle Drive — folders in My Drive")
        print("0. Create a new destination folder")

        for number, folder in enumerate(folders, start=1):
            print(f"{number}. {folder['name']}")

        choice = input("\nSelect a folder: ").strip()

        if choice == "0":
            name = input("New folder name: ").strip()

            if not name:
                print("Folder name cannot be empty.")
                continue

            created = service.files().create(
                body={
                    "name": name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": ["root"],
                },
                fields="id,name",
            ).execute()

            return created

        if choice.isdigit():
            index = int(choice)

            if 1 <= index <= len(folders):
                return folders[index - 1]

        print("Invalid selection. Try again.")


def get_or_create_folder(service, name, parent_id):
    """Return a module folder ID, creating the folder if needed."""
    escaped_name = escape_query(name)

    response = service.files().list(
        q=(
            f"name = '{escaped_name}' and "
            f"'{parent_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            "trashed = false"
        ),
        fields="files(id,name)",
        pageSize=100,
    ).execute()

    folders = response.get("files", [])

    if folders:
        return folders[0]["id"]

    folder = service.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id,name",
    ).execute()

    return folder["id"]


# ============================================================
# Application setup
# ============================================================

def setup():
    """Configure the Google Drive destination and module names."""
    prepare_directories()

    if not CLIENT_FILE.is_file():
        print("\nGoogle OAuth setup is required.")
        print(f"Expected OAuth client file: {CLIENT_FILE}")
        print("\nBefore continuing:")
        print("1. Create or select a project in Google Cloud.")
        print("2. Enable the Google Drive API.")
        print("3. Create an OAuth client ID of type Desktop app.")
        print("4. Place its downloaded JSON file at the path above.")
        print("5. Run this setup option again.")
        return False

    service = authenticate()
    destination = choose_destination(service)

    defaults = "UML,FRONT,EN,AGILE,GOV,MOBILE,CRYPT"

    print(f"\nDefault modules: {defaults}")
    raw = input(
        "Enter module names separated by commas, "
        "or press Enter to use the defaults: "
    ).strip()

    modules = [
        item.strip()
        for item in (raw or defaults).split(",")
        if item.strip()
    ]

    if not modules:
        print("At least one module is required.")
        return False

    config = {
        "root_folder_id": destination["id"],
        "root_folder_name": destination["name"],
        "modules": modules,
    }

    write_json(CONFIG_FILE, config)

    print("\nConfiguration saved.")
    print(f"Destination: {destination['name']}")
    print(f"Modules: {', '.join(modules)}")

    return True


# ============================================================
# Upload management
# ============================================================

def upload_file(service, path, parent_id):
    """Upload one local file to Google Drive."""
    media = MediaFileUpload(
        str(path),
        resumable=True,
    )

    return service.files().create(
        body={
            "name": path.name,
            "parents": [parent_id],
        },
        media_body=media,
        fields="id,name,webViewLink",
    ).execute()


def run_uploads():
    """Select a module for each incoming file and upload it."""
    prepare_directories()
    config = read_json(CONFIG_FILE)

    if not config or not config.get("root_folder_id"):
        print("No configuration found. Choose 'Configure Google Drive' first.")
        return

    modules = config.get("modules", [])

    if not modules:
        print("No modules configured. Run setup again.")
        return

    service = authenticate()

    files = sorted(
        path
        for path in INCOMING_DIR.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )

    if not files:
        print(f"\nNo files found in {INCOMING_DIR}")
        print("Copy your course documents into the incoming folder.")
        return

    print(f"\nFound {len(files)} file(s).")

    for path in files:
        print(f"\nFile: {path.name}")

        for number, module in enumerate(modules, start=1):
            print(f"{number}. {module}")

        print("s. Skip")

        choice = input("Choose module: ").strip().lower()

        if choice == "s":
            continue

        if not choice.isdigit():
            print("Invalid selection; file skipped.")
            continue

        index = int(choice)

        if not 1 <= index <= len(modules):
            print("Invalid selection; file skipped.")
            continue

        module = modules[index - 1]

        try:
            folder_id = get_or_create_folder(
                service,
                module,
                config["root_folder_id"],
            )

            result = upload_file(service, path, folder_id)

            # Move the local file only after a successful upload.
            archived = UPLOADED_DIR / path.name

            if archived.exists():
                archived = (
                    UPLOADED_DIR
                    / f"{path.stem}_{result['id']}{path.suffix}"
                )

            shutil.move(str(path), str(archived))

            print(f"Uploaded: {result['name']}")

            if result.get("webViewLink"):
                print(f"Drive link: {result['webViewLink']}")

            print(f"Local archive: {archived.name}")

        except (HttpError, OSError, ValueError) as exc:
            print(f"Upload failed: {exc}")


# ============================================================
# Module configuration
# ============================================================

def edit_modules():
    """Update the list of course modules."""
    config = read_json(CONFIG_FILE)

    if not config:
        print("Configure Google Drive first.")
        return

    current = ", ".join(config.get("modules", []))
    print(f"\nCurrent modules: {current}")

    raw = input(
        "Enter the new comma-separated module list: "
    ).strip()

    modules = [
        item.strip()
        for item in raw.split(",")
        if item.strip()
    ]

    if not modules:
        print("No changes made.")
        return

    config["modules"] = modules
    write_json(CONFIG_FILE, config)

    print("Module list updated.")


# ============================================================
# Main menu
# ============================================================

def main():
    prepare_directories()

    while True:
        print("\n===================================")
        print("         WhatsApp-Courses")
        print("===================================")
        print("1. Configure Google Drive")
        print("2. Upload course documents")
        print("3. Edit module list")
        print("4. Exit")

        choice = input("\nYour choice: ").strip()

        try:
            if choice == "1":
                setup()

            elif choice == "2":
                run_uploads()

            elif choice == "3":
                edit_modules()

            elif choice == "4":
                print("Goodbye.")
                return 0

            else:
                print("Invalid choice.")

        except (HttpError, OSError, RuntimeError, ValueError) as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted.")
        raise SystemExit(130)
