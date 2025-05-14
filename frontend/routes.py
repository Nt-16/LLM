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
@login_required
def ask():
    if check_cooldown():
        return redirect(url_for('main.home'))
    
    text = request.form.get('text', '')
    words = text.split()
    
    # Free user word limit
    if current_user.user_type == 'free' and len(words) > 20:
        flash('Free users limited to 20 words', 'danger')
        return redirect(url_for('main.home'))
    
    # Token check
    required_tokens = len(words)
    if current_user.balance < required_tokens:
        if current_user.user_type == 'paid':
            current_user.balance = max(0, current_user.balance - (required_tokens // 2))
            db.session.commit()
            flash('Insufficient tokens - 50% penalty applied', 'danger')
        else:
            flash('Please upgrade to paid plan for more capacity', 'warning')
        return redirect(url_for('main.home'))
    
    # Process with OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "Highlight changes with <mark> tags"
            }, {
                "role": "user",
                "content": text
            }]
        )
        
        # Deduct tokens
        current_user.balance -= required_tokens
        current_user.last_submission = datetime.utcnow()
        db.session.commit()
        
        return render_template('result.html', 
                            original=text,
                            corrected=response.choices[0].message.content)
    
    except Exception as e:
        current_app.logger.error(f"OpenAI Error: {str(e)}")
        flash('Error processing your request', 'danger')
        return redirect(url_for('main.home'))
    

@bp.route('/submit', methods=['POST'])
@login_required
def submit_text():
    # Free user cooldown check
    if current_user.user_type == 'free':
        if current_user.last_submission and \
           (datetime.utcnow() - current_user.last_submission) < timedelta(minutes=3):
            return jsonify({'error': 'Free user cooldown active'}), 429

    # Word count validation
    text = request.json.get('text', '')
    word_count = len(text.split())
    
    if current_user.user_type == 'free' and word_count > 20:
        current_user.last_submission = datetime.utcnow()
        db.session.commit()
        return jsonify({'error': 'Free user word limit exceeded'}), 400

    # Process blacklist words
    blacklisted_words = Blacklist.query.filter_by(status='approved').all()
    processed_text, penalty = process_blacklist(text, blacklisted_words)
    
    # Token management
    required_tokens = word_count + penalty
    if current_user.balance < required_tokens:
        if current_user.user_type == 'paid':
            current_user.balance = max(0, current_user.balance - (required_tokens // 2))
            db.session.commit()
        return jsonify({'error': 'Insufficient tokens'}), 402

    # Deduct tokens
    current_user.balance -= required_tokens
    db.session.add(TokenTransaction(
        user_id=current_user.id,
        amount=-required_tokens,
        transaction_type='usage'
    ))
    
    # Save correction history
    correction = CorrectionHistory(
        user_id=current_user.id,
        original_text=text,
        corrected_text=processed_text,
        correction_type='self',
        tokens_used=required_tokens
    )
    db.session.add(correction)
    db.session.commit()
    
    return jsonify({'processed_text': processed_text})

@bp.route('/llm-correct', methods=['POST'])
@login_required
def llm_correct():
    try:
        text = request.json.get('text', '')
        
        # Free user word limit check
        if current_user.user_type == 'free':
            word_count = len(text.split())
            if word_count > 20:
                return jsonify({
                    'error': 'Free users limited to 20 words'
                }), 402

        # Process with OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "Highlight changes with <mark class='llm-correction'> tags"
            }, {
                "role": "user",
                "content": text
            }]
        )
        
        return jsonify({
            'original': text,
            'corrected': response.choices[0].message.content
        })
    
    except Exception as e:
        current_app.logger.error(f"LLM Correction Error: {str(e)}")
        return jsonify({'error': 'AI processing failed'}), 500

@bp.route('/self-correct', methods=['POST'])
@login_required
def self_correct():
    try:
        text = request.json.get('text', '')
        processed_text = process_blacklist(text)
        
        # Calculate token cost
        original_words = len(text.split())
        processed_words = len(processed_text.split())
        token_cost = max(0, original_words - processed_words) // 2
        
        # Update user balance
        current_user.balance -= token_cost
        db.session.commit()
        
        return jsonify({
            'original': text,
            'corrected': processed_text,
            'tokens_used': token_cost
        })
    
    except Exception as e:
        current_app.logger.error(f"Self Correction Error: {str(e)}")
        return jsonify({'error': 'Self-correction failed'}), 500

def process_blacklist(text):
    # Get approved blacklist entries
    blacklist = Blacklist.query.filter_by(status='approved').all()
    for entry in blacklist:
        text = text.replace(entry.word, '*' * len(entry.word))
    return text

@bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade_account():
    if current_user.user_type != 'free':
        flash('You are already a paid user', 'info')
        return redirect(url_for('main.home'))
    
    # Add payment processing logic here
    current_user.user_type = 'paid'
    db.session.commit()
    flash('Account upgraded successfully!', 'success')
    return redirect(url_for('main.home'))

def check_cooldown():
    if current_user.user_type == 'free' and current_user.last_submission:
        remaining = (current_user.last_submission + 
                    timedelta(minutes=3) - datetime.utcnow()).seconds // 60
        if remaining > 0:
            flash(f'Free users can only submit every 3 minutes ({remaining} min remaining)', 'warning')
            return True
    return False