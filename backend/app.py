import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend import create_app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from frontend.models import db
        # db.create_all()  # Create database tables
    app.run(debug=True)