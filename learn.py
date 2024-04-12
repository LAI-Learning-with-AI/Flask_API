from flask import Blueprint, request, jsonify
from .main_agent.main import run_chat
from .models import db, Quiz, User, Question, Explanations
from .main_agent.get_similar import get_similar
from collections import defaultdict

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
    return jsonify({'topic': topic_id, 'explanation': response}), 201

@learn_bp.route('/time_analysis', methods=['POST'])
def time_analysis():
    # extract data from the request body
    data = request.json
    user_id = data.get('userId')

    # Query the user's account creation date
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    initial_date = user.created_at.strftime('%Y-%m-%d %H:%M:%S')

    # Query the quizzes and their associated questions for the specified user_id
    quizzes = Quiz.query.filter_by(user_id=user_id).join(Question).all()

    # Create a dictionary to store aggregated data for each topic
    topic_scores = defaultdict(lambda: {'dates': [initial_date], 'average_scores': [0]})

    # Iterate over quizzes and questions to aggregate data
    for quiz in quizzes:
        for question in quiz.questions:
            # Split topics string into a list
            topics = question.topics.split(',')
            for topic in topics:
                # Skip null values for score
                if question.score is not None:
                    # Append quiz date and score to the topic's data
                    topic_scores[topic]['dates'].append(quiz.created_at.strftime('%Y-%m-%d %H:%M:%S'))
                    topic_scores[topic]['average_scores'].append(float(question.score))

    # Calculate average score for each topic over time
    for topic, data in topic_scores.items():
        # Sort dates in ascending order
        sorted_dates = sorted(set(data['dates']))
        # Calculate average score for each sorted date
        average_scores = []
        for date in sorted_dates:
            scores_for_date = [score for i, score in enumerate(data['average_scores']) if data['dates'][i] == date]
            # Skip null values when calculating average score
            scores_for_date = [score for score in scores_for_date if score is not None]
            if scores_for_date:  # Check if the list is not empty
                average_score_for_date = sum(scores_for_date) / len(scores_for_date)
                average_scores.append(round(average_score_for_date, 2))
            else:
                average_scores.append(None)  # Set score to 0 for dates with no scores
        # Update topic_scores with the sorted dates and calculated average scores
        topic_scores[topic]['dates'] = sorted_dates
        topic_scores[topic]['average_scores'] = average_scores

    return jsonify(topic_scores)