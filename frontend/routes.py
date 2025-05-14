from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from frontend.models import User, db
from openai import OpenAI
from dotenv import load_dotenv
import os
from sqlalchemy import func


bp = Blueprint('main', __name__)

load_dotenv()  # Load environment variables explicitly

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@bp.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter(func.lower(User.email) == email.lower()).first()


        print("DEBUG:", user, "PW Match:", user.check_password(password) if user else None)

        if user and user.check_password(password):  # ✅ secure check
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.signup'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('main.signup'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))

    return render_template('signup.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

@bp.route('/ask', methods=['POST'])
def ask():
    text = request.json.get('question', '')

    editing_prompt = (
        "Fix only spelling, grammar, and punctuation errors in the following text. "
        "Preserve the original structure and intent of the text exactly as written. "
        "Do not rephrase or restructure the text:\n" + text
    )

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a proofreader. Only correct spelling, grammar, and punctuation errors. Keep the original text structure exactly as is. Do not rephrase, restructure, or modify the intent of the text."},
            {"role": "user", "content": editing_prompt},
        ],
        temperature=0.1
    )

    edited_text = completion.choices[0].message.content

    return jsonify({'answer': edited_text})

# Python cache files
__pycache__/
*.py[cod]
*.pyo

# Virtual environment
venv/
env/

# Environment variables
.env

# Flask instance folder
instance/

# Database files
*.sqlite3
*.db

# Logs
*.log

# Compiled files
*.so

# Jupyter Notebook checkpoints
.ipynb_checkpoints/

# IDE-specific files
.vscode/
.idea/

# OS-specific files
.DS_Store
Thumbs.db
