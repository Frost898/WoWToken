# WoWToken

## Tech
### 1. World of Warcraft - WoW Token API
This API was chosen, as price data is simple and easy to work with. The API outputs the price of the WoW Token and a timestamp of the last time the price was updated.
You can read more about Blizzards APIs here: https://develop.battle.net/documentation/world-of-warcraft/game-data-apis

### 2. Python
Python was chosen as the programming language as it is widely used for Data Engineering. It is also my prefered language. Python here acts as the "glue" which connects the different parts of the systems.
You can find all code used in this repository.

### 3. Google Cloud Function
Google Cloud Function is used to automate the data pipeline. This Function holds the Python code. Because it is placed in the cloud, I'm able to run the code every 20 minutes, even when my computer is not on.
Here, I use the script found in this repository in a Google Cloud Run Function. I use Google Schedule to trigger the Google Cloud Run Function every 20 minutes.

### 4. Google Sheets
Google Sheets was essentially chosen as the database. Not because it is best-practice as a database, but because it is free and has a built-in connection to Looker Studio. For a more data-intensive project, I'd use something like BigQuery to hold the data.
You can see the data in the Google Sheet here: https://docs.google.com/spreadsheets/d/1hNr5aJTArFSsOskLYDFB6U0ekcFWtm2si7-i0AaCKcA/edit?usp=sharing

### 5. Looker Studio
Looker Studio was chosen because it is free and has the built-in connection with Google Sheets.
You can find an example dashboard, which shows the WoW Token price here: https://lookerstudio.google.com/s/lmocDfuP_cc
