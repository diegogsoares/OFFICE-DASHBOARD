# **WELCOME to OFFICE-DASHBOARD**

## **What is OFFICE-DASHBOARD?**

OFFICE-DASHBOARD is a WEB Dashboard that allows visualization of Key Metrics (KPIs) of real state utilization (Enterprise Workspaces, Retail Stores and others) leveraging Cisco infrastructure as a Sensor.
The use of these metrics can help organizations to prioritize/justify investments in real state based on utilization metrics of its spaces, it also can help better understand employee behaviors when it comes to a relly important question, How is my Office being used?

IMAGE of the DASHBOARD
![Dashboard Sample](x.jpg)

Example of some metrics:

- What is the busiest time of the day?
- Where are employees concentrating inside the office?
- What is the utilization of my meeting rooms?
- How many employees come in/out every day?
- What are employees mood inside the office?
- What is the Gender/Age profile of the office users?

<br>

## **What are OFFICE-DASHBOARD Components?**

Written in python it leverages [Flask Framework](https://flask.palletsprojects.com/en/1.1.x/) to handle the induvidual data collection modules and the expose urls for data posting.
Each module has the capability of runninng as a standalone script for testing/troubleshooting scenarios.

IMAGE of the APP Architecture
![APP Architecture](x.jpg)

If you want more details on the _Office Dashboard_ check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** with detailed explanation.

### **Meraki Module**

Meraki module 

```console
(venv)$ python3 modules/meraki.py
```

>**Note:** Make sure you look at [Installing](#Installing) Section of this file to have the proper credentials.

If you want more details on the _Office Dashboard -  Meraki Module_ check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** with detailed explanation.

### **WEBEX Module**

`Paragraph 1`

```console
(venv)$ python3 modules/webex.py
```

>**Note:** Make sure you look at [Installing](#Installing) Section of this file to have the proper credentials.

If you want more details on the _Office Dashboard - WEBEX Module_ check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** with detailed explanation.

### **DNA Spaces Module**

`Paragraph 1`

```console
(venv)$ python3 modules/dnaspaces.py
```

>**Note:** Make sure you look at [Installing](#Installing) Section of this file to have the proper credentials.

If you want more details on the _Office Dashboard - DNA Spaces Module_ check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** with detailed explanation.

### **Data Retention Module**

`Paragraph 1`

>**Note:** Make sure you look at [Installing](#Installing) Section of this file to have the proper settings on credentials file.

If you want more details on the _Office Dashboard - Data Retention Module_ check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** with detailed explanation.

<br>

## **How to install OFFICE-DASHBOARD?**

### **Prerequisites**

- MAC, Linux (not supported on Windows)
- python 3.x
- pip package manager (https://pip.pypa.io/en/stable/installing/)

>**Note:** Check this **[post](https://netdevopsmadeeasy.com/office-dashboard/)** to setup a Linux VM as your development environmennt.

If already installed, make sure that pip / setuptools are upto date (commands may vary)

```bash
    pip install --upgrade pip

    Ubuntu: sudo pip install --upgrade setuptools
```

- virtualenv (recommended)

```bash
    Ubuntu: sudo apt-get install python-virtualenv
    Fedora: sudo dnf install python-virtualenv
    MAC: sudo pip install virtualenv
```

### **Installing**

Step 1: Clone code repository

```bash
git clone https://github.com/diegogsoares/OFFICE-DASHBOARD.git
cd OFFICE-DASHBOARD
```

Setp 2: Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Step 3: Install requirements

```bash
python3 -m pip install -r requirements.txt 
```

Step 4: Edit credentials.py file and add your credentials

```bash
vi credentials.py 
or
nano credentials.py
```

>**Note:** I personally like to use a more robust file editor called nano 

### **Testing / Running APP**

#### Testing Meraki Module

```console
(venv)$ python3 modules/meraki.py
```

approximated expected output:

```console
Expected output
```

#### Testing Webex Module

```console
(venv)$ python3 modules/webex.py
```

approximated expected output:

```console
Expected output
```

#### Testing DNA Spaces Module

```console
(venv)$ python3 modules/dnaspaces.py
```

approximated expected output:

```console
Expected output
```

#### Running OFFICE-DASHBOARD APP

```console
(venv)$ python3 new-app.py
```

approximated expected output:

```console
Expected output
```

<br>

>**Note:** You will need influxDB and Grafana installed and running on the same host was your code is runninng. Check the posts below:
- [Installing TIG Stack Instructions](https://netdevopsmadeeasy.com/setting-up-your-tig-stack/)

<br>

## **Built With**

- [Visual Studio Code](https://code.visualstudio.com/) - Python IDE

<br>

## **Contributing**

none

<br>

## **Authors**

- **Diego Soares** - _Initial work_
  - [GITHUB account](https://github.com/diegogsoares) &nbsp;
  - [BLOG netdevopsmadeeasy.com](https://netdevopsmadeeasy.com/about-me/)

See also the list of [contributors] who participated in this project.

<br>

## **License**

This project is licensed under the GPLv2 License - see the [LICENSE]() file for details

<br>

## **Acknowledgments**

- BIG THANK YOU to all my CISCO customers that challenged me with use cases.
