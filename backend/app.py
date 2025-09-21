import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import db
from routes.file_routes import file_bp
from models import File 

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app) 

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(file_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5000, debug=True)