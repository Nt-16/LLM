from frontend import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ✅ This line creates the User table
    app.run(debug=True)
