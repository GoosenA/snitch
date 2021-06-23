import os
import json
from flask import Response

from google.cloud import pubsub_v1
from google.cloud import firestore


MERCHANT_TOPIC = os.environ["MERCHANT_TOPIC"]
CARD_TOPIC = os.environ["CARD_TOPIC"]
USER_COLLECTION = os.environ["USER_COLLECTION"]


def process_transaction(request):
    # Try to get json from post
    request_json = request.get_json()
    if request_json is None:
        message = "failed - json"
        return Response(message, status=400)

    transaction = request_json["transaction"]

    # Validate user id
    user_id = request_json.get("user_id", None)
    if not user_id:
        return Response("User id not in transaction", status=500)
    if not validate_user_id(user_id):
        return Response("Not a valid user", status=500)
    
    # If minimum number of transaction fields set
    if all(key in transaction for key in ["merchant", "card", "dateTime"]):
        transaction["transactionDate"] = transaction["dateTime"].split("T", 1)[0]

        try:
            subscription_status = determine_subscription_status(transaction)
            process_transaction_info(transaction, user_id, subscription_status)
        except Exception as e:
            return Response("failed", status=500)
        return Response("ok", status=200)

    # Finally fail
    message = "failed - invalid data"
    return Response(message, status=400)


def validate_user_id(user_id):
    db = firestore.Client()
    user_ref = db.collection(USER_COLLECTION).document(user_id)
    user = user_ref.get()

    return user.exists


def determine_subscription_status(transaction):
    # determine if transaction is a subscription or a not
    if not transaction["currencyCode"].lower() == "zar":
        return True

    if not transaction["merchant"]["country"]["code"].lower() == "za":
        return True

    merchant_cat_matches = ["4121", "4784", "4899", "5968", "6300", "7399" ]
    if any(x in transaction["merchant"]["category"]["code"].lower() for x in merchant_cat_matches):
        return True
    
    merchant_name_keyword_matches = ["online", ".com", "digital", "payfast", "paygate", "wirecard"]
    if any(x in transaction["merchant"]["name"].lower() for x in merchant_name_keyword_matches):
        return True
    
    subscription_merchants = ["aliexpress", "uber", "ebay", "loot", "netflorist", "raru", "zando", "takealot", "onedayonly", "yuppiechef", "superbalist"]
    if any(x in transaction["merchant"]["name"].lower() for x in subscription_merchants):
        return True

    return False


def process_transaction_info(transaction, user_id, subscription_status):
    merchant_info = {
        "user_id": user_id,
        "subscription": subscription_status,
        "merchant": transaction["merchant"],
        "card": transaction["card"],
        "transaction": {
            "date": transaction["transactionDate"]
        }
    }
    if "description" in transaction:
        merchant_info["description"] = transaction["transaction"]
    else:
         merchant_info["description"] = None
    publish_merchant(merchant_info)

    card_info = {}
    card_info["card_id"] = transaction["card"]["id"]
    if "display" in transaction["card"]:
        card_info["display"] = transaction["card"]["display"]
    if "expiry_date" in transaction["card"]:
        card_info["expiry_date"] = transaction["card"]["expiry_date"]
    card_info["user_id"] = user_id
    publish_card(card_info)


def publish_merchant(merchant_info):
    publish_pubsub_message(merchant_info, os.environ["PROJECT_ID"], MERCHANT_TOPIC)


def publish_card(card_info):
    publish_pubsub_message(card_info, os.environ["PROJECT_ID"], CARD_TOPIC)


def publish_pubsub_message(payload, project_id, topic_id):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    data = json.dumps(payload).encode("utf-8")
    publisher.publish(topic_path, data)
