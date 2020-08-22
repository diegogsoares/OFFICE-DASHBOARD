### Import Needed Libraries
from flask import Flask
from flask import request,send_file
from flask_apscheduler import APScheduler
import os, time, datetime,json

# Import modules needed for the APP
import credentials
from modules import webex
from modules import meraki
from modules import dnaspaces
from modules import save_data

# Set Global Variables
basedir = os.path.abspath(os.path.dirname(__file__))

################################################################
###     Define Reocurring Tasks
################################################################
# Define jobs to run and its frequency
class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'new-app:get_webex_devices', 'args': (),
            'trigger': 'interval', 'seconds': 30
        },{
            'id': 'job2',
            'func': 'new-app:get_meraki_dashboard', 'args': (),
            'trigger': 'interval', 'seconds': 60
        },{
            'id': 'job3',
            'func': 'new-app:get_meraki_endpoints', 'args': (),
            'trigger': 'interval', 'seconds': 30
        },{
            'id': 'job4',
            'func': 'new-app:get_dnaspaces', 'args': (),
            'trigger': 'interval', 'seconds': 30
        }
    ]
    
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }
    
    SCHEDULER_API_ENABLED = True

#Collect Information from Webex Devices
def get_webex_devices():
    t1 = datetime.datetime.now()
    # Find Webex devices and collect info
    devices_result, access_token = webex.get_webex_device_details(credentials.webex_token)
    #Save info from all devices
    save_data.write_list(devices_result,"webex_devices","webex")
    t2 = datetime.datetime.now()
    #Log Excecution
    print("Webex Devices Info Collected and Saved! - "+str(t2 - t1))
    return
#Collect Information from DNA Spaces
def get_dnaspaces():
    t1 = datetime.datetime.now()
    #Get DNA Spaces Client Information
    clients,device_types,device_perfloor = dnaspaces.get_clients(credentials.dnaspaces_token)
    #Get DNA Spaces MAP Elements
    map_elements = dnaspaces.get_elements(credentials.dnaspaces_token)
    #Get DNA Spaces MAP Images
    floor_images = dnaspaces.get_floor_images(credentials.dnaspaces_token,map_elements)
    #Save info Collected
    save_data.write_list(clients,"clients","dnaspaces")
    save_data.write_list(device_types,"device_types","dnaspaces")
    save_data.write_list(device_perfloor,"devices_floor","dnaspaces")
    save_data.write_list(map_elements,"map_elements","dnaspaces")
    save_data.write_list(floor_images,"floor_images","dnaspaces")

    t2 = datetime.datetime.now()
    #Log Excecution
    print("DNA Spaces Info Collected and Saved! - "+str(t2 - t1))
    return
#Collect Information from Meraki Dashboard
def get_meraki_dashboard():
    time.sleep(8)
    t1 = datetime.datetime.now()
    # Collect Meraki Dashboard information
    dashboard_result = meraki.find_meraki_dashboard(credentials.meraki_org_id)
    #Save information collected
    for key in dashboard_result:
        primed_result = meraki.prime_meraki_data(dashboard_result[key])
        save_data.write_list(primed_result,key,"meraki")
    t2 = datetime.datetime.now()
    #Log Excecution
    print("Meraki Dashboard Info Collected and Saved! - "+str(t2 - t1))
    return
#Collect Information from Meraki Connected Devices
def get_meraki_endpoints():
    t1 = datetime.datetime.now()
    # Collect Meraki Client information
    clients_result = meraki.find_meraki_clients(credentials.meraki_org_id)
    #Save information collected
    for key in clients_result:
        primed_result = meraki.prime_meraki_data(clients_result[key])
        save_data.write_list(primed_result,key,"meraki")
    t2 = datetime.datetime.now()
    #Log Excecution
    print("Meraki Clients Info Collected and Saved! - "+str(t2 - t1))
    #############################################################################
    t1 = datetime.datetime.now()
    # Collect Meraki Camera information
    cameras_result = meraki.find_meraki_camera(credentials.meraki_org_id)
    #Save information collected
    for key in cameras_result:
        primed_result = meraki.prime_meraki_data(cameras_result[key])
        save_data.write_list(primed_result,key,"meraki")
    t2 = datetime.datetime.now()
    delta = t2 - t1
    #Log Excecution
    print("Meraki Cameras Info Collected and Saved! - "+str(delta))
    return

################################################################
###     Define FLASK APP and enable Job Scheduling
################################################################
# Initialize Flask
app = Flask(__name__)
app.config.from_object(Config())
# Create a Scheduler to execute periodic data collection
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()    

################################################################
###     Define Flask Views
################################################################
# Index View
@app.route('/', methods=['GET', 'POST'])
def index():
    return ("Welcome to OFFICE DASHBOARD APP!")

# Image View
@app.route('/image/<image_file>')
def image(image_file):
    #Retrive Images
    if os.path.isfile(os.path.join(basedir, "images/"+image_file)):
        if ".png" in image_file:
            return send_file(os.path.join(basedir, "images/"+image_file), mimetype="image/png", cache_timeout=-1)
        else:
            return send_file(os.path.join(basedir, "images/"+image_file), mimetype="image/jpeg", cache_timeout=-1)
    #If image does not exist
    return ("NOT a valid file!")

# DNA Spaces Notifications POST URL 
@app.route('/dnaspaces-notification/', methods=['GET', 'POST'])
def dnaspaces_notification():
    if request.method == 'POST':
        t1 = datetime.datetime.now()
        save_data.write_list(request.json,"notifications","dnaspaces")
        t2 = datetime.datetime.now()
        print("DNA Spaces Notification Posted. - "+str(t2-t1))
        return ("DNA Spaces Notification Posted.")
    
    return ("DNA Spaces Notification URL.")

# Meraki Location POST URL
@app.route('/location/<validator>', methods=['GET', 'POST'])
def location(validator):
    t1 = datetime.datetime.now()
    # Save Meraki Location
    result,message,code = meraki.save_meraki_location(request,validator)
    t2 = datetime.datetime.now()
    save_data.write_list(result,"meraki_location","meraki")
    #Log Excecution
    print("Meraki Location Posted. - "+str(t2-t1))
    #Return result to View Call
    return (message,code)

# MV Alert POST URL
@app.route('/mvalert', methods=['GET', 'POST'])
def alert():
    t1 = datetime.datetime.now()
    # Analyze MV Camera Notification
    result = meraki.analyze_camera_alert(request.json)
    # Save Analysis result
    for key in result:
        save_data.write_list(result[key],key,"meraki")
    t2 = datetime.datetime.now()    
    #Log Excecution
    print("Meraki MV Notification Saved! - "+str(t2-t1))
    #Return result to View Call
    return ("Posted MV Notification.")

################################################################
###    Start APP
################################################################
if __name__ == '__main__':
    # Start Flask
    app.run(host='0.0.0.0',debug=True, use_reloader=False)