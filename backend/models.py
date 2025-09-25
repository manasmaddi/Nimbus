from extensions import db
from datetime import datetime

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    s3_url = db.Column(db.String(1024), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_size = db.Column(db.Integer, nullable=False)

    # Add indexes
    __table_args__ = (
        db.Index('idx_user_upload_date', user_id, upload_date),
    )