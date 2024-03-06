# To run:

- Install required libraries --> pip install -r requirements.txt
- Initiate main_agent repo as a submodule --> git submodule add --force https://github.com/LAI-Learning-with-AI/main_agent main_agent
- If submodule has wrong GitHub origin --> git remote set-url origin https://github.com/LAI-Learning-with-AI/main_agent
- Ensure the main_agent submodule is updated --> git fetch origin, git checkout origin
- Run the server --> flask run