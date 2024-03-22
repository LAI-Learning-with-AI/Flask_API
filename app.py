from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .config import Config
from .models import db, Quiz, Question, Chat, Message
from .main_agent.main import run_chat
from .main_agent.generate_quizzes import generate_quiz 
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

# Code to serialize ORM objects
## credit: https://stackoverflow.com/a/54069595
def row2dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}

@app.route('/generateResponse', methods=['POST'])
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
@app.route('/chats', methods=['POST'])
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
         "chats": msgs
      })

    # Return the response
    return jsonify(formatted), 200

# Route to create a new chat for a user
@app.route('/createChat', methods=['POST'])
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
    return jsonify({'chat_id': chat.id}), 200

# Route to get quizzes associated to a user
@app.route('/quizzes', methods=['POST'])
def get_quizzes():
    # Extract data from the request body
    data = request.json
    user_id = data.get('userId')

    # Get all the quizzes associated with user
    quizzes = Quiz.query.filter(Quiz.user_id == user_id).all()

    # Prepare the response body
    formatted = []
    for quiz in quizzes:
      formatted.append(row2dict(quiz))

    return jsonify(formatted), 200

# Route to get quiz questions with input: USER_ID and QUIZ_ID
@app.route('/quiz', methods=['POST'])
def quiz():
    # Extract data from the request body
    data = request.json
    user_id = data.get('userId')
    quiz_id = data.get('quizId')

    quiz = Quiz.query.get(quiz_id)
    # Check to see if quiz is in DB
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    # Check to see if quiz belongs to user
    elif quiz.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403  
    
    # Get all the questions for the quiz
    questions = Question.query.filter(Question.quiz_id == quiz_id).all()

    # Prepare the response body
    formatted = []
    for question in questions:
      formatted.append(row2dict(question))
    
    responseBody = {
        "questions" : formatted,
        "date": quiz.created_at.isoformat()
    }

    # Return the response
    return responseBody, 200

@app.route('/generatequiz', methods=['POST'])
def generatequiz():
    # Extract data from the request body
    data = request.json
    userId = data.get('userId')
    name = data.get('name')
    numQs = data.get('numberOfQuestions')
    types = data.get('types')
    topics = data.get('topics')

    # Call my_func with the extracted data
    # questions, date = generatequiz_temp(userId, numQs, types, topics)
    body = generate_quiz(numQs, types, topics, False)

    # Prepare the response body
    # responseBody = {
    #     "questions": questions,
    #     "date": date
    # }

    # Commit new quiz to database
    quiz_id = store_quiz_in_db(userId, name, topics, body)

    # Return the response
    return jsonify({'quiz_id': quiz_id}), 200

# Function to commit quizzes to database
def store_quiz_in_db(user_id, name, topics, questions):
    # Create quiz ORM object 
    quiz = Quiz(user_id=user_id, name=name, topics=topics)

    # Commit to DB
    db.session.add(quiz)
    db.session.commit()

    # Parse through the JSON object from generate_quiz(numQs, types, topics).
    for question_data in questions['questions']:
      # Create question ORM object
      question = Question(quiz_id=quiz.id, type=question_data['type'], question=question_data['question'],
                          topics=question_data['topics'], choices=question_data['choices'],
                          answers=question_data['answer'])
      
      # Commit to DB
      db.session.add(question)
      db.session.commit()

    # Return final quiz for frontend redirect
    return quiz.id

