import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from routes.file_routes import file_bp

# Loading environment variables from a .env file
load_dotenv()

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for your React frontend
CORS(app) 

# Load necessary credentials and configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

# --- Register Blueprints ---
app.register_blueprint(file_bp, url_prefix='/api')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)
