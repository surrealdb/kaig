from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from demo_unstruct_to_graph.loaders.google_drive.creds import get_creds
from demo_unstruct_to_graph.loaders.google_drive.definitions import FileHandle


def list_drive_items(
    service,  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
    drive_id: str,
    folder_id: str,
) -> list[FileHandle]:
    r"""
    Lists files and folders from a specific drive and folder in Google Drive.
    """

    try:
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
                    pageToken=page_token,
                )
                .execute()
            )

            for file in response.get("files", []):
                file_handle = FileHandle.from_dict(file)
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


def list_drive_items_recursive(
    service: object,
    drive_id: str,
    folder_id: str,
) -> list[FileHandle]:
    files: list[FileHandle] = []
    visited = set()
    items = list_drive_items(service, drive_id, folder_id)
    while len(items):
        item = items.pop()
        if item.id in visited:
            break
        else:
            visited.add(item.id)
        if item.is_folder:
            items.extend(list_drive_items(service, drive_id, item.id))
        else:
            files.append(item)
    return files


if __name__ == "__main__":
    # --- Replace these with your actual file ID and desired save location ---
    DRIVE_ID = "0AC309-7UY9naUk9PVA"  # 👈 Replace this!
    FOLDER_ID = "1JTGlu1z48EVWJ7z3Kb3_WGe-6aeqz9TN"  # 👈 Replace this!
    # ----------------------------------------------------------------------

    # Build the Drive API service
    creds = get_creds()
    service: object = build("drive", "v3", credentials=creds)
    assert isinstance(service, object)
    files = list_drive_items_recursive(service, DRIVE_ID, FOLDER_ID)
    for file in files:
        print(file)
