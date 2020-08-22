### Import Needed Libraries
import sys, os, time, requests, json, collections

### Set Correct Directories
basedir = os.path.abspath(os.path.dirname(__file__))
imagedir = os.path.normpath(os.path.join(basedir, "../images/"))

### Set proper working directory to import Credentials
sys.path.append('.')

### Import Credential Files
import credentials

#######################################################################################
########   Data Translation Layer
#######################################################################################
################################################################
#### Flatten JSON
################################################################
def flatten_json(d,sep="_"):
    obj = collections.OrderedDict()
    def recurse(t,parent_key=""):
        if isinstance(t,list):
            if len(t) == 0:
                obj[parent_key] = "EMPTY"
            for i in range(len(t)):
                recurse(t[i],parent_key + sep + str(i) if parent_key else str(i))
        elif isinstance(t,dict):
            for k,v in t.items():
                recurse(v,parent_key + sep + k if parent_key else k)
        else:
            obj[parent_key] = t
    recurse(d)
    return dict(obj)

################################################################
#### Prime data to facilitate search in influxDB
################################################################
def prime_influx(raw_list):
    flatten_list = []
    if type(raw_list) is list:
        # Interact over Items on a list
        for item in raw_list:
            # Flatten the JSON Item
            flatten_item = flatten_json(item, sep='_')
            # Sanitize for influx Queries
            for key in flatten_item:
                if type(flatten_item[key]) is bool:
                    if flatten_item[key] == False:
                        flatten_item[key] = "INCORRECT"
                    elif flatten_item[key] == True:
                        flatten_item[key] = "CORRECT"
                if flatten_item[key] == None:
                    flatten_item[key] = "EMPTY"
            flatten_list.append(flatten_item)
    elif type(raw_list) is dict:
        # Flatten the JSON Item
        flatten_item = flatten_json(raw_list, sep='_')
        # Sanitize for influx Queries
        for key in flatten_item:
            if type(flatten_item[key]) is bool:
                if flatten_item[key] == False:
                    flatten_item[key] = "INCORRECT"
                elif flatten_item[key] == True:
                    flatten_item[key] = "CORRECT"
            if flatten_item[key] == None:
                flatten_item[key] = "EMPTY"
        flatten_list.append(flatten_item)
    
    return flatten_list

################################################################
#### Prime coordiantes on clients
################################################################
def prime_client(raw_list):
    # Adjust Coordinates to float
    for item in raw_list:
        item["rawCoordinates_0"] = float(item["rawCoordinates_0"])
        item["rawCoordinates_1"] = float(item["rawCoordinates_1"])
        item["coordinates_0"] = float(item["coordinates_0"])
        item["coordinates_1"] = float(item["coordinates_1"])
    
    return raw_list

#######################################################################################
########   Data Collection Layer
#######################################################################################
################################################################
###    GET Image
################################################################
def get_image(url,credentials):
    # Set Variables
    headers = {"Authorization": "Bearer "+credentials, "Content-Type": "application/json"}
    response_code = count = 0
    # Get Image from URL
    image = requests.get(url, headers=headers, allow_redirects=True)
    response_code = image.status_code
    # Check if images was retrieved and retry if needed.
    while response_code != 200 and count <3:
        image = requests.get(url, headers=headers, allow_redirects=True)
        response_code = image.status_code
        count += 1
        time.sleep(1)

    return image

################################################################
#### Get DNA Spaces Clients
################################################################
def get_dnaspaces_clients(credentials):
    # Variable Initialiation
    headers = {"Authorization": "Bearer "+credentials, "Content-Type": "application/json"}
    # Get Device Details
    clients_resp = requests.get('https://dnaspaces.io/api/location/v1/clients', headers=headers)
    device_types_resp = requests.get('https://dnaspaces.io/api/location/v1/clients/count?groupBy=deviceType', headers=headers)
    device_perfloor_resp = requests.get('https://dnaspaces.io/api/location/v1/clients/floors', headers=headers)

    return (clients_resp,device_types_resp,device_perfloor_resp)

################################################################
#### Get DNA Spaces MAP Elements
################################################################
def get_dnaspaces_elements(credentials):
    # Variable Initialiation
    headers = {"Authorization": "Bearer "+credentials, "Content-Type": "application/json"}
    # Get MAP Hierarchy
    map_hierarchy_resp = requests.get('https://dnaspaces.io/api/location/v1/map/hierarchy', headers=headers)
    #Search for all elements in Hierarchy
    obj = []
    def recurse_map(t):
        item = {}
        if type(t) is list:
            for i in t:
                item["name"] = i.get("name") 
                item["level"] = i.get("level")
                item["id"] = i.get("id")
                if i.get("relationshipData").get("children"):
                    recurse_map (i.get("relationshipData").get("children"))
                obj.append(item)
    recurse_map(map_hierarchy_resp.json().get("map"))

    return obj

################################################################
#### Get DNA Spaces MAP Images
################################################################
def get_floor_images(credentials,map_elements):
    # Variable Initialization
    headers = {"Authorization": "Bearer "+credentials, "Content-Type": "application/json"}
    # GET images for floors
    obj = []
    for i in map_elements:
        if i["level"] == "FLOOR":
            item = {}
            element_resp = requests.get('https://dnaspaces.io/api/location/v1/map/elements/'+i["id"], headers=headers)
            image_name = element_resp.json().get("map").get("details").get("image").get("imageName")
            # Build JSON Structure for Floor Image
            item["floor_name"] = str(i.get("name"))
            item["floor_id"] = str(i.get("id"))
            item["hierarchy"] = str(element_resp.json().get("map").get("relationshipData").get("ancestors"))
            item["image_name"] = str(image_name)
            item["image_url"] = str("https://dnaspaces.io/api/location/v1/map/images/floor/"+image_name)
            #Append JSON Structure to response
            obj.append(item)
            #Save Image on images folder
            image = get_image(item["image_url"],credentials)
            print (os.path.join(imagedir, item["floor_id"]+".png"))
            f = open(os.path.join(imagedir, item["floor_id"]+".png"), "wb")
            f.write(image.content)
            f.close()

    return (obj)

################################################################
#### MAIN FUNCTION, used only for when you call the file.
################################################################
if __name__ == "__main__":
    #Get DNA Spaces Clients
    clients_resp,device_types_resp,device_perfloor_resp = get_dnaspaces_clients(credentials.dnaspaces_token)
    #Get DNA Spaces MAP Elements
    map_elements = get_dnaspaces_elements(credentials.dnaspaces_token)
    #Get DNA Spaces MAP Images
    floor_images = get_floor_images(credentials.dnaspaces_token,map_elements)

    #Prime data
    clean_list = prime_client(prime_influx(clients_resp.json().get("results")))
    
    ################################################################
    #### Print Results
    ################################################################
    #Print Clients
    print("##############\n##  List of Clients\n##############")
    for item in clean_list:
        print(json.dumps(item, sort_keys=True,indent=4, separators=(',', ': ')))
    #Print Device Types
    print("##############\n##  Summary of Device Types\n##############")
    print(json.dumps(prime_influx(device_types_resp.json().get("results")), sort_keys=True,indent=4, separators=(',', ': ')))
    #Print Device Count
    print("##############\n##  Device Counts\n##############")
    print(json.dumps(prime_influx(device_perfloor_resp.json().get("results")), sort_keys=True,indent=4, separators=(',', ': ')))
    #Print MAP Elements
    print("##############\n##  List of MAP Elements\n##############")
    print(json.dumps(map_elements, sort_keys=True,indent=4, separators=(',', ': ')))
    #Print MAP Images
    print("##############\n##  List of MAP Images\n##############")
    print(json.dumps(floor_images, sort_keys=True,indent=4, separators=(',', ': ')))