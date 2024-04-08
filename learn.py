from flask import Blueprint, request, jsonify
from .main_agent.main import run_chat
from .models import db, Quiz, User, Question, Explanations
from .main_agent.get_similar import get_similar

# Blueprint to import into App.py
learn_bp = Blueprint('learn', __name__)

@learn_bp.route('/getsimilar', methods=['POST'])
def getsimilar():
    """
    A function that handles the '/getsimilar' route with the 'POST' method.

    Parameters:
    - None
    - The request contains a list of 'topics' in json, which is a list of strings.
    - The request contains a 'max_resources_per_topic' in json, which is an integer.
    - Ex: {"topics": ""}
    - Ex: {"max_resources_per_topic": 5}

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


@learn_bp.route('/groupQuizResults', methods=['POST'])
def groupQuizResults():
    group_frequency_cutoff = 10
    mastery_score_cutoff = 0.8

    # Extract data from the request body
    data = request.json
    userId = data.get('userId')
    all_user_quiz_ids = [q.id for q in Quiz.query.filter(User.id == userId).all()]

    all_questions = []
    for quizId in all_user_quiz_ids:
        all_questions += Question.query.filter(Question.quiz_id == quizId).all()

    # Assuming every question has only one topic
    scores = {}
    for q in all_questions:
        if q.score is None:
            continue
        if q.topics not in scores:
            scores[q.topics] = []
        scores[q.topics].append(q.score)

    results = {}
    for k, v in scores.items():
        results[k] = (len(v), sum(v)/len(v))

    response = []
    for k, v in results.items():
        mastery = ""
        if v[0] < group_frequency_cutoff:
            mastery = "learning"
        elif v[1] < mastery_score_cutoff:
            mastery = "struggling"
        elif v[1] >= mastery_score_cutoff:
            mastery = "mastered"
        else:
            mastery = "undermined"

        response += [{
            "topic": k,
            "frequency": v[0],
            "score": v[1],
            "mastery": mastery
        }]

    # Return the response
    return response, 200

# Route to get explanation for a topic from database.
@learn_bp.route('/getExplanation', methods=['POST'])
def get_explanation():
    # Extract the topic from the request body
    data = request.json
    topic = data.get('topic')

    # Double check to make sure topic is inside the request body
    if not topic:
        return jsonify({'error': 'Bad Request'}), 400

    # Grab explanation from database
    query = Explanations.query.filter_by(topic=topic).first()

    # Return response
    if query:
        # If in DB, send topic and explanation.
        return jsonify({'topic': query.topic, 'explanation': query.explanation}), 200
    else:
        # If not, send error.
        return jsonify({'error': 'Not found'}), 404
    
# Route to create an explanation
@learn_bp.route('/postExplanation', methods=['POST'])
def post_explanation():
    # Extract data from the request body
    data = request.json
    topic_id = data.get('topic_id')
    topic = data.get('topic')

    # Double check to make sure topic and explanation are inside the request body
    if not topic_id or not topic:
        return jsonify({'error': 'Both topic and explanation are required'}), 400

    # Check if the topic already exists
    duplicate = Explanations.query.filter_by(topic=topic_id).first()
    if duplicate:
        return jsonify({'error': 'Duplicate Explanation'}), 400
    
    # Generate explanation using LLM
    response, date = run_chat('123', '456', f'Give me a detailed explanation of {topic}.', [], {})

    # Prepare ORM object for DB insertion
    explanation = Explanations(topic=topic_id, explanation=response)

    # Commit explanation to DB
    db.session.add(explanation)
    db.session.commit()

    # Return response.
    return jsonify({'message': 'Explanation Created'}), 201