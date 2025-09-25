# Standard library
from datetime import datetime
import os

# Third-party imports
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

# Local application imports
from extensions import db
from models import File
from validator import requires_auth

# Configure logging
logger = logging.getLogger(__name__)

# Create a Blueprint for the file routes
file_bp = Blueprint('files', __name__)

# Constants
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_aws_credentials() -> None:
    required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME', 'S3_BUCKET_REGION']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def upload_to_s3(file: FileStorage, bucket_name: str, region: str) -> [str]:
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=region
        )

        filename = secure_filename(file.filename)
        s3.upload_fileobj(file, bucket_name, filename)
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"

    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {str(e)}")
        return None

@file_bp.route('/upload', methods=['POST'])
@requires_auth
def upload_file() -> Tuple[dict, int]:
    user_id = request.auth_payload['sub']

    # File validation
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File size exceeds maximum limit'}), 400

    try:
        s3_url = upload_to_s3(
            file,
            os.environ['S3_BUCKET_NAME'],
            os.environ['S3_BUCKET_REGION']
        )
        
        if not s3_url:
            return jsonify({'error': 'Failed to upload file to S3'}), 500

        new_file = File(
            user_id=user_id,
            filename=secure_filename(file.filename),
            s3_url=s3_url,
            upload_date=datetime.utcnow(),
            file_size=size
        )
        db.session.add(new_file)
        db.session.commit()

        # Invalidate cache
        cache.delete(f'user_files_{user_id}')

        return jsonify({
            'message': 'File uploaded successfully',
            'url': s3_url,
            'file_id': new_file.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@file_bp.route('/files', methods=['GET'])
@requires_auth
def list_files() -> Tuple[dict, int]:

    user_id = request.auth_payload['sub']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Check cache first
    cache_key = f'user_files_{user_id}_p{page}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result), 200

    try:
        files = File.query.filter_by(user_id=user_id)\
            .order_by(File.upload_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        file_list = [{
            'id': file.id,
            'filename': file.filename,
            'url': file.s3_url,
            'upload_date': file.upload_date.isoformat(),
            'file_size': file.file_size
        } for file in files.items]

        result = {
            'files': file_list,
            'total': files.total,
            'pages': files.pages,
            'current_page': files.page
        }

        # Cache the result
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error fetching files: {str(e)}")
        return jsonify({'error': 'Failed to retrieve files'}), 500