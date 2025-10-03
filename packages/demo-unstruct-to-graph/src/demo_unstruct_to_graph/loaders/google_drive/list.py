from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from demo_unstruct_to_graph.loaders.google_drive.creds import get_creds
from demo_unstruct_to_graph.loaders.google_drive.definitions import FileHandle


def list_drive_items(drive_id: str, folder_id: str) -> list[FileHandle]:
    r"""
    Lists files and folders from a specific drive and folder in Google Drive.
    """
    creds = get_creds()

    try:
        # Build the Drive API service
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API to list items
        # docs: https://googleapis.github.io/google-api-python-client/docs/dyn/drive_v3.files.html#list
        # guide: https://developers.google.com/workspace/drive/api/guides/search-files#all
        query = f"'{folder_id}' in parents"
        page_token = None
        files: list[FileHandle] = []
        while True:
            response = (
                service.files()
                .list(
                    corpora="drive",
                    driveId=drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    q=query,
                    pageSize=40,
                    fields=FileHandle.build_fields_param(),
                )
                .execute()
            )

            for file in response.get("files", []):
                file_handle = FileHandle.from_dict(file)
                print(file_handle)
                files.append(file_handle)

            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break

    except HttpError as error:
        # Handle potential errors, such as not having permission to view the folder
        print(f"An error occurred: {error}")
        if error.resp.status == 404:
            print(
                "Error: Folder not found. Check if the folder ID is correct and you have permission to access it."
            )
        files = []

    return files


if __name__ == "__main__":
    # --- Replace these with your actual file ID and desired save location ---
    DRIVE_ID = "0AC309-7UY9naUk9PVA"  # 👈 Replace this!
    FOLDER_ID = "1JTGlu1z48EVWJ7z3Kb3_WGe-6aeqz9TN"  # 👈 Replace this!
    # ----------------------------------------------------------------------

    _ = list_drive_items(DRIVE_ID, FOLDER_ID)
