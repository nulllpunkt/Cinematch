from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Prefixed with blueprint name
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app():
    # Serve static files from the parent directory's static folder
    static_folder = os.path.join(os.path.dirname(__file__), '..', 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')

    # --- App Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://127.0.0.1:5432/postgres')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # -----------------------

    # --- Initialize App with Extensions ---
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # ------------------------------------

    # --- Register Blueprints ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    # ---------------------------

    with app.app_context():
        db.create_all()  # Create database tables
        print("Database tables checked/created.")

    return app
