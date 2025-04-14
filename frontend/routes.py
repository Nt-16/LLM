from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from frontend.models import User, db
from openai import OpenAI
from dotenv import load_dotenv
import os

bp = Blueprint('main', __name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@bp.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('index.html', username=user.username)
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id  # Store user ID in session
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'error')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('main.login'))
    return render_template('signup.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

# Route to handle user input and provide a response
@bp.route('/ask', methods=['POST'])
def ask():
    # Get the user input from the JSON body of the POST request
    text = request.json.get('question', '')

    # Define the editing prompt with strict instructions
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
        temperature=0.1  # Very low temperature for consistent, minimal editing
    )
    
    edited_text = completion.choices[0].message.content
    response = {
        'answer': edited_text
    }
    
    return jsonify(response)