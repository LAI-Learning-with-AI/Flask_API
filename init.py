from .chats import chats_bp
from .learn import learn_bp
from .quizzes import quizzes_bp
from .users import users_bp

def init_routes(app):
    app.register_blueprint(chats_bp)
    app.register_blueprint(learn_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(users_bp)