import os
import json
from urllib.request import urlopen
from functools import wraps
from jose import jwt
from flask import request, jsonify

# Load environment variables for Auth0
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
API_IDENTIFIER = os.environ.get("AUTH0_API_IDENTIFIER")
ALGORITHMS = ["RS256"]

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected"}, 401)
    
    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": "Authorization header must start with Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",   "description": "Authorization header must be Bearer token"}, 401)
    
    token = parts[1]
    return token

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_auth_header()
            jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
            jwks = json.loads(jsonurl.read())
            
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)

            if not rsa_key:
                raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)
            
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_IDENTIFIER,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )

            request.auth_payload = payload
        except AuthError as e:
            response = jsonify(e.error)
            response.status_code = e.status_code
            return response
        except jwt.ExpiredSignatureError:
            response = jsonify({"code": "token_expired", "description": "Token is expired"})
            response.status_code = 401
            return response
        except jwt.JWTClaimsError:
            response = jsonify({"code": "invalid_claims", "description": "Incorrect claims. Check the audience and issuer"})
            response.status_code = 401
            return response
        except Exception:
            response = jsonify({"code": "invalid_token", "description": "Unable to parse authentication token."})
            response.status_code = 401
            return response

        return f(*args, **kwargs)
    return decorated

