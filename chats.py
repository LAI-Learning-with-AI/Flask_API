from flask import Blueprint, request, jsonify
from .models import db, Chat, Message
from .main_agent.main import run_chat

# Blueprint to import into App.py
chats_bp = Blueprint('chats', __name__)

# Code to serialize ORM objects
## credit: https://stackoverflow.com/a/54069595
def row2dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}

@chats_bp.route('/generateResponse', methods=['POST'])
def generateResponse():
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

    # Create Chat ORM objects
    question_message = Message(chat_id=chatId, message=message)
    response_message = Message(chat_id=chatId, message=responseText)

    # Commit to DB
    db.session.add(question_message)
    db.session.add(response_message)
    db.session.commit()

    # Prepare the response body
    responseBody = {
        "response": responseText,
        "date": date
    }

    # Return the response
    return jsonify(responseBody)

# Route to get all chats associated to a user
@chats_bp.route('/chats', methods=['POST'])
def get_chats():
    # Extract data from the request body
    data = request.json
    user_id = data.get('userId')

    # Get all the quizzes associated with user
    chats = Chat.query.filter(Chat.user_id == user_id).all()

    # Prepare the response body
    formatted = []
    for chat in chats:
      # Convert chat rows to a dictionary
      details = row2dict(chat)

      # Get messages associated to a chat
      messages = Message.query.filter(Message.chat_id == chat.id).all()
      
      # Compile messages into an array
      msgs = []
      for message in messages:
         msgs.append(message.message)

      # Format response
      formatted.append({
         "chat_id": details['id'],
         "title": details['name'],
         "description": details['description'],
         "created_at": details['created_at'],
         "chats": msgs
      })

    # Return the response
    return jsonify(formatted), 200

# Route to create a new chat for a user
@chats_bp.route('/createChat', methods=['POST'])
def createChat():
    # Extract data from the request body
    data = request.json
    user_id = data.get('userId')
    name = data.get('name')
    # description = data.get('description')

    # Create Chat ORM object 
    chat = Chat(user_id=user_id, name=name)

    # Commit to DB
    db.session.add(chat)
    db.session.commit()

    # Return the response
    return jsonify({'chat_id': chat.id}), 201