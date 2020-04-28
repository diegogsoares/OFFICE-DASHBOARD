import json
from datetime import datetime
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from influxdb import InfluxDBClient

# Start influxDB Client
client = InfluxDBClient(host='localhost', port=8086)
#client.drop_database('meraki')
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

################################################################
###    Prime Devices Info
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

################################################################
###    Prime Air Marshal Information
################################################################
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
    # Format item to be able to filter in Grafana
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
###    Post info to DB
################################################################
def meraki_post_to_db(result,measurement):

    if type(result) is list:
        for item in result:
            # Remove Lists before posting
            item = prime_influx_data(item,measurement)

            body= []
            item_json = {}
            item_json["tags"] = {} 
            item_json["measurement"] = measurement
            item_json["fields"] = item
            body.append(item_json)
            client.write_points(body,database='meraki',time_precision='ms')

    else:
        # Remove Lists before posting
        item = prime_influx_data(result,measurement)
        
        body = []
        body_json = {}
        body_json["measurement"] = measurement
        body_json["tags"] = {}
        body_json["fields"] = item
        body.append(body_json)
        client.write_points(body,database='meraki',time_precision='ms')    
    
    return

def find_meraki_dashboard_info(meraki):
    params = {}
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params["organization_id"] = str(orgs["id"])
    
    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)
    # Print reult to Screen
    #print(nets)
    # Post reult to DB
    meraki_post_to_db(nets,"networks")

    for network in nets:
        if network["type"] == "combined":
            # Collect Floor plans
            floor_plan = meraki.floorplans.get_network_floor_plans(network["id"])
            # Print reult to Screen
            #print(floor_plan)
            # Post reult to DB
            meraki_post_to_db(floor_plan,"floor_plan")

    # Collect Organization Devices
    devices = meraki.devices.get_organization_devices(params)
    # Print reult to Screen
    #print(devices)
    # Post reult to DB
    meraki_post_to_db(devices,"devices")
    
    # Collect Organization Devices Statues
    devices_status = meraki.organizations.get_organization_device_statuses(orgs["id"])
    # Print reult to Screen
    #print(devices_status)
    # Post reult to DB
    meraki_post_to_db(devices_status,"devices_status")

    # Find Conmined Networks
    for network in nets:
        if network["type"] == "combined":
            params_clients = {}
            params_clients['network_id'] = network["id"]
            ssids = meraki.ssids.get_network_ssids(network["id"])
            # Print reult to Screen
            #print(ssids)
            # Post reult to DB
            meraki_post_to_db(ssids,"ssids")
    
    print ("Posted DASHBOARD.")
    
    return

def find_meraki_client_info(meraki):
    params = {}
    # Collect Organization
    orgs = meraki.organizations.get_organizations()[0]
    params["organization_id"] = str(orgs["id"])

    # Collect Organization Networks
    nets = meraki.networks.get_organization_networks(params)
    # Collect Organization Devices
    devices = meraki.devices.get_organization_devices(params)
    
    # Find Cameras
    for device in devices:
        if device["model"].startswith("MV"):
            collect = {}
            collect['serial'] = device["serial"]
            # Collect people count now
            camera_people = meraki.mv_sense.get_device_camera_analytics_live(device["serial"])
            # Collect Camera Analytics from past hour
            camera_entrance = meraki.mv_sense.get_device_camera_analytics_overview(collect)

    # Find Network Information
    for network in nets:
        if network["type"] == "combined":
            params_clients = {}
            params_clients['network_id'] = network["id"]
            
            # Collect All Wired/Wireless Clients
            wifi_clients = meraki.clients.get_network_clients(params_clients)
            # Print result to Screen
            #print(devices_status)
            # Post reult to DB
            meraki_post_to_db(wifi_clients,"wifi_clients")

            # Collect All Bluethoot Clients
            ble_clients = meraki.bluetooth_clients.get_network_bluetooth_clients(params_clients)
            # Print result to Screen
            #print(devices_status)
            # Post reult to DB
            meraki_post_to_db(ble_clients,"ble_clients")

            # Collect AirMarshal Wireleass Information
            air_marshal = meraki.networks.get_network_air_marshal(params_clients)
            # Print result to Screen
            #print(devices_status)
            # Post reult to DB
            meraki_post_to_db(air_marshal,"air_marshal")


    
    print ("Posted CLIENTS.")

    return