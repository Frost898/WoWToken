import datetime
import requests
import json
import os.path
import logging
import pandas as pd

#logging.getLogger().setLevel(logging.DEBUG)

#WoW Keys
clientID = "" #Insert your Client ID from Blizzard here
clientSecret = "" #Insert your Client Secret from Blizzard here

url = "https://eu.api.blizzard.com"
token_url = "https://oauth.battle.net/token"

wowTokenAddon = "/data/wow/token/index?namespace=dynamic-eu"

#Google Variables
googleSecretsFile = "secrets.json"
googleRefreshFile = "refreshCredentials.json"

GoogleAccessTokenURL = "https://www.googleapis.com/oauth2/v4/token"

googleSheetID = "1hNr5aJTArFSsOskLYDFB6U0ekcFWtm2si7-i0AaCKcA"

def wow_refresh_access_token(clientID, clientSecret, fileToCheck):
    data = {'grant_type': 'client_credentials'}
    
    #Get credentials
    r = requests.post(token_url, data=data, auth=(clientID, clientSecret))
    r = r.json()

    r["expiration_time"] = (datetime.datetime.today() + datetime.timedelta(seconds=r["expires_in"])).strftime('%Y-%m-%d %H:%M:%S')

    #Save to local
    with open(fileToCheck, 'w') as f:
        json.dump(r, f)

def wow_check_access_token(fileToCheck):
    file_exists = os.path.isfile(fileToCheck)

    if file_exists:
        logging.info("File found")
        with open(fileToCheck) as f:
            d = json.load(f)

        logging.debug("Check if expired")
        expiration_date = datetime.datetime.strptime(d["expiration_time"], '%Y-%m-%d %H:%M:%S')

        if expiration_date < datetime.datetime.today():
            logging.debug("Expiration date exceeded. Get new access token")
            wow_refresh_access_token(clientID, clientSecret, fileToCheck)
            with open(fileToCheck) as f:
                d = json.load(f)
        else:
            logging.debug("Expiration date not exceeded")
        return d
    
    else:
        logging.debug("File not found")
        wow_refresh_access_token(clientID, clientSecret, fileToCheck)
        with open(fileToCheck) as f:
            d = json.load(f)
        return d
    
def wowtoken():
    access = wow_check_access_token("WoWaccess.json")
    access_token = access["access_token"]

    wowtoken_url = "".join([url, wowTokenAddon,"&access_token=", access_token])

    wowtoken = requests.get(wowtoken_url)
    wowtoken = wowtoken.json()

    wowtoken_price, wowtoken_time = wowtoken["price"], datetime.datetime.fromtimestamp(wowtoken["last_updated_timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")

    extraction_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return wowtoken_price, wowtoken_time, extraction_time

def google_refresh_access_token(googleSecretsFile, googleRefreshFile, desiredFileName):
    #Credentials
    f = open(googleSecretsFile)
    credentials = json.load(f)
    f.close()

    #Read client id and client secret from file
    #Credentials
    clientID = credentials["web"]["client_id"]
    clientSecret = credentials["web"]["client_secret"]

    #Refresh token
    f = open(googleRefreshFile)
    refreshToken = json.load(f)
    f.close()
    
    #Request building
    auth = (clientID, clientSecret)
    params = {
        "grant_type":"refresh_token",
        "refresh_token":refreshToken["refresh_token"]
    }

    #Send request
    r = requests.post(GoogleAccessTokenURL, auth=auth, data=params) #note data=params, not params=params

    #Access token
    if r.status_code == 200:
        r = r.json()

        r["expiration_time"] = (datetime.datetime.today() + datetime.timedelta(seconds=r["expires_in"])).strftime('%Y-%m-%d %H:%M:%S')
        #Save to local
        with open(desiredFileName, 'w') as f:
            json.dump(r, f)
    else:
        print("Error")

def google_check_access_token(googleSecretsFile, googleRefreshFile, fileToCheck):

    file_exists = [os.path.isfile(n) for n in [fileToCheck]][0]

    if file_exists:
        logging.info("File found")
        with open(fileToCheck) as f:
            d = json.load(f)

        logging.debug("Check if expired")
        expiration_date = datetime.datetime.strptime(d["expiration_time"], '%Y-%m-%d %H:%M:%S')

        if expiration_date < datetime.datetime.today():
            logging.debug("Expiration date exceeded. Get new access token")
            google_refresh_access_token(googleSecretsFile, googleRefreshFile, fileToCheck)
            with open(fileToCheck) as f:
                d = json.load(f)
        else:
            logging.debug("Expiration date not exceeded")
        return d
    
    else:
        logging.debug("File not found")
        google_refresh_access_token(googleSecretsFile, googleRefreshFile, fileToCheck)
        with open(fileToCheck) as f:
            d = json.load(f)
        return d
    

### Code starts ###
#Calling the API
price, last_updated_time, extraction_time = wowtoken()

#Building DataFrame
df = pd.DataFrame({"price":[price], "last_updated_time":[last_updated_time], "extraction_time":[extraction_time]})

#Upload to Google Sheets
#https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append

#Access Token
access = google_check_access_token(googleSecretsFile, googleRefreshFile, "googleaccess.json")
access_token = access["access_token"]

#Columns as string (Google Sheet columns are capital letters)
colStr = "".join(["A:",chr(ord('A') + len(df.columns.tolist()) - 1)])

#Check if sheet is empty
gs_url_length = f"https://sheets.googleapis.com/v4/spreadsheets/{googleSheetID}/values/{colStr}?access_token={access_token}"
r = requests.get(url=gs_url_length)
containsValues = "values" in r.json().keys()

#Duplication Check - If there are values -> What was the latest updated timestamp?
if containsValues:
    GSlatestUpdate = r.json()["values"][-1][1] #Latest timestamp for then the price was updated
    APIlatestUpdate = df["last_updated_time"].values[0]
    updateGS = GSlatestUpdate != APIlatestUpdate #Can be True or False:
                                                 #If True, the timestamps from GS and API are the same. Meaning we don't need the data
                                                 #If False, the timestamps from GS and API are NOT the same. Meaning we want to upload data
else:
    updateGS = True

if updateGS: #If it is True
    # Upload data
    gs_url = f"https://sheets.googleapis.com/v4/spreadsheets/{googleSheetID}/values/{colStr}:append?access_token={access_token}&valueInputOption=USER_ENTERED"

    # If Google Sheet is empty, upload headers first
    if not containsValues:
        r = requests.post(url=gs_url, json={"values": [df.columns.tolist()]})
        if r.status_code == 200:
            logging.info("Headers added")
            containsValues = True
        else:
            logging.info("Error uploading headers")
    else:
        logging.info("Headers not uploaded")

    # If Google Sheet contains 1 row, upload rest of data
    if containsValues:
        r = requests.post(url=gs_url, json={"values": df.values.tolist()})
        if r.status_code == 200:
            logging.info("Data added")
        else:
            logging.info("Error uploading data")
    else:
        logging.info("Data not uploaded")
else:
    logging.info("Data was not uploaded due to API and GS values being identical")