from flask import Blueprint, request, jsonify
from .models import db, User

# Blueprint to import into App.py
users_bp = Blueprint('users', __name__)

# Route to create a new user
@users_bp.route('/createUser', methods=['POST'])
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

# Route to check if user exists
@users_bp.route('/checkUser', methods=['POST'])
def check_user():
    # Extract data from the request body
    data = request.get_json()
    userId = data.get('userId')

    # check if user exists
    exists = False
    user = User.query.filter_by(id=userId).first()
    if user is not None:
        exists = True
    
    return {'exists': exists}, 200