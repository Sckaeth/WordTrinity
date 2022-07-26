from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from app.api import bp

# Generates an error response based off the input status code and provided message.
def error_response(status_code, message=None):
    # If the status code is defined, send a proper error response. If not, a JSON response with a message suffices.
    if status_code is not None:
        payload = {'success': False, 'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    else:
        payload = {'success': False}

    if message:
        payload['message'] = message

    response = jsonify(payload)
    if status_code is not None:
        response.status_code = status_code

    return response
