from flask import Flask
from dotenv import load_dotenv
from .config import Config
from .models import db
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load DB config from config.py
app.config.from_object(Config)

# Initialize DB
db.init_app(app)

# Create tables from models.py if they dont exist in database
with app.app_context():
    db.create_all()

# Import function to initialize app routes
from .init import init_routes

# Initialize app routes
init_routes(app)

if __name__ == '__main__':
    # run app.py not api.py
    app.run(debug=True)