# [Snitch]((https://hackathon-202106.ue.r.appspot.com/)) :speech_balloon:

![#f03c15](https://via.placeholder.com/15/f03c15/000000?text=+) TODO: add project description



## Getting started
Create a user [here](https://hackathon-202106.ue.r.appspot.com/) and follow the steps to get started using this project. 


# Index
1. [Overview](#overview)
    1. [Features]()
    2. [Benefits of using this project](#benefits-of-using-this-project)
    3. [Getting started](#getting-started)
2. [Technical Details](#technical-details) 
    1. [Technology used](#technology-used)
    2. [Design](#design)
3. [Setup your own version](#setup-your-own-version)
4. [Future improvements](#future-improvements)


# Overview
## Features
The project analyses credit card transactions and creates a list of merchants were the credit card information is potentialy stored, such as online stores or for subscription services. This list can then be used to update the credit card information with various merchants when the credit card expires. 

## Benefits of using this project
This project provides the end user with a few benefits including:
- A list of merchants where the credit card information is stored to make it easier to update the info when a credit card expires.
- Get notifications when a credit card is nearing its expiry date, allowing you to plan your update time.
- Potentially avoid paying penalties due to late payments when credit cards expire.
- You remain in control of your data the entire time. We do NOT store any transaction data on our side.


# Technical details
## Technology used
The project is built using:
- GCP Cloud Functions, Firestore, Pub/Sub
- Python
- [Apps Script](https://developers.google.com/apps-script)
- [AppSheet](https://www.appsheet.com/)
- Flask

## Design
The application stores user account details in a GCP firestore collection. The Flask web app connects to the collection to create and retrieve user details.

![System diagram](docs/snitch.png)

Every time a card transaction is made, the transaction information is sent to the `process_transaction` cloud function. The merchant information and card information is seperated and processed. The merchant information is published to the `merchant` Pub/Sub topic. The card information is published to the `card` Pub/Sub topic.

The `process_merchant` cloud function is triggered by the message published to the `merchant` topic. The cloud function determines if the merchant is in either the **Subscriptions**/**Not subscriptions** sheets or not. If the merchant information is not in either sheet, it is added to the relevant sheet based on the categorisation thereof. If the merchant information is already stored in one of the sheets, the merchant information is updated where necessary.

The `process_card` cloud function is triggered by the message published to the `card` topip. The cloud function determines if the card information is stored in the **Credit card** sheet. If the credit card information is not in the sheet, it is added.


# Setup your own version
Don't want to sign up for one more user account? Would you rather do things the hard way and deploy your own version? No problem. Follow [these steps](docs/SETUP.md) to set up your own version of the project on Google Cloud.


# Future improvements
There are various ways this project can be improved upon, including:
- Improve the merchant information classification
- Add a **scalable** mobile app
