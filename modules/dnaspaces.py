### Import Needed Libraries
import sys, requests, json, collections

### Set proper working directory to import Credentials
sys.path.append('.')
### Import Credential Files
import credentials

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
#### Get DNA Spaces MAP Elements
################################################################
def get_floor_images(credentials):
    # Variable Initialiation
    headers = {"Authorization": "Bearer "+credentials, "Content-Type": "application/json"}
    # Get MAP Elements
    map_elements = get_dnaspaces_elements(credentials)
    # GET images for floors
    for i in map_elements:
        if i["level"] == "FLOOR":
            element_resp = requests.get('https://dnaspaces.io/api/location/v1/map/elements/'+i["id"], headers=headers)
            image_name = element_resp.json().get("map").get("details").get("image").get("imageName")
            print("################################################################")
            print("Name : "+str(i["name"]))
            print("Hierarchy : "+str(element_resp.json().get("map").get("relationshipData").get("ancestors")))
            print("Image Name : "+str(image_name))
            
            #image = requests.get('https://dnaspaces.io/api/location/v1/map/images/floor/'+image_name, headers=headers)

    return

################################################################
#### MAIN FUNCTION, used only for when you call the file.
################################################################
if __name__ == "__main__":
    #Get DNA Spaces Clients
    clients_resp,device_types_resp,device_perfloor_resp = get_dnaspaces_clients(credentials.dnaspaces_token)
    #Get DNA Spaces MAP Elements
    map_elements = get_dnaspaces_elements(credentials.dnaspaces_token)


    #Prime data
    clean_list = prime_influx(clients_resp.json().get("results"))
    
    #Get Clients
    print("##############\n##  List of Clients\n##############")
    #for item in clean_list:
    #    print(json.dumps(item, sort_keys=True,indent=4, separators=(',', ': ')))

    #Get Device Types
    print("##############\n##  Summary of Device Types\n##############")
    print(json.dumps(prime_influx(device_types_resp.json().get("results")), sort_keys=True,indent=4, separators=(',', ': ')))
    #Get Device Count
    print("##############\n##  Device Counts\n##############")
    print(json.dumps(prime_influx(device_perfloor_resp.json().get("results")), sort_keys=True,indent=4, separators=(',', ': ')))
    #Get MAP Elements
    print("##############\n##  List of MAP Elements\n##############")
    print(json.dumps(map_elements, sort_keys=True,indent=4, separators=(',', ': ')))
    #Get MAP Images
    print("##############\n##  List of MAP Images\n##############")
    get_floor_images(credentials.dnaspaces_token)