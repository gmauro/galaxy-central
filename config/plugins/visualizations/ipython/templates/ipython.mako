<%
import os
import sys
import tempfile
import shutil
import time
import subprocess
import yaml
import random


history_id = trans.security.encode_id( trans.history.id )
dataset_id = trans.security.encode_id( hda.id )
# Ensure generation of notebook id is deterministic for the dataset. Replace with history id
# whenever we figure out how to access that.
random.seed( history_id )
notebook_id = ''.join(random.choice('0123456789abcdef') for _ in range(64))
empty_nb = """{
 "metadata": {
  "name": "",
  "signature": "sha256:%s"
 },
 "nbformat": 3,
 "nbformat_minor": 0,
 "worksheets": [
  {
   "cells": [
    {
     "cell_type": "heading",
     "level": 2,
     "metadata": {},
     "source": [
      "Welcome to the interactive Galaxy IPython Notebook."
     ]
    },
    {
     "cell_type": "markdown",
     "metadata": {},
     "source": [
      "You can access your data via the dataset number. For example: handle = open('42', 'r')"
     ]
    },
    {
     "cell_type": "code",
     "collapsed": false,
     "input": [],
     "language": "python",
     "metadata": {},
     "outputs": []
    }
   ],
   "metadata": {}
  }
 ]
}""" % (notebook_id, )


# Find all ports that are alreaxy occupied
netstat_cmd = "netstat -tnaAinet | awk 'NR >= 3 { print $4 }' | cut -d: -f2 | sort -un"
netstat_out = subprocess.check_output( shlex.split( netstat_cmd ))
occupied_ports = [port for port in netstat_out.split('\n') if port.isdigit()]

# Generate random free port number for our docker container
while True:
    PORT = random.randrange(10000,15000)
    if PORTS not in occupied_ports:
        break

HOST = request.host
# Strip out port, we just want the URL this galaxy server was accessed at.
if ':' in HOST:
    HOST = HOST[0:HOST.index(':')]

temp_dir = os.path.abspath( tempfile.mkdtemp() )

conf_file = {
    'history_id': history_id,
    'galaxy_url': request.application_url,
    'api_key': trans.user.api_keys[0].key,
}
with open( os.path.join( temp_dir, 'conf.yaml' ), 'wb' ) as handle:
    handle.write( yaml.dump(conf_file) )

empty_nb_path = os.path.join(temp_dir, 'ipython_galaxy_notebook.ipynb')
with open( empty_nb_path, 'w+' ) as handle:
    handle.write( empty_nb )

docker_cmd = 'docker run -d --sig-proxy=true -p %s:6789 -v "%s:/import/" bgruening/docker-ipython-notebook' % (PORT, temp_dir)

subprocess.call(docker_cmd, shell=True)

# We need to wait until the Image and IPython in loaded
# TODO: This can be enhanced later, with some JS spinning if needed.
time.sleep(1)

%>
<html>


<body>
    <object data="http://${HOST}:${PORT}/notebooks/ipython_galaxy_notebook.ipynb" height="100%" width="100%">
        <embed src="http://${HOST}:${PORT}/notebooks/ipython_galaxy_notebook.ipynb" height="100%" width="100%">
        </embed>
    </object>
</body>
</html>
