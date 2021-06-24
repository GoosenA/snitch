import os
import json
import base64
import hashlib

from datetime import datetime
from dateutil.relativedelta import relativedelta
from re import sub

from flask import Response

from googleapiclient import discovery
from google.oauth2 import service_account
from google.cloud import secretmanager

from google.cloud import firestore


USER_COLLECTION = os.environ["USER_COLLECTION"]

CREDIT_CARD_RANGE_NAME = os.environ["CREDIT_CARD_RANGE_NAME"]
SUBCRIPTIONS_RANGE_NAME = os.environ["SUBCRIPTIONS_RANGE_NAME"]
NOT_SUBCRIPTIONS_RANGE_NAME = os.environ["NOT_SUBCRIPTIONS_RANGE_NAME"]


def process_merchant(event, context):
    decoded = base64.b64decode(event["data"]).decode("utf-8")
    merchant = json.loads(decoded)
    merchant["merchant_id"] = calculate_merchant_id(merchant["merchant"])

    sheet_id = get_sheet_id_from_user(merchant["user_id"])
    sheets = GoogleSheets(sheet_id)

    range_name = SUBCRIPTIONS_RANGE_NAME
    subscription_exist = False
    if not merchant["subscription"]:
        if sheets.check_subscription_exists(merchant["merchant_id"], NOT_SUBCRIPTIONS_RANGE_NAME) or sheets.check_subscription_exists(merchant["merchant_id"], SUBCRIPTIONS_RANGE_NAME):
            # update last transaction date
            sheets.update_subscription(merchant)
            subscription_exist = True
        else:
            range_name = NOT_SUBCRIPTIONS_RANGE_NAME

    if not subscription_exist:
        sheets.add_subscriptions(merchant, range_name)

    return Response("ok", status=200)


def calculate_merchant_id(merchant):
    payload = {
        "category": merchant["category"],
        "city": merchant["city"],
        "country": merchant["country"],
        "name": merchant["name"],
    }
    id = hashlib.md5(str(payload).encode('utf-8')).hexdigest() 
    return id


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


    # =============== SUBSCRIPTION =====================================
    def add_subscriptions(self, subscription, range_name):

        if self.check_subscription_exists(subscription["merchant_id"], range_name):
            return

        last_row = self.get_last_subscription_row(range_name)
        _range = range_name + "!A"+str(last_row+1)+":L"+str(last_row+1)
        values = [
            [
                subscription["merchant_id"],
                subscription["card"]["id"],
                subscription["subscription"],
                subscription["merchant"]["name"],
                subscription["merchant"]["category"]["code"],
                subscription["merchant"]["category"]["key"],
                subscription["merchant"]["category"]["name"],
                subscription["merchant"]["city"],
                subscription["merchant"]["country"]["code"], 
                subscription["merchant"]["country"]["name"],
                subscription["transaction"]["date"]
            ]
        ]

        self.add_data(_range, values, 'USER_ENTERED')

    def check_subscription_exists(self, subscription_id, range_name):
        subscriptions = self.get_subscriptions(range_name)
        for ss in subscriptions:
            if ss[0] == subscription_id:
                return True
        return False

    def get_last_subscription_row(self, range_name):
        return int(self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=range_name+"!M1").execute()["values"][0][0])


    def get_subscriptions(self, range_name):
        row_count = self.get_last_subscription_row(range_name)
        subscriptions = []
        if row_count > 1:
            subscriptions_range = "!A"+ str(2) + ":K" + str(row_count)
            result = self.get_data(range_name + subscriptions_range)
            subscriptions = result.get('values', [])

        return subscriptions

    def update_subscription(self, subscription):
        _range = NOT_SUBCRIPTIONS_RANGE_NAME
        if self.check_subscription_exists(subscription["merchant_id"], SUBCRIPTIONS_RANGE_NAME):
            _range = SUBCRIPTIONS_RANGE_NAME
        
        # find range row and column
        subscriptions = self.get_subscriptions(_range)
        update_column = 0
        for i, ss in enumerate(subscriptions):
            if ss[0] == subscription["merchant_id"]:
                last_date = ss[10]
                update_column = i+2
        
        update_range= _range + "!K"+ str(i+2)
        values = [
            [subscription["transaction"]["date"]]
        ]
        self.add_data(update_range, values, 'USER_ENTERED')

        last = datetime.strptime(last_date, "%Y-%m-%d")
        new = datetime.strptime(subscription["transaction"]["date"], "%Y-%m-%d")
        date_diff = relativedelta(new, last)

        if (date_diff.months > 0 or date_diff.years > 0) and date_diff.days == 0:
            subscription = True

        update_range = _range + "!C" + str(update_column)
        values = [
            [True]
        ]
        self.add_data(update_range, values, 'USER_ENTERED')

