from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from frontend.models import User, db
from openai import OpenAI
from dotenv import load_dotenv
import os
from sqlalchemy import func
import logging

bp = Blueprint('main', __name__)
load_dotenv()  # Load environment variables explicitly

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@bp.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        # Debug logging
        current_app.logger.debug(f"\nLogin attempt - Email: {email}")

        user = User.query.filter(func.lower(User.email) == email).first()

        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember', False))
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

        existing_user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
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
    try:
        # Request logging
        current_app.logger.debug("\n=== INCOMING REQUEST ===")
        current_app.logger.debug(f"Headers: {dict(request.headers)}")
        current_app.logger.debug(f"Raw JSON: {request.get_data(as_text=True)}")

        # Validate input
        if not request.is_json:
            current_app.logger.error("Invalid request: Not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        text = request.json.get('question', '').strip()
        if not text:
            current_app.logger.error("Empty question received")
            return jsonify({"error": "No text provided"}), 400

        current_app.logger.debug(f"\n--- USER INPUT ---\n{text}\n")

        # Create prompt
        editing_prompt = (
            "Fix only spelling, grammar, and punctuation errors in the following text. "
            "Preserve the original structure and intent exactly as written. "
            "Do not rephrase or restructure. Text:\n" + text
        )

        try:
            # API call
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional proofreader. Only fix technical writing errors without changing meaning."},
                    {"role": "user", "content": editing_prompt},
                ],
                temperature=0.1,
                max_tokens=2000
            )
        except openai.APIConnectionError as e:
            current_app.logger.error(f"API Connection Error: {str(e)}")
            return jsonify({"error": "Connection to AI service failed"}), 500
        except openai.RateLimitError as e:
            current_app.logger.error(f"Rate Limit Error: {str(e)}")
            return jsonify({"error": "AI service overloaded, please try again later"}), 429
        except openai.APIError as e:
            current_app.logger.error(f"API Error: {str(e)}")
            return jsonify({"error": "AI service error"}), 500

        # Validate response
        if not completion.choices or not completion.choices[0].message.content:
            current_app.logger.error("Invalid API response structure")
            return jsonify({"error": "AI service returned unexpected format"}), 500

        edited_text = completion.choices[0].message.content
        current_app.logger.debug(f"\n--- EDITED TEXT ---\n{edited_text}\n")

        return jsonify({'answer': edited_text})

    except Exception as e:
        current_app.logger.error(f"Unhandled Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500