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
                item = prime_influx_data(item,measurement)
                # Save to DB
                post_data(item,measurement)
        else:
            # Remove Lists before posting
            item = prime_influx_data(result,measurement)
            # Save to DB
            post_data(item,measurement)     
    return

################################################################
###    Prime DATA
################################################################
def prime_devices(item):
    if str(item["model"]).startswith("MR"):
        item["devicetype"] = "AP"
    elif str(item["model"]).startswith("MV"):
        item["devicetype"] = "CAMERA"
    elif str(item["model"]).startswith("MS"):
        item["devicetype"] = "SWITCH"
    elif str(item["model"]).startswith("MX"):
        item["devicetype"] = "FIREWALL"
    else:
        item["devicetype"] = "OTHER"
    
    return (item)

def prime_air_marshal(item):
    bssids_count = len(item["bssids"])
    channels_count = len(item["channels"])
    rssi = 0
    for bssid in item["bssids"]:
        for device in bssid["detectedBy"]:
            if device["rssi"] >= rssi:
                rssi = device["rssi"]

    item["bssids_count"] = bssids_count
    item["channels_count"] = channels_count
    item["hih_rssi"] = rssi

    return (item)

################################################################
###    Influxdb does not accept lists in the field field.
###    Delete all Lists from JSON prior to Post to Influx.
################################################################
def prime_influx_data(item,measurement):
    # Format items to be able to filter in Grafana
    item_string = json.dumps(item)
    clean_item = item_string.replace(': true,',': "OK",').replace(': false,',': "NOK",').replace(': true}',': "OK"}').replace(': false}',': "NOK"}')
    item = json.loads(clean_item)
    
    if measurement == "devices":
        item = prime_devices(item)
    elif measurement == "air_marshal":
        item = prime_air_marshal(item)
    
    del_dict_keys = []
    for key in item:
        if type(item[key]) is dict:
            del_dict_keys.append(key)

    for del_dict_key in del_dict_keys:
        del item[del_dict_key]

    del_list_keys = []
    for key in item:
        if type(item[key]) is list:
            del_list_keys.append(key)

    for del_list_key in del_list_keys:
        del item[del_list_key]

    return (item)

################################################################
###    Collect Dashboard Information
################################################################
def find_meraki_dashboard_info(meraki):
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params = {"organization_id": orgs["id"]}
    
    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)
    save_data(nets,"networks")            
    # Collect Organization Devices
    devices = meraki.devices.get_organization_devices(params)
    save_data(devices,"devices")    
    # Collect Organization Devices Statues
    devices_status = meraki.organizations.get_organization_device_statuses(orgs["id"])
    save_data(devices_status,"devices_status")

    # Find Combined Networks
    for network in nets:
        if network["type"] == "combined":
            # Collect Network SSIDs
            ssids = meraki.ssids.get_network_ssids(network["id"])
            save_data(ssids,"ssids")
            # Collect Network SSIDs
            floor_plan = meraki.floorplans.get_network_floor_plans(network["id"])
            save_data(floor_plan,"floor_plan")
                
    print ("Posted DASHBOARD.")
    return

################################################################
###    Collect Client Information
################################################################
def find_meraki_client_info(meraki):
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params = {"organization_id": orgs["id"]}
    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)
    
    # Find Network Information
    for network in nets:
        if network["type"] == "combined":
            params_clients = {"network_id": network["id"]}
            params_timespan = {"network_id": network["id"], "timespan": "7200"}

            # Collect All Wired/Wireless Clients
            wifi_clients = meraki.clients.get_network_clients(params_clients)
            save_data(wifi_clients,"wifi_clients")
            # Collect All Bluethoot Clients
            ble_clients = meraki.bluetooth_clients.get_network_bluetooth_clients(params_clients)
            save_data(ble_clients,"ble_clients")
            # Collect AirMarshal Wireleass Information
            air_marshal = meraki.networks.get_network_air_marshal(params_timespan)
            save_data(air_marshal,"air_marshal")

    print ("Posted CLIENTS.")
    return