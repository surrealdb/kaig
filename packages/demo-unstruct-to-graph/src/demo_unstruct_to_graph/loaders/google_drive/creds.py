import os

from google.auth.external_account_authorized_user import (
    Credentials as ExternalCredentials,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import (  # pyright: ignore[reportMissingTypeStubs]
    InstalledAppFlow,
)

# This defines the level of access the script will have.
# '.readonly' is safer if you only need to download.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SECRET_FILE = "secrets/google-cloud-client-secret.json"
TOKEN_FILE = "secrets/token.json"


def get_creds() -> Credentials | ExternalCredentials | None:
    creds: Credentials | ExternalCredentials | None = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)  # pyright: ignore[reportUnknownMemberType]

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:  # pyright: ignore[reportUnknownMemberType]
            creds.refresh(Request())  # pyright: ignore[reportUnknownMemberType]
        else:
            # You must have 'credentials.json' from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType]
                SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)  # pyright: ignore[reportUnknownMemberType]

        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            _ = token.write(creds.to_json())  # pyright: ignore[reportUnknownMemberType]

    return creds
