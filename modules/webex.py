### Import Needed Libraries
import sys, os, json,requests
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from urllib import parse
from benedict import benedict

### Set proper working directory to import Credentials
sys.path.append('.')
### Import Credential Files
import credentials

################################################################
#### Function to Retrieve  Webex Room Devices Statistics
################################################################
def get_webex_device_details(access_token):
    #If access token is not present, request a new access token
    if access_token == "":
        print("Access Token Required!")
        return 

    # Webex API required Headers and Parameters
    webexheaders = {'Authorization': 'Bearer '+str(access_token)}
    webexparams = {'deviceId': '', 'name': ''}

    # Get Registered Devices
    devices_response = requests.get('https://api.ciscospark.com/v1/devices', headers=webexheaders)

    #If Authorization is Unauthorized, SHOW ERROR MSG
    if devices_response.status_code == 401:
        print("Access Token Unauthorized!")
        return 

    # xAPI Commands to be retrieved
    query_items = ['Network[1].IPv4.Address','Audio.Volume','SystemUnit.State.NumberOfActiveCalls','SystemUnit.State.NumberOfInProgressCalls','Cameras.Camera[1].LightingConditions','RoomAnalytics.AmbientNoise.Level.A','RoomAnalytics.PeopleCount.Current','RoomAnalytics.PeoplePresence','RoomAnalytics.Sound.Level.A','Standby.State','SystemUnit.Hardware.Monitoring.Temperature.Status']

    devices_result = []
    # Collect details and commands from Registered Devices
    for device in devices_response.json().get("items"):
        # Variable Initialiation
        device_status = {}
        device_status["deviceId"] = device["id"]
        device_status["connectionStatus"] = device["connectionStatus"]
        webexparams["deviceId"] = device["id"]
        # Get Device Details
        response = requests.get('https://api.ciscospark.com/v1/devices/'+device["id"], headers=webexheaders)
        # Get Device xAPI Statuses
        if device["connectionStatus"] == "connected" or device["connectionStatus"] == "connected_with_issues":
            for item in query_items:
                webexparams['name'] = item
                response = requests.get('https://api.ciscospark.com/v1/xapi/status', headers=webexheaders, params=webexparams)
                # Allow to Serialize dictionary query.
                response_json = benedict(response.json(), keypath_separator='.')
                device_status[item] = response_json.search(item.split('.')[-1], in_keys=True, in_values=False, exact=True, case_sensitive=False)[0][2]
        # Save data to influx
        devices_result.append(device_status)

    return (devices_result, access_token)

################################################################
#### MAIN FUNCTION, used only for when you call the file.
################################################################
if __name__ == "__main__":
    #Check if Webex Token into Credentials file
    if credentials.webex_token == "":
        print("Access Token Required! Please update credentials file with your BOT API Token.")
        exit()

    #Collect Devices Details
    devices_result, access_token = get_webex_device_details(credentials.webex_token)
    #Print Devices Details
    for result in devices_result:
        print(json.dumps(result, sort_keys=True,indent=4, separators=(',', ': ')))  
