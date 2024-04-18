from flask import Blueprint, request, jsonify
from .main_agent.generate_quizzes import generate_quiz, grade_quiz
from .models import db, Quiz, Question

# Code to serialize ORM objects
## credit: https://stackoverflow.com/a/54069595
def row2dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}

# Blueprint to import into App.py
quizzes_bp = Blueprint('quizzes', __name__)

# Route to get quizzes associated to a user
@quizzes_bp.route('/quizzes', methods=['POST'])
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
@quizzes_bp.route('/quiz', methods=['POST'])
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
        "date": quiz.created_at.isoformat(),
        "name": quiz.name,
        "score": quiz.score,
        "id": quiz.id
    }

    # Return the response
    return responseBody, 200

# Route to import quiz / duplicate quiz
@quizzes_bp.route('/importQuiz', methods=['POST'])
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

@quizzes_bp.route('/generatequiz', methods=['POST'])
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

@quizzes_bp.route('/gradequiz', methods=['POST'])
def gradequiz():
    '''Takes info on quiz MC questions correct & FRQs, grades FRQs, computes a final quiz grade, and stores relevant grade info
    in the database. Expects input JSON body of the following format:
    {
        "userId": 1234,
        "quizId": 5678,
        "questions": [
            {
                "id": 4000,
                "question": "This is a question asked?",
                "type": "SHORT_ANSWER",
                "answers": "This is the ground-truth answer.",
                "user_answer": "This is the user's answer.",
            },
            {
                "id": 4001,
                "question": "This is another question asked?",
                "type": "MULTIPLE_CHOICE",
                "answers": "This is the ground-truth answer.",
                "user_answer": "This is the ground-truth answer."}
            }
        ]   
    }
    '''

    # extract data from the request body
    data = request.json
    user_id = data.get('userId')
    quiz_id = data.get('quizId')
    questions = data.get('questions')

    question_ids = []
    question_answers = []
    for question in questions:
        question_ids.append(question['id'])
        question_answers.append(question['user_answer'])

    # store answers in db
    _store_answers_in_db(question_ids, question_answers)

    # grade quiz
    final_score, question_scores, code_errors = grade_quiz(questions)

    # store scores in db
    _store_scores_in_db(user_id, quiz_id, final_score, question_ids, question_scores, code_errors)

    # return response
    return jsonify({'quizId': quiz_id}), 200

def _store_answers_in_db(question_ids, question_answers):
    # set question answers
    for question_id, answer in zip(question_ids, question_answers):
        question = Question.query.get(question_id)
        question.user_answer = answer

    # commit to db
    db.session.commit()

def _store_scores_in_db(user_id, quiz_id, final_grade, question_ids, question_scores, code_errors):
    '''Stores quiz scores in the database.'''

    # set final grade
    quiz = Quiz.query.get(quiz_id)
    quiz.score = final_grade

    # set question scores and (if applicable)
    for question_id, score, errors in zip(question_ids, question_scores, code_errors):
        question = Question.query.get(question_id)
        question.score = score
        question.warnings = errors

    # commit to db
    db.session.commit()

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
