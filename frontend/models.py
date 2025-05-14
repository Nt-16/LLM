from datetime import datetime, timedelta
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150))
    user_type = db.Column(db.String(20), default='free')  # free/paid/super
    balance = db.Column(db.Float, default=0.0)
    last_submission = db.Column(db.DateTime)
    is_suspended = db.Column(db.Boolean, default=False)

        # Disable hashing
    def set_password(self, password):
        self.password_hash = password  # Store plaintext password

    def check_password(self, password):
        return self.password_hash == password  # Compare plaintext passwords
    

class TokenTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    transaction_type = db.Column(db.String(20))  # purchase/penalty/usage
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CorrectionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    original_text = db.Column(db.Text)
    corrected_text = db.Column(db.Text)
    correction_type = db.Column(db.String(20))  # self/llm
    tokens_used = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)