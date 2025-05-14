from datetime import datetime
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

    # Relationships
    transactions = db.relationship('TokenTransaction', backref='user', lazy=True)
    corrections = db.relationship('CorrectionHistory', backref='user', lazy=True)
    blacklist_entries = db.relationship('Blacklist', backref='submitter', lazy=True)

    def set_password(self, password):
        self.password_hash = password  # Switch back to generate_password_hash(password) for production

    def check_password(self, password):
        return self.password_hash == password  # Switch to check_password_hash(self.password_hash, password)

class TokenTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # purchase/penalty/usage
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=True, nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CorrectionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    corrected_text = db.Column(db.Text, nullable=False)
    correction_type = db.Column(db.String(20), nullable=False)  # self/llm
    tokens_used = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(25), default='pending')  # Extended length for statuses
    rejection_reason = db.Column(db.Text)
    final_text = db.Column(db.Text)

    __table_args__ = (
        db.Index('idx_status', 'status'),  # Added for better query performance
    )