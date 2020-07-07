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
#### OAUTH2 Function to Authenticate and Retrieve Access token from Webex
################################################################
def get_webex_token():
    # Create OAUTH URL
    url_webex_authorization = 'https://api.ciscospark.com/v1/authorize?response_type=code&state=STATE_STRING&client_id='+str(credentials.webex_client_id)
    url_webex_authorization = url_webex_authorization + "&redirect_uri=" + str(parse.quote(credentials.webex_redirect_uri, safe='')) + "&scope="
    
    #### Scopes required on Authentication to have access to Devices.
    scopes = ['spark:xapi_statuses','spark:xapi_commands','spark:devices_read']
    for scope in scopes:
        url_webex_authorization = url_webex_authorization + parse.quote(scope) + parse.quote(" ")

    # Autenticate User on Credentials page
    opts = Options()
    opts.headless = True
    browser = Firefox(options=opts)
    browser.get(url_webex_authorization)
    login_user = browser.find_element_by_id('IDToken1')
    login_user.send_keys(credentials.webex_user)
    browser.find_element_by_id("IDButton2").click()
    login_pass = browser.find_element_by_id('IDToken2')
    login_pass.send_keys(credentials.webex_pass)
    browser.find_element_by_id("Button1").click()
    code_url = str(browser.current_url)

    # Retrieve Code embeded on URL
    code = parse.parse_qs(parse.urlparse(code_url).query)['code'][0]

    # Get API Token based on Generated Code
    headers = {'accept':'application/json','content-type':'application/x-www-form-urlencoded'}
    payload = ("grant_type=authorization_code&client_id={0}&client_secret={1}&code={2}&redirect_uri={3}").format(credentials.webex_client_id, credentials.webex_client_secret, code, credentials.webex_redirect_uri)
    response_token = requests.post(url='https://api.ciscospark.com/v1/access_token', data=payload, headers=headers)
    access_token = response_token.json().get("access_token")
    save_webex_token(access_token)

    return (access_token)

################################################################
#### Save Webex Token to Credentials File
################################################################
def save_webex_token(token):
    #Set correct path to credentials file
    basedir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../"))
    #Open and read Credentials file
    f=open(basedir+"/credentials.py","r+")
    a=f.readlines()
    #Search for webex token line
    for line in a:
        if line.startswith("webex_token"):
            p=a.index(line)
    #so now we have the position of the line which to be modified
    a[p]="webex_token = \'"+token+"\'\n"
    #Erase all data from the file
    f.seek(0)
    f.truncate() 
    f.close()
    #so now we have an empty file and we will write the modified content now in the file
    o=open(basedir+"/credentials.py","w")
    for i in a:
        o.write(i)
    o.close()
    
    return

################################################################
#### Function to Retrieve  Webex Room Devices Statistics
################################################################
def get_webex_device_details(access_token):
    #If access token is not present, request a new access token
    if access_token == "":
        access_token = get_webex_token()

    # xAPI Commands to be retrieved
    query_items = ['Network[1].IPv4.Address','Audio.Volume','SystemUnit.State.NumberOfActiveCalls','SystemUnit.State.NumberOfInProgressCalls','Cameras.Camera[1].LightingConditions','RoomAnalytics.AmbientNoise.Level.A','RoomAnalytics.PeopleCount.Current','RoomAnalytics.PeoplePresence','RoomAnalytics.Sound.Level.A','Standby.State','SystemUnit.Hardware.Monitoring.Temperature.Status']
    # Webex API required Headers and Parameters
    webexheaders = {'Authorization': 'Bearer '+str(access_token)}
    webexparams = {'deviceId': '', 'name': ''}

    # Get Registered Devices
    devices_response = requests.get('https://api.ciscospark.com/v1/devices', headers=webexheaders)
    #If Authorization is Unauthorized, regenerate Token and try again
    if devices_response.status_code == 401:
        access_token = get_webex_token()
        webexheaders = {'Authorization': 'Bearer '+str(access_token)}
        devices_response = requests.get('https://api.ciscospark.com/v1/devices', headers=webexheaders)
    
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
    if credentials.webex_token != "":
        access_token = credentials.webex_token
    else: # Ask for Credentials Token
        access_token = input("If you have a TOKEN paste here, or hit enter: ")
        save_webex_token(access_token)
    #If Token still empty, generate a Token
    if access_token == "":
        access_token = get_webex_token()
    #Collect Devices Details
    devices_result, access_token = get_webex_device_details(access_token)
    #Print Devices Details
    for result in devices_result:
        print(json.dumps(result, sort_keys=True,indent=4, separators=(',', ': ')))  
