from extensions import db
from datetime import datetime

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, nullable=False)
    s3_url = db.Column(db.String, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)