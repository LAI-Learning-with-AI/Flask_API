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