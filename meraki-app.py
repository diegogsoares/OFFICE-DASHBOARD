from flask import Flask
from flask import render_template, url_for,request,redirect,flash,send_file
from flask_apscheduler import APScheduler

import credentials
from meraki_module.meraki_dashboard import *
from meraki_module.meraki_location import *
from meraki_module.meraki_sense import *

# Define a job to run and its frequency
class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'meraki-app:collect_meraki_dashboard_info', 'args': (),
            'trigger': 'interval', 'seconds': 60
        },{
            'id': 'job2',
            'func': 'meraki-app:collect_meraki_client_info', 'args': (),
            'trigger': 'interval', 'seconds': 30
        }
    ]
    SCHEDULER_API_ENABLED = True

################################################################
###     Reocurring Tasks
################################################################
#Collect Information from Meraki Dashboad
def collect_meraki_dashboard_info():
    # Initialize Meraki SDK
    meraki = MerakiSdkClient(credentials.meraki_api_dashboard_key)
    # Find Dashboard Base Information
    # Orgs, Networks, Devices, SSIDs
    find_meraki_dashboard_info(meraki)

    return

#Collect Client Information from Meraki Dashboad
def collect_meraki_client_info():
    # Initialize Meraki SDK
    meraki = MerakiSdkClient(credentials.meraki_api_dashboard_key)
    # Find Dashboard Base Information
    # Orgs, Networks, Devices, SSIDs
    find_meraki_client_info(meraki)

    return

################################################################
###     Define FLASK APP
################################################################
# Initialize Flask
app = Flask(__name__)
app.debug = True
app.config.from_object(Config())
# Create a Scheduler to execute periodic data collection
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()    

################################################################
###     Views
################################################################
# URL to receive Meraki Location posts 
@app.route('/location/<validator>', methods=['GET', 'POST'])
def location(validator):
    # Save Meraki Location
    result = save_meraki_location(request,validator,credentials)

    return (result)

# Alert View
@app.route('/mvalert', methods=['GET', 'POST'])
def alert():
    # Save MV Camera Notification
    result = analyze_camera_alert(request.json)

    return (result)

# Index View
@app.route('/', methods=['GET', 'POST'])
def index():

    return ("Welcome to Meraki APP!")

################################################################
###    Start APP
################################################################
if __name__ == '__main__':
    # Start Flask
    app.run(host='0.0.0.0',use_reloader=False)