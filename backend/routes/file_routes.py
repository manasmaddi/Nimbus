import os
import boto3
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError, ClientError
from validator import requires_auth
from extensions import db
from models import File
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Create a Blueprint for the file routes
file_bp = Blueprint('files', __name__)

# --- Helper functions ---

def upload_to_s3(file, bucket_name, region):
    """Uploads a file object to an AWS S3 bucket."""
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    if not aws_access_key_id or not aws_secret_access_key:
        raise NoCredentialsError("AWS credentials not configured.")

    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region
    )

    filename = secure_filename(file.filename)
    try:
        s3.upload_fileobj(file, bucket_name, filename)
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"
        return s3_url
    except ClientError as e:
        print(f"S3 upload failed: {e}")
        return None

# --- The API Endpoints ---

@file_bp.route('/upload', methods=['POST'])
@requires_auth
def upload_file():
    user_id = request.auth_payload['sub']

    # 1. File Check
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400

    # 2. S3 Upload
    if file:
        try:
            s3_url = upload_to_s3(file, os.environ.get('S3_BUCKET_NAME'), os.environ.get('S3_BUCKET_REGION'))
            
            # 3. Store Metadata in the Database
            if s3_url:
                new_file = File(
                    user_id=user_id,
                    filename=secure_filename(file.filename),
                    s3_url=s3_url,
                    upload_date=datetime.utcnow()
                )
                db.session.add(new_file)
                db.session.commit()
                return jsonify({'message': 'File uploaded successfully!', 'url': s3_url}), 200
            else:
                return jsonify({'message': 'S3 upload failed.'}), 500

        except NoCredentialsError:
            return jsonify({'message': 'AWS credentials are not configured correctly.'}), 500
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({'message': 'Database error occurred.'}), 500
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return jsonify({'message': 'An unexpected error occurred.'}), 500

    return jsonify({'message': 'An unexpected error occurred.'}), 500

@file_bp.route('/files', methods=['GET'])
@requires_auth
def list_files():
    """Fetches a list of files for the authenticated user from the database."""
    user_id = request.auth_payload['sub']
    
    try:
        files = File.query.filter_by(user_id=user_id).all()
        file_list = [
            {'id': file.id, 'filename': file.filename, 'url': file.s3_url, 'upload_date': file.upload_date}
            for file in files
        ]
        return jsonify(file_list), 200
    except Exception as e:
        print(f"Error fetching files: {e}")
        return jsonify({'message': 'Failed to retrieve files.'}), 500
