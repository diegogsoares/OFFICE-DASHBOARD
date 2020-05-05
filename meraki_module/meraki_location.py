import os
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
                item = prime_meraki_location(item)
                # Save to DB
                post_data(item,measurement)
        else:
            # Remove Lists before posting
            item = prime_meraki_location(result)
            # Save to DB
            post_data(item,measurement)     
    return

################################################################
###    Prime Location API
################################################################
def prime_meraki_location(locationdata):

    device_location = {}
    data = locationdata["data"]
    for key in data.keys():
        if key == "observations":
            for observation in data[key]:
                for item in observation.keys():
                    if item == "location":
                        device_location["location_lat"] = float(observation["location"]["lat"])
                        device_location["location_lon"] = float(observation["location"]["lng"])
                        device_location["location_unc"] = float(observation["location"]["unc"])
                        device_location["location_x"] = float(observation["location"]["x"][0])
                        device_location["location_y"] = float(observation["location"]["y"][0])
                    else:
                        if observation[item]:
                            device_location[item] = observation[item]
                        else:
                            device_location[item] = "EMPTY"
                device_location["type"] = locationdata["type"]
                device_location["apMac"] = data["apMac"]
                device_location["apFloors"] = data["apFloors"][0]

    return (device_location)

################################################################
###    Validate Location API Data and Save
################################################################
def save_meraki_location(request,validator,credentials):
    if request.method == 'POST':

        ### Verify if post is json
        if not request.json:
            return ("invalid data", 400)

        locationdata = request.json
        ### Verify validator
        if validator != credentials.meraki_validator:
            print("validator invalid:", validator)
            return ("invalid validator", 403)

        ### Verify secret
        if locationdata["secret"] != credentials.meraki_secret:
            print("secret invalid:", locationdata["secret"])
            return ("invalid secret", 403)

        # Verify version
        if locationdata["version"] != credentials.meraki_version:
            print("invalid version")
            return ("invalid version", 400)

        # Save data
        save_data(locationdata,"meraki_location")
        # Return success message
        print("Posted LOCATION.")
        return "Location Scanning POST Received"

    else:
        print ("Location URL Accessed")
        return validator
