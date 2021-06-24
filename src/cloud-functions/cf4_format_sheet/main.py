import os
import json

from google.cloud import secretmanager
from googleapiclient import discovery
from google.oauth2 import service_account


def format_sheet(request):
    request_json = request.get_json(silent=True)

    if request_json and "sheet_id" in request_json:
        sheet_id = request_json["sheet_id"]
    else:
        return "fail - no sheet id"

    sheets = GoogleSheets(sheet_id)
    sheets.add_multiple_sheets(get_sheet_structures())
    return "success"


def get_sheet_structures():
    return {
        os.environ.get("CREDIT_CARD_RANGE_NAME", "Credit card"): [
            "ID",
            "Card number",
            "Expiry date",
            "Reminder sent",
            "=COUNTA(A:A)",
        ],
        os.environ.get("SUBCRIPTIONS_RANGE_NAME", "Subscriptions"): [
            "ID",
            "Card ID",
            "Subscription",
            "Name",
            "Category Code",
            "Category Key",
            "Category Name",
            "City",
            "Country Code",
            "Country Name",
            "Last Transaction Date",
            "Image",
            "=COUNTA(A:A)",
        ],
        os.environ.get("NOT_SUBCRIPTIONS_RANGE_NAME", "Not subscriptions"): [
            "ID",
            "Card ID",
            "Subscription",
            "Name",
            "Category Code",
            "Category Key",
            "Category Name",
            "City",
            "Country Code",
            "Country Name",
            "Last Transaction Date",
            "Image",
            "=COUNTA(A:A)",
        ],
    }


class GoogleSheets:
    spreadsheet_id = None

    def __init__(self, spreadsheet_id):
        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        sheets_secret = self.access_secret_version("SHEETS")
        credentials = service_account.Credentials.from_service_account_info(sheets_secret, scopes=scopes)

        self.service = discovery.build("sheets", "v4", credentials=credentials)
        self.spreadsheet_id = spreadsheet_id

    def access_secret_version(self, secret_id, version_id="latest"):
        project_id = os.environ["GCP_PROJECT"]
        # Create the Secret Manager client.
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version.
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

        # Access the secret version.
        response = client.access_secret_version(name=name)

        # Return the decoded payload.
        return json.loads(response.payload.data.decode("UTF-8"))

    def add_multiple_sheets(self, sheet_structures):
        for name, columns in sheet_structures.items():
            self.add_sheet(name, columns)
            self.add_data(f"{name}!A1", [columns], "USER_ENTERED")

    def add_sheet(self, sheet_name, sheet_structure):
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {"rowCount": 200, "columnCount": len(sheet_structure)},
                            "tabColor": {"red": 1.0, "green": 0, "blue": 0},
                        }
                    }
                }
            ]
        }
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
        print(f"{sheet_name} created")

    # =============== GENERIC =====================================
    def add_data(self, _range, values, value_input_option):
        body = {"values": values}
        request = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=self.spreadsheet_id, range=_range, valueInputOption=value_input_option, body=body)
            .execute()
        )
