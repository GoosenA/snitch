import os
import json
import base64

from flask import Response

from googleapiclient import discovery
from google.oauth2 import service_account
from google.cloud import secretmanager

from google.cloud import firestore

USER_COLLECTION = os.environ["USER_COLLECTION"]

CREDIT_CARD_RANGE_NAME = os.environ["CREDIT_CARD_RANGE_NAME"]
SUBCRIPTIONS_RANGE_NAME = os.environ["SUBCRIPTIONS_RANGE_NAME"]
NOT_SUBCRIPTIONS_RANGE_NAME = os.environ["NOT_SUBCRIPTIONS_RANGE_NAME"]


def process_card(event, context):
    decoded = base64.b64decode(event["data"]).decode("utf-8")
    card = json.loads(decoded)

    sheet_id = get_sheet_id_from_user(card["user_id"])
    sheets = GoogleSheets(sheet_id)
    sheets.add_credit_card(card)

    return "ok"

def get_sheet_id_from_user(user_id):
    db = firestore.Client()
    user_ref = db.collection(USER_COLLECTION).document(user_id)
    user = user_ref.get()

    return user.to_dict()["sheet_id"]


class GoogleSheets():
    spreadsheet_id = None

    def __init__(self, spreadsheet_id):
        scopes = ["https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
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
        return json.loads(response.payload.data.decode('UTF-8'))

    
    # =============== GENERIC =====================================
    def add_data(self, _range, values, value_input_option):
        body = {
            'values': values
        } 
        request = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=_range, 
            valueInputOption=value_input_option, 
            body=body
        ).execute()


    def get_data(self, range_name):
        return self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()


    # =============== CREDIT CARDS =====================================
    def add_credit_card(self, credit_card):
        credit_cards = self.get_credit_cards()
        cc_already_exists = False
        for cc in credit_cards:
            if cc[0] == credit_card["card_id"]:
                cc_already_exists = True

        if cc_already_exists:
            return   

        display = ""
        if "display" in credit_card:
            display = credit_card["display"]

        last_row = self.get_last_credit_card_row(CREDIT_CARD_RANGE_NAME)
        _range = CREDIT_CARD_RANGE_NAME + "!A"+str(last_row+1)+":C"+str(last_row+1)
        values = [
            [credit_card["card_id"], display, ""]
        ]

        self.add_data(_range, values, 'USER_ENTERED')
        

    def get_last_credit_card_row(self, range_name):
        return int(self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=range_name+"!E1").execute()["values"][0][0])


    def get_credit_cards(self):
        row_count = self.get_last_credit_card_row(CREDIT_CARD_RANGE_NAME)
        credit_cards = []
        if row_count> 1:
            credit_card_range = "!A"+ str(2) + ":C" + str(row_count)
            result = self.get_data(CREDIT_CARD_RANGE_NAME + credit_card_range)
            credit_cards = result.get('values', [])

        return credit_cards
