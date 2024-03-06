from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

# DB Table Schema for Users
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String)
    name = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

# DB Table Schema for Quizzes
## user_id is a foreign key from table Users
class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    name = db.Column(db.String)
    score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    user = db.relationship("User", backref="quizzes")

# DB Table Schema for Questions
## quiz_id is a foreign key from table Quizzes
class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'))
    type = db.Column(db.String(20))
    question = db.Column(db.Text)
    topics = db.Column(db.String)
    choices = db.Column(db.String)
    answers = db.Column(db.JSON)
    score = db.Column(db.Integer)

    quiz = db.relationship("Quiz", backref="questions")

# DB Table Schema for Chats
## user_id is a foreign key from table Users
class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    name = db.Column(db.String)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    user = db.relationship("User", backref="chats")

# DB Table Schema for Messages
## chat is a foreign key from table Chats
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'))
    message = db.Column(db.String)

    chat = db.relationship("Chat", backref="messages")