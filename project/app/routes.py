from datetime import timedelta
from flask import render_template, session
from app import app, db
from app.api import load


# Sets the current session to persist for 365 days of inactivity.
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=365)


# Sets the route for the index page, initialising any session variables if they do not exist.
@app.route('/')
def index():
    # Initialises the UserID session variable if it does not already exist.
    if 'userid' not in session or not load.is_valid_user(session['userid']):
        load.generate_userid()

    # GameID is set to a placeholder of 0 until it is later generated.
    if 'gameid' not in session:
        session['gameid'] = 0

    return render_template('index.html')
