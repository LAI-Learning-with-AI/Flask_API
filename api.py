from flask import Flask, request, jsonify
from .submodules.main_agent.main import run_chat
from dotenv import load_dotenv
from .config import Config
from .models import db
from .submodules.main_agent.generate_quizzes import generate_quiz 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load DB config from config.py
app.config.from_object(Config)

# Initialize DB
db.init_app(app)

# Create tables from models.py if they dont exist in database
with app.app_context():
    db.create_all()

@app.route('/chat', methods=['POST'])
def chat():
    # Extract data from the request body
    data = request.json
    userId = data.get('userId')
    chatId = data.get('chatId')
    message = data.get('message')
    context = data.get('context')

    # Extract previous messages and user data from the context
    previous_messages = context.get('previous', [])
    userData = context.get('userData', {})

    # Call my_func with the extracted data
    responseText, date = run_chat(userId, chatId, message, previous_messages, userData)


    # Prepare the response body
    responseBody = {
        "response": responseText,
        "date": date
    }

    # Return the response
    return jsonify(responseBody)


@app.route('/generatequiz', methods=['POST'])
def generatequiz():
    # Extract data from the request body
    data = request.json
    userId = data.get('userId')
    numQs = data.get('numberOfQuestions')
    types = data.get('types')
    topics = data.get('topics')

    # Call my_func with the extracted data
    # questions, date = generatequiz_temp(userId, numQs, types, topics)
    body = generate_quiz(numQs, types, topics)

    # Prepare the response body
    # responseBody = {
    #     "questions": questions,
    #     "date": date
    # }

    # Return the response
    return jsonify(body)


def generatequiz_temp(userId, numQs, types, topics):
    return [{
          "type": "TRUE_FALSE",
          "question": "This is a question?",
          "answers": ["True", "False"]
        },
        {
          "type": "MULTIPLE_CHOICE",
          "question": "What is an even number?",
          "answers": ["1", "3", "7", "8"]
        },
        {
          "type": "SHORT_ANSWER",
          "question": "What is a question?",
          "answers": None
        },
        {
          "type": "CODING",
          "question": "Write a function to print Hello World! to console.",
          "answers": None
        }
      ], "2024-02-28T00:00:00Z"
