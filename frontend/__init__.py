from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    load_dotenv()

    # Debugging print statements to verify environment variables
    print("DB_USERNAME:", os.getenv('DB_USERNAME'))
    print("DB_PASSWORD:", os.getenv('DB_PASSWORD'))
    print("DB_HOST:", os.getenv('DB_HOST'))
    print("DB_PORT:", os.getenv('DB_PORT'))
    print("DB_NAME:", os.getenv('DB_NAME'))

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    db.init_app(app)
    login_manager.init_app(app)

    from frontend.routes import bp
    app.register_blueprint(bp)

    @login_manager.user_loader
    def load_user(user_id):
        from frontend.models import User
        return User.query.get(int(user_id))

    login_manager.login_view = 'main.login'

    return app
