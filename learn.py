from flask import Blueprint, request, jsonify
from .models import Quiz, User, Question
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
