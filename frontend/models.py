# models.py
from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)  # Rename to "password" if preferred

    # Disable hashing
    def set_password(self, password):
        self.password_hash = password  # Store plaintext password

    def check_password(self, password):
        return self.password_hash == password  # Compare plaintext passwords