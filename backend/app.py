import os
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from validator import requires_auth, AuthError

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for your React frontend
CORS(app) 

# Load necessary credentials and configuration from environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_BUCKET_REGION = os.environ.get('S3_BUCKET_REGION')

# --- Helper functions ---

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    """
    Error handler for AuthError.
    This converts authentication errors into a JSON response.
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

def upload_to_s3(file, bucket_name, region):
    """Uploads a file object to an AWS S3 bucket."""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise NoCredentialsError("AWS credentials not configured.")

    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=region
    )

    filename = secure_filename(file.filename)
    try:
        s3.upload_fileobj(file, bucket_name, filename)
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"
        return s3_url
    except ClientError as e:
        app.logger.error(f"S3 upload failed: {e}")
        return None


# --- The REST API Endpoint ---

@app.route('/api/upload', methods=['POST'])
@requires_auth # This is the simple decorator that protects the endpoint
def upload_file():
    """Handles file uploads from the frontend."""
    # 1. File Check
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400

    # 2. S3 Upload
    if file:
        try:
            s3_url = upload_to_s3(file, S3_BUCKET_NAME, S3_BUCKET_REGION)
            
            # The 's3_url' is now available to be stored in your database
            return jsonify({'message': 'File uploaded successfully!', 'url': s3_url}), 200
        except NoCredentialsError:
            return jsonify({'message': 'AWS credentials are not configured correctly.'}), 500
        except Exception as e:
            app.logger.error(f"An error occurred: {e}")
            return jsonify({'message': 'An unexpected error occurred.'}), 500

    return jsonify({'message': 'An unexpected error occurred.'}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
