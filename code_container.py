from flask import Flask, request, jsonify
import docker
import subprocess
import os
import time
import tempfile
from flask_cors import CORS

app = Flask(__name__)
client = docker.from_env()
CORS(app)

def _create_docker_image(image_name, requirements_txt=None):
    """Takes a name and an optional path to a requirements.txt file. Creates and returns a docker image."""

    cmd = ["docker", "build", "-t", image_name]

    # handle requirements.txt
    if requirements_txt:
        cmd.extend(["-f", "-", "."])
        with open(requirements_txt, "r") as file:
            requirements = file.read()
            cmd.append(f"COPY requirements.txt ./")
            cmd.append(f"RUN pip install -r requirements.txt <<< {requirements}")
    else:
        cmd.append(".")
    subprocess.run(cmd, check=True)

@app.route('/runcode', methods=['POST'])
def run_code():
    '''Takes JSON input of form: {"code": "code here"}. Runs the code in a Docker container and
    returns output of the form:'''

    code = request.json['code']

    try:

        # set up container
        client = docker.from_env()
        container_config = {
            'image': 'python:3.9',
            'command': ['python', '-c', code],
            'stdin_open': True,
            'tty': True,
        }

        # run container
        start_time = time.time()
        container = client.containers.run(**container_config)
        output = container.decode('utf-8')
        end_time = time.time()

        # parse output for errors and warnings only
        errors = ''
        for line in output.split('\n'):
            if line.startswith("ERROR:"):
                errors += line + '\n'
            elif line.startswith("WARNING:"):
                errors += line + '\n'

        # delete container
        latest_container = client.containers.list(all=True, limit=1)[0]
        latest_container.remove(force=True)

        runtime = end_time - start_time
        if runtime > 5:
            return jsonify({'ran': False, 'errors': 'Code took too long to execute\n' + errors, 'status_code': 500})
        else:
            return jsonify({'ran': True, 'errors': errors, 'status_code': 200})
    
    except Exception as e:
        return jsonify({'ran': False, 'errors': errors, 'status_code': 500})

if __name__ == '__main__':
    app.run(debug=True, port=5002)