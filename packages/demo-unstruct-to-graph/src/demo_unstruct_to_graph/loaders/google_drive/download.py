import io
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from demo_unstruct_to_graph.loaders.google_drive.creds import get_creds

FileDescriptorOrPath = int | str | bytes | os.PathLike[str] | os.PathLike[bytes]


def download_file(file_id: str, destination_path: FileDescriptorOrPath):
    """Downloads a file from Google Drive."""
    creds = get_creds()

    try:
        # Build the Drive API service
        service = build("drive", "v3", credentials=creds)

        # Create the request to get the file's media content
        request = service.files().get_media(fileId=file_id)

        # Create a file object to save the downloaded content
        fh = io.FileIO(destination_path, "wb")

        # Use MediaIoBaseDownload to handle the download, especially for large files
        downloader = MediaIoBaseDownload(fh, request)  # pyright: ignore[reportUnknownArgumentType]

        done = False
        print(f"Downloading file with ID: {file_id} to {destination_path}...")
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        print("Download complete! ✅")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python download.py <file_id> <save_location>")
        sys.exit(1)
    file_id = sys.argv[1]
    save_location = sys.argv[2]
    download_file(file_id, save_location)
