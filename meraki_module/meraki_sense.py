import json
import os
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from influxdb import InfluxDBClient

basedir = os.path.abspath(os.path.dirname(__file__))
logdir = os.path.normpath(os.path.join(basedir, "../logs/"))
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
#client.drop_measurement('meraki_location')

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
                item = prime_meraki_sense(item)
                # Save to DB
                post_data(item,measurement)
        else:
            # Remove Lists before posting
            item = prime_meraki_sense(result)
            # Save to DB
            post_data(item,measurement)     
    return

################################################################
###    Prime DATA
################################################################
def prime_meraki_sense(result,measurement):
  
    return

################################################################
###    Collect MV Sense Information
################################################################
def collect_camera_data(meraki):
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params["organization_id"] = str(orgs["id"])
    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)

    # Find Cameras
    for network in nets:
        if network["type"] == "combined":
            params = {"network_id": network["id"]}
            devices  = meraki.devices.get_network_devices(params)
            for device in devices:
                if device["model"].startswith("MV"):
                    collect = {"serial": device["serial"]} 
                    param_snapshot = {"serial": device["serial"], "network_id": network["id"]}
                    # Collect people count now
                    camera_people = meraki.mv_sense.get_device_camera_analytics_live(device["serial"])
                    save_data(camera_people,"camera_people")
                    # Collect Camera Analytics from past hour
                    camera_entrance = meraki.mv_sense.get_device_camera_analytics_recent(device["serial"])
                    save_data(camera_people,"camera_entrance")
                    # Collect Camera snapshot
                    camera_entrance = meraki.cameras.generate_network_camera_snapshot(param_snapshot)
                    save_data(camera_people,"camera_entrance")

    return

################################################################
###    Analyze MV Sense Alert
################################################################
def analyze_camera_alert(data):

    print(data)

    return ("Alert Posted!")

