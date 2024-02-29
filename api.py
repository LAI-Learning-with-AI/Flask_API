from flask import Flask, request, jsonify
from .submodules.main_agent.main import run_chat
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)


@app.route('/chat', methods=['POST'])
def chat():
    # Extract data from the request body
    data = request.json
    user_id = data.get('userId')
    chat_id = data.get('chatId')
    message = data.get('message')
    context = data.get('context')

    # Extract previous messages and user data from the context
    previous_messages = context.get('previous', [])
    user_data = context.get('userData', {})

    # Call my_func with the extracted data
    response_text, date = run_chat(user_id, chat_id, message, previous_messages, user_data)

    # Prepare the response body
    response_body = {
        "response": response_text,
        "date": date
    }

    # Return the response
    return jsonify(response_body)


def test_func(a, b, c, d, e):
    return 'Hello, World!', "2022-01-01 00:00:00"
