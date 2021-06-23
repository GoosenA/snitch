# Follow these steps to deploy your own version
1. [Create Google Cloud Project](#create-google-cloud-project)
2. [Create a Firestore database](#create-a-firestore-database) 
3. [Create Cloud Functions](#create-cloud-functions)
5. [Upload code to Investec Programmable Banking card](#upload-code-to-investec-programmable-banking-card)


## Create Google Cloud Project
Follow  [these steps](https://cloud.google.com/resource-manager/docs/creating-managing-projects#gcloud) to create a GCP project. You need to configure your local terminal to deploy cloud functions in later steps. To do so, you need to set the project-id:
1. Check your project:
  ```
  gcloud config get-value project
  ```
2. Set the project id:
  ```
  gcloud config set project <PROJECT_ID>
  ```

## Create a Firestore database
### Firestore is used to store user info. The user info stored includes:
- user id
- spreadsheet id

### Important considerations
- Choose the database **location** in the same area where the Cloud Functions instances will be created.
- Create the Firestore instance in **native** mode.

### Instructions
- Follow [these instructions](https://cloud.google.com/firestore/docs/quickstart-servers#create_a_in_native_mode_database) to create a Firestore instance in your GCP project.

## Create Cloud Functions
### a. Process transactions
#### What this function does:
This functions processes transaction and user information. 
- Validates provided user data (aka checks if the user is registered)
- Extracts the merchant information
- Determines if the transaction is a subscription or not based on the merchant information
- Sends the processed merchant information to the [process_merchant]() cloud function
- Extracts card information and sends it to the [process_card]() cloud function.

#### Deploy the function using `gcloud` ([Google cloud SDK](https://cloud.google.com/sdk/docs/install))
  ```
  gcloud functions deploy process-transaction --entry-point=process_transaction --runtime=python38 --trigger-http --region=[REGION] --memory=128MB --timeout=60s --env-vars-file .env.yaml
  ```

### b. Process merchants
#### What this function does
This functions processes merchant and user information. 
- Checks if the merchant information provided already exists in the google spreadsheet owned by the user
- Adds the merchant information to the spreadsheet if the merchant does not exists - either in the **Subscriptions** or **Not subscriptions** sheets
- Updates the merchant info, such as the last transaction date, in the spreadsheet
  - If the last transaction was exactly **n** months or **n** years ago, non-subscriptions are changed to subscriptions

#### Deploy the function using `gcloud` 
  ```
  gcloud functions deploy process-merchant --entry-point=process_merchant --runtime=python38 --trigger-topic merchant --region=[REGION] --memory=256MB --timeout=60s --env-vars-file .env.yaml
  ```

### c. Process cards
#### What this function does
This functions processes card and user information. 
- It checks if the card info provided already exists in the spreadsheet owned by the user
- Adds the card info to the spreadsheet if the card does not exists
- Updates the card info in the spreadsheet if the card already exists

#### Deploy the function using `gcloud` 
  ```
  gcloud functions deploy process-card --entry-point=process_card --runtime=python38 --trigger-topic card --region=us-east1 --memory=256MB --timeout=60s --env-vars-file .env.yaml
  ```

### d. Create and format a Google spreadsheet
#### In GCP, create a GCP service account to access the Google sheets:
Create a new service account and create a service account key. The service account key will be downloaded to a .json file. Create a new secret in the secrets manager calles `SHEETS`. Add the service account key file to the `SHEETS` secret.


#### In Google Spreadsheets:
Create a blank spreadsheet and copy the spreadsheet ID from the spreadsheet url.
```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit#gid=0
```
Add the service account to the spreadsheet with editor writes.

#### In GCP Firestore:
Add a dummy user to the **user** collection in Firestore.
![Add user to firestore](add_user_firestore.png)
Make sure the document id matches the username field. 
Add the spreadsheet ID to the `sheet_id` field in the user document.

#### In GCP Cloud Functions:
Run the `format sheet` cloud function to initialise your spreadsheet.
![Run the format sheet cloud function](format_sheet.png)



## Upload code to Investec Programmable Banking card

The same code is used for all your cards. 

### Environmental variables
To set up the environment variables on the Investec Programmable Card, the transaction API URL and an user ID is required.

To get the transaction API URL, navigate to the trigger page of the **process-transaction** cloud function. 
![Transaction API URL](transaction_api_link.png)



Add the transaction API URL and the user ID to the environment variables code below. Add the code to your to the env.json file on your Investec Programmable Card. Note, you can still use your own environmental variables as well.
```
{
    "your_variable": "another variable you might have",
    "transactionApi": "TRANSACTION API LINK",
    "user_id": "USER IDENTIFIER"
}
```
### Code
Add the following code to your to the main.js file. Note, you can still use your own code as well. By default this code only executes on simulation. You can remove that limitation if you want to process production data.
```
{
    async function pushTransaction(transaction) {
        try {
            const response = await fetch(process.env.transactionApi, {
                method: 'POST',
                headers: {  'Content-Type': 'application/json'},
                body: JSON.stringify({
                    "transaction": transaction,
                    "user_id": process.env.user_id
                })
            });
            responseLog = {
                status: response.status,
                statusText: response.statusText,
                serverMessage: (await response.text())
            }
            console.log(JSON.stringify(responseLog))
        }
        catch (e) {
            console.log(e)
        }
    };
    
    // This function runs during the card transaction authorization flow.
    // It has a limited execution time, so keep any code short-running.
    const beforeTransaction = async (authorization) => {
        return true;
    };
    
    // This function runs after a transaction.
    const afterTransaction = async (transaction) => {
        if (transaction.reference === 'simulation') {
            // this is a simulated transaction
            await pushTransaction(transaction)
        }
        else {
            // this is a production transaction
        }
    };
}
```




[:arrow_left: Go back to Setup list](../README.md#setup)