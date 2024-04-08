from flask import Flask, request, jsonify
import docker
import subprocess
from flask_cors import CORS

app = Flask(__name__)
client = docker.from_env()
CORS(app)

@app.route('/runcode', methods=['POST'])
def run_code():
    code = request.json['code']
    
    try:
        # create a Docker container
        container = client.containers.run('python:3.9', detach=True, stdin_open=True, tty=True)

        # write the code to a temporary file
        with open('temp.py', 'w') as file:
            file.write(code)

        # copy the file to the container
        container.put_archive('/', ('temp.py',))

        # execute the code inside the container
        output = container.exec_run('python temp.py', stdin=False, stdout=True, stderr=True)

        # remove the temporary file and the container
        subprocess.run(['rm', 'temp.py'])
        container.remove(force=True)

        return jsonify({'ran': True, 'status_code': 200})
    
    except Exception as e:
        return jsonify({'ran': False, 'status_code': 500})

if __name__ == '__main__':
    app.run(debug=True, port=5002)