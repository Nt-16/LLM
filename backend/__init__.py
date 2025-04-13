from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # AWS RDS MySQL Configuration
    # app.config['SQLALCHEMY_DATABASE_URI'] = (
    #     'mysql+pymysql://admin:Password322@project322.cr2mqca8ek5f.us-east-2.rds.amazonaws.com:3306/project322'
    # )
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.secret_key = 'your_secret_key'  # Required for session management and flash messages

    # # Initialize the database
    # db.init_app(app)

    # Import and register routes
    # Load environment variables from .env file
    load_dotenv()

    # Get database credentials from environment variables
    db_username = os.getenv('DB_USERNAME', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'project322.cr2mqca8ek5f.us-east-2.rds.amazonaws.com')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'project322')

    try:
        db_port = int(db_port)
    except ValueError:
        raise ValueError("Invalid DB_PORT value. Ensure it is a valid integer.")

    # Set SQLAlchemy database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)

    from frontend import routes
    app.register_blueprint(routes.bp)

    return app