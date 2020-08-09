### Import Needed Libraries
import json, os, sys
from influxdb import InfluxDBClient

### Set Global Variables
basedir = os.path.abspath(os.path.dirname(__file__))
logdir = os.path.normpath(os.path.join(basedir, "../logs/"))
### Set proper working directory to import Credentials
sys.path.append('.')
### Import Credential Files
import credentials

################################################################
###    Connect to DB
################################################################
# Start influxDB Client
client = InfluxDBClient(host='localhost', port=8086)

### Used for Troubleshooting
#client.drop_database('meraki')
#client.switch_database('dnaspaces')
#client.drop_measurement('clients')

# List Databases
dbs = client.get_list_database()
# Set required DBs
db_list = ["meraki", "webex", "dnaspaces"]
# Check if Required dbs exist
for item in db_list:
    db_status = 0
    for db in dbs:
        if db["name"] == item:
            db_status = 1
    # Create DB if does not exist
    if db_status == 0:
        client.create_database(item)

################################################################
###    Save Single Entry
################################################################
def write_data(data,measurement,db):
    ### Print to File if save_file parameter is True
    if credentials.save_file: 
        # Write to LOG file
        f= open(os.path.join(logdir, db+"_"+measurement+".log"),"a+")
        f.write(json.dumps(data)+"\n")
        f.close()
    else: ### Post to DB if save_file parameter is False
        body= []
        item_json = {}
        item_json["tags"] = {} 
        item_json["measurement"] = measurement
        item_json["fields"] = data
        body.append(item_json)
        client.write_points(body,database=db,time_precision='ms') 
    
    return

################################################################
###    Save List of entries
################################################################
def write_list(data_list,measurement,db):
    if isinstance(data_list, list):
        for data in data_list: 
            write_data(data,measurement,db)
    
    return