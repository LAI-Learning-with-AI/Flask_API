from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .config import Config
from .models import db, Quiz, Question, Chat, Message, User
from .main_agent.main import run_chat
from .main_agent.generate_quizzes import generate_quiz
from .main_agent.generate_quizzes import grade_quiz
from .main_agent.get_similar import get_similar
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

# Route to create a new user
@app.route('/createUser', methods=['POST'])
def create_user():
    # Extract data from the rqeuest body
    data = request.get_json()
    userId = data.get('userId')
    email = data.get('email')
    name = data.get('name')
    
    # Create user ORM object
    new_user = User(
        id=userId,
        email=email,
        name=name
    )

    # Commit to DB
    db.session.add(new_user)
    db.session.commit()
    
    # Return response
    return jsonify({'message': 'User created successfully'}), 201

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
         "created_at": details['created_at'],
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
    return jsonify({'chat_id': chat.id}), 201

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

# Route to import quiz / duplicate quiz
@app.route('/importQuiz', methods=['POST'])
def import_quiz():
    # Extract data from the request body
    data = request.json
    userId = data.get('userId')
    quizId = data.get('quizId')

    # Get quiz to be duplicated
    quiz = Quiz.query.get(quizId)
    questions = Question.query.filter(Question.quiz_id == quizId).all()

    # Check to see if quiz is in DB
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    # Define ORM object for new Quiz
    newQuiz = Quiz(user_id=userId, name=quiz.name, topics=quiz.topics)

    # Add Quiz to DB
    db.session.add(newQuiz)
    db.session.commit()

    # Add questions to DB
    for question in questions: 
        # Create ORM object for Question
        newQuestion = Question(quiz_id=newQuiz.id, type=question.type, question=question.question,
                               topics=question.topics, choices=question.choices,
                               answers=question.answers)
        
        # Add to DB
        db.session.add(newQuestion)

    # Commit to DB
    db.session.commit()

    # Return the response
    return jsonify({'quiz_id': newQuiz.id}), 201

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
    body = generate_quiz(numQs, types, topics)

    # return 400 for failed quiz generation
    if body == False:
        return jsonify({'error': 'Failed to generate quiz'}), 400

    # Prepare the response body
    # responseBody = {
    #     "questions": questions,
    #     "date": date
    # }

    # Commit new quiz to database
    quiz_id = _store_quiz_in_db(userId, name, topics, body)

    # Return the response
    return jsonify({'quiz_id': quiz_id}), 201

@app.route('/gradequiz', methods=['GET'])
def gradequiz():
    '''Takes info on quiz MC questions correct & FRQs, grades FRQs, computes a final quiz grade, and stores relevant grade info
    in the database. Expects input JSON body of the following format:
    {
        "userID": 1234,
        "quizID": 5678,
        "questions": [
            {
                "questionID": 4000,
                "question": "This is a question asked?",
                "question_type": "SHORT_ANSWER",
                "answer": "This is the ground-truth answer.",
                "user_answer": "This is the user's answer.",
            },
            {
                "questionID": 4001,
                "question": "This is another question asked?",
                "question_type": "MULTIPLE_CHOICE",
                "answer": "This is the ground-truth answer.",
                "user_answer": "This is the ground-truth answer."}
            }
        ]   
    }
    '''

    # extract data from the request body
    data = request.json
    user_id = data.get('userID')
    quiz_id = data.get('quizID')
    num_mc = data.get('numMC')
    num_mc_correct = data.get('numMCCorrect')
    questions = data.get('questions')

    # grade quiz
    final_score, question_scores = grade_quiz(questions)

    # store scores in db
    # TODO:

    # return response
    return jsonify({'quiz_id': quiz_id}), 200

def store_scores_in_db(user_id, quiz_id, final_grade, frq_scores):
    # TODO:
    return

# Function to commit quizzes to database
def _store_quiz_in_db(user_id, name, topics, questions):
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

@app.route('/getsimilar', methods=['POST'])
def getsimilar():
    """
    A function that handles the '/getsimilar' route with the 'POST' method.

    Parameters:
    - None
    - The request contains a list of 'topics' in json, which is a list of strings.

    Returns:
    - A JSON response containing the similar topics and their corresponding resources.
    - A status code of 200 if the request was successful.
    - Ex: {"resources": {"topic1": ["resource1", "resource2"]}, {"topic2": ["resource3"]}, ...}
    """
    # Extract data from the request body
    data = request.json
    topics = data.get('topics')
    max_resources_per_topic = data.get('max_resources_per_topic')

    # Call my_func with the extracted data
    similar_topics = get_similar(topics, max_resources_per_topic)

    # Return the response
    return jsonify({'resources': similar_topics}), 200
