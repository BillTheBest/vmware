#!/usr/bin/python
from __future__ import division
from pysphere import *
from flask import Flask, render_template
import re, os

app = Flask(__name__)
app.debug = True
target_host = os.getenv('VMWARE_HOST')
target_user = os.getenv('VMWARE_USER')
target_pass = os.getenv('VMWARE_PASS')

# pySphere >
server = VIServer()
server.connect(target_host, target_user, target_pass)
# < pySphere

# Locally cached queries >
server_type = server.get_server_type()
server_version = server.get_api_version()
datacenter = server.get_datacenters().values()
clusters = server.get_clusters().values()
hosts = server.get_hosts().values()
# < Locally cached queries

datastore = [] 

for ds, name in server.get_datastores().items():
   props = VIProperty(server, ds)
   try:
     capacity = props.summary.capacity
     free = props.summary.freeSpace
     uncommitted = props.summary.uncommitted
     used = capacity - free
     overprov = used + uncommitted
     overprovPercent = (overprov / capacity) * 100
     datastore.append((name, "{0:.0f}".format(capacity / 1024 / 1024 / 1024), "{0:.0f}".format(free / 1024 / 1024 / 1024), "{0:.0f}".format(used / 1024 / 1024 / 1024), "{0:.0f}".format(overprov / 1024 / 1024 / 1024), "{0:.0f}".format(overprovPercent), "{0:.0f}".format(uncommitted / 1024 / 1024 / 1024)))
   except AttributeError:
     pass


@app.route("/")
def index():
     temp = ''
     resp = []    
 
     if server.is_connected():
        if not server.keep_session_alive():
           server.connect(target_host, target_user, target_pass)
     else: server.connect(target_host, target_user, target_pass)


     vms = {'all': []}
     for status in ('poweredOn', 'poweredOff'):
         vmlist = [re.findall('\[(.*?)\].*?/(.*)\.', vm)[0][::-1] + (status,)
                      for vm in server.get_registered_vms(status=status)]
         vms[status] = sorted(vmlist)
         vms['all'].extend(vmlist)

     vms['all'].sort()

     for host in hosts:
         temp = os.system('ping -c 1 ' + host + ' > /dev/null')
         if temp == 0: resp.append((host, 'isUp'))
         else: resp.append((host, 'isDown'))

     return render_template("index.html", vms=vms, server_type=server_type,
                            server_version=server_version, datacenter=datacenter,
                            clusters=clusters, hosts=resp, datastore=datastore)

if __name__ == "__main__":
    app.run('0.0.0.0', 5000)
