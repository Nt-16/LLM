# Flask Chat Application

A web-based chat application using Flask and OpenAI's GPT-4 for intelligent conversations.

## Features

- **User Authentication**
  - Secure signup and login
  - Password hashing
  - Session management

- **Chat Interface**
  - Real-time chat with GPT-4
  - Message history
  - Responsive design

- **Security**
  - Environment variable protection
  - SQL injection prevention
  - CSRF protection

## Prerequisites

- Python 3.10 or higher
- OpenAI API key

## Setup Instructions

1. Clone and navigate to the project:
```sh
git clone <repository-url>
cd LLM
```

2. Create and activate a virtual environment:
```sh
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

4. Create `.env` file in root directory and add provided keys

## Running the Application

1. Ensure virtual environment is activated:
```sh
source .venv/bin/activate
```

2. Start the Flask server:
```sh
python backend/app.py
```

3. Access the application through terminal

## License

This project is licensed under the MIT License - see the LICENSE file for details.