# To run:

- Install required libraries --> pip install -r requirements.txt
- Initiate main_agent repo as a submodule --> git submodule update --init
- If submodule has wrong GitHub origin --> git remote set-url origin https://github.com/LAI-Learning-with-AI/main_agent
- cd into main_agent submodule and ensure it is updated --> git reset --hard, git fetch origin, git checkout origin
- Run the main server --> flask run
- Start Docker Desktop and then run the server for executing user quiz code --> python code_container.py
