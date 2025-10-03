import gspread

# gspread docs: https://docs.gspread.org/en/latest/index.html


def load(spreadsheet: str) -> None:
    gc = gspread.oauth(
        credentials_filename="./secrets/google-cloud-client-secret.json"
    )

    spreadsheets = gc.list_spreadsheet_files()
    for sh in spreadsheets:
        print(f"spreadsheet: {sh}")

    sh = gc.open(spreadsheet)

    worksheets = sh.worksheets()
    print(f"worksheets: {worksheets}")
    for ws in worksheets:
        records = ws.get_all_records()
        print(records)
