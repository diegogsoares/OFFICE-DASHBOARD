import boto3, json, os, requests, time
from influxdb import InfluxDBClient

basedir = os.path.abspath(os.path.dirname(__file__))
logdir = os.path.normpath(os.path.join(basedir, "../logs/"))
imagedir = os.path.normpath(os.path.join(basedir, "../images/"))
os.chdir('../')

import credentials

################################################################
###    Connect to DB
################################################################
# Start influxDB Client
client = InfluxDBClient(host='localhost', port=8086)
# List Databases
dbs = client.get_list_database()
# Check if meraki db exists
db_status = 0
for db in dbs:
    if db["name"] == "meraki":
        db_status = 1
# Create Meraki DB if does not exist
if db_status == 0:
    client.create_database('meraki')

#client.drop_database('meraki')
#client.switch_database('meraki')
#client.drop_measurement('rekognition_face')

################################################################
###    Post Primed Data to InfluxDB
################################################################
def post_data(data,measurement):
    body= []
    item_json = {}
    item_json["tags"] = {} 
    item_json["measurement"] = measurement
    item_json["fields"] = data
    body.append(item_json)
    client.write_points(body,database='meraki',time_precision='ms')
    return

################################################################
###    Save Data Selection
################################################################
def save_data(result,measurement):
    ### Print to File if save_file parameter is True
    if credentials.save_file: 
        # Write to LOG file
        f= open(os.path.join(logdir, measurement+".log"),"a+")
        f.write(json.dumps(data)+"\n")
        f.close()
    else: ### Post to DB if save_file parameter is False
        if type(result) is list:
            for item in result:
                # Remove Lists before posting
                item = prime_meraki_sense(item,measurement)
                # Save to DB
                if item:
                    post_data(item,measurement)
        else:
            # Remove Lists before posting
            item = prime_meraki_sense(result,measurement)
            # Save to DB
            if item:
                post_data(item,measurement)     
    return

################################################################
###    Prime DATA
###    Remove nested data
################################################################
def prime_meraki_sense(result,measurement):
    # Prime Camera Analytics
    if measurement == "camera_people":
        for key1 in result["zones"].keys():
            for key2 in result["zones"][key1].keys():
                result["zones_"+key1+"_"+key2] = result["zones"][key1][key2]
        
        del result["zones"]

    # Prime AWS Rekognition FACE_DETECT
    elif measurement == "rekognition_face":
        rekognition_result = {}
        face_attributes = ["AgeRange", "Smile", "Eyeglasses", "Gender", "Emotions", "Confidence"]

        for key1 in result.keys():
            if key1 in set(face_attributes):
                if type(result[key1]) is list:
                    for item2 in result[key1]:
                        rekognition_result["emotion_"+item2["Type"]+"_confidence"] = item2["Confidence"]
                elif type(result[key1]) is dict:
                    for key2 in result[key1].keys():
                        rekognition_result[key1+"_"+key2] = result[key1][key2]
                else:
                    rekognition_result[key1] = result[key1]

        return rekognition_result
    
    # Prime AWS Rekognition FACE_DETECT
    elif measurement == "rekognition_objects":
        rekognition_result = {}
        if len(result["Instances"]) != 0:
            rekognition_result["object_count"] = len(result["Instances"])       
            rekognition_result["object_name"] = result["Name"]
            rekognition_result["object_confidence"] = result["Confidence"]
            return rekognition_result
        else:
            return

    return result

################################################################
###    GET Image
################################################################
def get_snapshot_image(url):
    # Get Meraki Snapshot Image
    response_code = 0
    while response_code != 200:
        time.sleep(1)
        image = requests.get(url, allow_redirects=True)
        response_code = image.status_code

    return image

################################################################
###    Analyze Snapshoot
################################################################
def analyze_snapshot(url):
    # Get Meraki Snapshot Image
    imgbytes = get_snapshot_image(url)

    # Create an AWS Session to post on image analytics service
    session = boto3.Session(credentials.aws_access_key_id,credentials.aws_secret_access_key)
    client = session.client('rekognition',credentials.aws_region)

    # Get analytics on face detection
    try:
        face_response = client.detect_faces(Image={'Bytes': imgbytes.content}, Attributes=['ALL'])
        
        for item in face_response["FaceDetails"]:
            save_data(item,"rekognition_face")
    except:
        print("FACE DETECTION FAILED")
        pass

    # Get analytics on image objects
    try:
        label_response = client.detect_labels(Image={'Bytes': imgbytes.content},MaxLabels=10,MinConfidence=90)
        
        for item in label_response["Labels"]:
            save_data(item,"rekognition_objects")
    except:
        print("LABEL DETECTION FAILED")
        pass
        

    return

################################################################
###    Analyze MV Sense Alert
################################################################
def analyze_camera_alert(data):
    # If using Motion recap
    if data.get("alertData").get("imageUrl"):
        analyze_snapshot(data.get("alertData").get("imageUrl"))
    else:
        print("No Alert Data.")

    print ("Posted MV Notification.")
    return ("Alert Posted!")

################################################################
###    Collect MV Sense Information
################################################################
def find_camera_data(meraki):
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params = {"organization_id": orgs["id"]}

    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)

    # Find Cameras
    for network in nets:
        if network["type"] == "combined":
            devices  = meraki.devices.get_network_devices(network["id"])
            for device in devices:
                if device["model"].startswith("MV"):
                    # Collect people count now
                    camera_people = meraki.mv_sense.get_device_camera_analytics_live(device["serial"])
                    camera_people["camera_serial"] = device["serial"]
                    save_data(camera_people,"camera_people")
                    # Collect Camera Analytics from past hour
                    camera_entrance = meraki.mv_sense.get_device_camera_analytics_recent({"serial" : device["serial"]})
                    for item in camera_entrance:
                        item["camera_serial"] = device["serial"]
                    save_data(camera_entrance,"camera_entrance")

    print ("Posted CAMERA.")
    return

