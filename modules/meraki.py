### Import Needed Libraries
import sys, os, requests, time, json, boto3, collections
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from benedict import benedict

### Set Correct Directories
basedir = os.path.abspath(os.path.dirname(__file__))
rootdir = os.path.normpath(os.path.join(basedir, "../"))
imagedir = os.path.normpath(os.path.join(basedir, "../images/"))
### Set proper working directory to import Credentials
sys.path.append('.')
### Import Credential Files
import credentials
### Initialize Meraki SDK
meraki = MerakiSdkClient(credentials.meraki_api_dashboard_key)

#######################################################################################
########   Standalone Functions
#######################################################################################
################################################################
###    GET input if Script runs as standalone
################################################################
def get_input():
    ### GET ORG ID
    #Check if Meraki Org id is into Credentials file
    if credentials.meraki_org_id != "":
        org_id = credentials.meraki_org_id
    else: # Ask for Credentials Token
        org_id = input("If you know your Meraki Organization ID paste here, or hit enter: ")
        save_org_id(org_id)
    #If Token still empty, generate a Token
    if org_id == "":
        org_id = get_org_id()
    
    ### GET PRINT OPTION
    #What is the Print option
    print("1: Raw JSON")
    print("2: Primed JSON")
    #GET input
    inp = int(input("Enter a number: "))
    #Evaluate Input
    if inp == 1:
        option = "raw"
    elif inp == 2:
        option = "primed"
    else:
        print("Invalid input!")
        exit()

    return(org_id,option)

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
###    Print result if Script runs as standalone
################################################################
def print_result(dashboard,client,camera,option):
    #Print RAW JSON
    if option == "raw":
        for key in dashboard:
            print("#########################")
            print("##### DASHBOARD - "+key)
            print("#########################")
            print(json.dumps(dashboard[key], sort_keys=True,indent=4, separators=(',', ': ')))
        for key in client:
            print("#########################")
            print("##### CLIENT - "+key)
            print("#########################")
            print(json.dumps(client[key], sort_keys=True,indent=4, separators=(',', ': ')))
        for key in camera:
            print("#########################")
            print("##### CAMERA - "+key)
            print("#########################")
            print(json.dumps(camera[key], sort_keys=True,indent=4, separators=(',', ': ')))
    #Print Primed JSON
    elif option == "primed":
        for key in dashboard:
            print("#########################")
            print("##### DASHBOARD - "+key)
            print("#########################")
            for item in dashboard[key]:
                print(json.dumps(flatten_json(item, sep='_'), sort_keys=True,indent=4, separators=(',', ': ')))
        for key in client:
            print("#########################")
            print("##### CLIENT - "+key)
            print("#########################")
            for item in client[key]:
                print(json.dumps(flatten_json(item, sep='_'), sort_keys=True,indent=4, separators=(',', ': ')))
        for key in camera:
            print("#########################")
            print("##### CAMERA - "+key)
            print("#########################")
            for item in camera[key]:
                print(json.dumps(flatten_json(item, sep='_'), sort_keys=True,indent=4, separators=(',', ': ')))  

    return

#######################################################################################
########   Auxiliary Functions
#######################################################################################
################################################################
###    GET Meraki Org id
################################################################
def get_org_id():
    # Collect Organization
    try:
        org = meraki.organizations.get_organizations()[0]
    except Exception as e:
        print("Unexpected error:", e)
    save_org_id(org["id"])

    return org["id"]

################################################################
###    Save Meraki Org id
################################################################
def save_org_id(org_id):
    #Open and read Credentials file
    f=open(rootdir+"/credentials.py","r+")
    a=f.readlines()
    #Search for webex token line
    for line in a:
        if line.startswith("meraki_org_id"):
            p=a.index(line)
    #so now we have the position of the line which to be modified
    a[p]="meraki_org_id = \'"+org_id+"\'\n"
    #Erase all data from the file
    f.seek(0)
    f.truncate() 
    f.close()
    #so now we have an empty file and we will write the modified content now in the file
    o=open(rootdir+"/credentials.py","w")
    for i in a:
        o.write(i)
    o.close()
    
    return 

################################################################
###    GET Image
################################################################
def get_image(url):
    # Get Image from URL
    response_code = count = 0
    while response_code != 200 and count <10:
        image = requests.get(url, allow_redirects=True)
        response_code = image.status_code
        count += 1
        time.sleep(1)

    return image

################################################################
###    Prime Meraki Data
################################################################
def prime_meraki_data(data):
    result = []
    for item in data:
        #print(item)
        b = benedict(item, keypath_separator='.')
        b = b.flatten(separator='_')
        #print(b)
        for key in item:
            #Evaluate if Dictionary Key is a list
            if type(item[key]) is list:
                new_dict = {}
                #Evaluate if Dictionary Key is NOT an Empty list
                if item[key]:
                    new_dict[key] = ''
                    count = 0
                    #Transform list into a sting
                    for value in item[key]:
                        if type(value) == dict:
                            l = []
                            l.append(value)
                            new_dict[key+"_"+str(count)] = prime_meraki_data(l)[0]
                            count += 1
                        else:
                            if new_dict[key] == '':
                                new_dict[key] = str(new_dict[key])+str(value)
                            else:
                                new_dict[key] = str(new_dict[key])+", "+str(value)
                    if count != 0:
                        new_dict[key] = count
                    flatten_dict = benedict(new_dict, keypath_separator='.').flatten(separator='_')
                    b.remove(key)
                    b.merge(flatten_dict)
                else:
                    new_dict[key] = "Empty"
                    b.remove(key)
                    b.merge(new_dict)   
        result.append(b)

    return (result)

#######################################################################################
########   AWS Functions
#######################################################################################
################################################################
###    Prime AWS Rekognition
################################################################
def prime_aws_rekognition(result,measurement):
    # Prime AWS Rekognition FACE_DETECT
    if measurement == "rekognition_face":
        emotion_result = {}
        b = benedict(result, keypath_separator='.')
        b = b.flatten(separator='_')
        for item in b["Emotions"]:
            emotion_result["emotion_"+item["Type"]+"_confidence"] = item["Confidence"]
        b.merge(emotion_result)
        b.remove(['Landmarks','Emotions'])
        return b
    
    # Prime AWS Rekognition FACE_DETECT
    elif measurement == "rekognition_objects":
        rekognition_result = {}
        rekognition_result["object_count"] = len(result["Instances"])       
        rekognition_result["object_name"] = result["Name"]
        rekognition_result["object_confidence"] = result["Confidence"]
        return rekognition_result
        
    return 

################################################################
###    Analyze Snapshoot using AWS Rekognition
################################################################
def analyze_snapshot(url):
    # Get Meraki Snapshot Image
    imgbytes = get_image(url)
    # Create an AWS Session to post on image analytics service
    session = boto3.Session(credentials.aws_access_key_id,credentials.aws_secret_access_key)
    client = session.client('rekognition',credentials.aws_region)
    # Get analytics on face detection
    try:
        face_response = client.detect_faces(Image={'Bytes': imgbytes.content}, Attributes=['ALL'])
    except Exception as e:
        print("FACE DETECTION FAILED:", e)
        pass
    # Prime Face Attributes
    face_result_list = []
    if face_response.get("FaceDetails"):
        for item in face_response["FaceDetails"]:
            face_result_list.append(prime_aws_rekognition(item,"rekognition_face"))

    # Get analytics on image objects
    try:
        label_response = client.detect_labels(Image={'Bytes': imgbytes.content},MaxLabels=10,MinConfidence=90)
    except Exception as e:
        print("LABEL DETECTION FAILED:", e)
        pass
    # Prime image objects
    label_result_list = []
    if label_response.get("Labels"):
        for item in label_response["Labels"]:
            label_result_list.append(prime_aws_rekognition(item,"rekognition_objects"))

    return ({"rekognition_face": face_result_list,"rekognition_objects": label_result_list})

#######################################################################################
########   Recurring Functions
#######################################################################################
################################################################
###    Collect Dashboard Information
################################################################
def find_meraki_dashboard_info(org_id):
    # Set parameter for SDK queries
    params = {"organization_id": org_id}
    # Collect Organization Networks
    try:
        nets = meraki.networks.get_organization_networks(params)
    except Exception as e:
        print("Unexpected error:", e)
    # Collect Organization Devices
    try:
        devices = meraki.devices.get_organization_devices(params)
    except Exception as e:
        print("Unexpected error:", e)
    # Collect Organization Devices Statues
    try:
        devices_status = meraki.organizations.get_organization_device_statuses(org_id)
    except Exception as e:
        print("Unexpected error:", e)
    # Find Combined Networks
    for network in nets:
        if network["type"] == "combined":
            # Collect Network SSIDs
            try:
                ssids = meraki.ssids.get_network_ssids(network["id"])
            except Exception as e:
                print("Unexpected error:", e)
            # Collect Floor Plans
            try:
                floor_plans = meraki.floorplans.get_network_floor_plans(network["id"])
            except Exception as e:
                print("Unexpected error:", e)
            # Save Floor Plan image
            for floor_plan in floor_plans:
                image = get_image(floor_plan["imageUrl"])
                f = open(os.path.join(imagedir, floor_plan["floorPlanId"]+".png"), "wb")
                f.write(image.content)
                f.close()
            # Get Camera Snapshot
            for device in devices:
                if device["model"].startswith("MV") and network["id"] == device["networkId"]:
                    try:
                        snapshoot = meraki.cameras.generate_network_camera_snapshot({"network_id": network["id"], "serial" : device["serial"]})
                    except Exception as e:
                        print("Unexpected error:", e)
                    image = get_image(snapshoot["url"])
                    f = open(os.path.join(imagedir, device["serial"]+".jpg"), "wb")
                    f.write(image.content)
                    f.close()
    return ({"networks": nets, "devices": devices, "devices_status": devices_status, "ssids": ssids, "floor_plan": floor_plans})

################################################################
###    Collect Client Information
################################################################
def find_meraki_client_info(org_id):
    # Set parameter for SDK queries
    params = {"organization_id": org_id}
    # Collect Organization Networks
    try:
        nets = meraki.networks.get_organization_networks(params)
    except Exception as e:
        print("Unexpected error:", e)
    # Find Network Information
    for network in nets:
        if network["type"] == "combined":
            params_clients = {"network_id": network["id"]}
            params_timespan = {"network_id": network["id"], "timespan": "7200"}
            # Collect All Wired/Wireless Clients
            try:
                wifi_clients = meraki.clients.get_network_clients(params_clients)
            except Exception as e:
                print("Unexpected error:", e)
            # Collect All Bluethoot Clients
            try:
                ble_clients = meraki.bluetooth_clients.get_network_bluetooth_clients(params_clients)
            except Exception as e:
                print("Unexpected error:", e)
            # Collect AirMarshal Wireless Information
            try:
                air_marshal = meraki.networks.get_network_air_marshal(params_timespan)
            except Exception as e:
                print("Unexpected error:", e)      

    return ({"wifi_clients": wifi_clients,"ble_clients": ble_clients,"air_marshal": air_marshal})

################################################################
###    Collect MV Sense Information
################################################################
def find_meraki_camera_info(org_id):
    # Set parameter for SDK queries
    params = {"organization_id": org_id}
    # Set variables
    camera_people = []
    camera_entrance = []
    # Collect Organization Networks
    try:
        nets = meraki.networks.get_organization_networks(params)
    except Exception as e:
        print("Unexpected error:", e)

    # GET CAMERA DATA
    for network in nets:
        if network["type"] == "combined":
            # Collect Network Devices
            try:
                devices = meraki.devices.get_network_devices(network["id"])
            except Exception as e:
                print("Unexpected error:", e)
            # Find Cameras  
            for device in devices:
                if device["model"].startswith("MV"):
                    # Collect people count now
                    try:
                        cam_people = meraki.mv_sense.get_device_camera_analytics_live(device["serial"])
                        cam_people["camera_serial"] = device["serial"]
                        cam_people["camera_network"] = device["networkId"]
                        cam_people["camera_name"] = device["name"]
                        camera_people.append(cam_people)
                    except Exception as e:
                        print("Unexpected error:", e)
                    # Collect Camera Analytics from past hour
                    try:
                        cam_entrance = meraki.mv_sense.get_device_camera_analytics_recent({"serial" : device["serial"]})
                        for item in cam_entrance:
                            item["camera_serial"] = device["serial"]
                            item["camera_network"] = device["networkId"]
                            item["camera_name"] = device["name"]
                            camera_entrance.append(item)
                    except Exception as e:
                        print("Unexpected error:", e)

    return ({"camera_people": camera_people,"camera_entrance": camera_entrance})

#######################################################################################
########   REST Triggered Functions
#######################################################################################
################################################################
###    Analyze MV Sense Alert
################################################################
def analyze_camera_alert(data):
    # If using Motion recap
    if data.get("alertData").get("imageUrl"):
        result = analyze_snapshot(data.get("alertData").get("imageUrl"))
    else:
        print("No Alert Data.")
    # Return Analysis Result
    return (result)

################################################################
###    Validate Location API Data and Save
################################################################
def save_meraki_location(request,validator):
    result = {}
    if request.method == 'POST':
        ### Verify if post is json
        if not request.json:
            return (result,"Meraki Location POST - Invalid data format", 400)
        else:
            locationdata = request.json
        ### Verify validator
        if validator != credentials.meraki_validator:
            return (result,"Meraki Location POST - Invalid validator", 403)
        ### Verify secret
        if locationdata["secret"] != credentials.meraki_secret:
            return (result,"Meraki Location POST - Invalid secret", 403)
        # Verify version
        if locationdata["version"] != credentials.meraki_version:
            return (result,"Meraki Location POST - Invalid version", 400)
        #Prime Data
        if type(locationdata["data"]) is dict:
            data = [locationdata["data"]]
        for item in data:
            location_result = prime_meraki_data(item.get("observations"))
            for sub_item in location_result:
                sub_item["location_y"] = sub_item["location_y"][0]
                sub_item["location_x"] = sub_item["location_x"][0]
                sub_item["type"] = locationdata.get("type")
                sub_item["apMac"] = item.get("apMac")
                sub_item["apFloors"] = item.get("apFloors")[0]
        # Return success message
        return (location_result,"Meraki Location Scanning POST Received",200)
    else:
        return (validator,"Meraki Location POST URL Accessed",200)

################################################################
#### MAIN FUNCTION, used only for when you call the file.
################################################################
if __name__ == "__main__":
    #Get Input
    org_id,option = get_input()
    
    #Get Dashboard info
    dashboard = find_meraki_dashboard_info(org_id)
    #Get Client info
    client = find_meraki_client_info(org_id)
    #Get Camera info
    camera = find_meraki_camera_info(org_id)

    #Print Results
    print_result(dashboard,client,camera,option)

    