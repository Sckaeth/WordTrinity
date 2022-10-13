import math
from flask import request, json, jsonify, session
from app.models import User, Game
from app import db
from app.api import bp
import app.api.load as load
from app.api.errors import error_response

# Rounds a value to the given decimal places, rounding up at 0.5 and upwards and vice versa.
def round_value(number, decimals):
    decimals = 10**decimals
    return math.floor(number * decimals + 0.5)/decimals

# Gets the statistics for the current puzzle or all puzzles, for all users.
def get_puzzle_statistics(type, user=None):
    # If the type is 'user' all puzzles are checked.
    # If the type is 'population' only the current day's puzzle is checked.
    if type == 'user':
        games = Game.query.filter_by().all()
    else:
        games = Game.query.filter_by(puzzleid=load.get_current_puzzleid()).all()

    total_games = 0
    total_wins = 0
    total_guesses = 0

    # Iterates through every game with the chosen puzzles, incrementing variables to track statistics.
    for game in games:
        if game.status > 0:
            total_games += 1

        if game.status == 2:
            total_wins += 1
            total_guesses += game.guesses

    # Returns a rounded win rate percentage and a rounded average guesses per win.
    win_rate, average_guesses = 0, 0
    if total_games != 0:
        win_rate = int(round_value((total_wins/total_games) * 100, 0))

    if total_wins != 0:
        average_guesses = int(round_value(total_guesses/total_wins, 0))

    # If user is input into the function, gets the total guesses and win rate for that input user.
    if user is not None:
        total_guesses = sum(json.loads(user.game_guesses))
        total_games = user.games_won + user.games_lost

        user_winrate = 0
        if total_games != 0:
            user_winrate = int(round_value(user.games_won / (user.games_won + user.games_lost) * 100, 0))

        return win_rate, average_guesses, total_guesses, user_winrate
    return win_rate, average_guesses

# Gets the statistics for the current puzzle or all puzzles, including user-specific and population statistics.
# Should receive 'userid=inputuserid' and 'type=inputtype' as parameters via the GET request.
@bp.route('/stats/game', methods=['GET'])
def get_game_statistics():
    # Gets the userid and type parameters from the GET request.
    userid = request.args.get('userid', '')
    dtype = request.args.get('type', '')

    # If any of the types are invalid, the type is set to None to indicate an error.
    if dtype != 'user' and dtype != 'population':
        dtype = None

    # If the type is invalid or if the input UserID is invalid, return an error response.
    if not load.is_valid_user(userid) or not dtype:
        error_message = "Incorrect data was input."
        return error_response(400, error_message)

    # Gets population statistics for the chosen puzzles and the input user.
    user = User.query.filter_by(userid=userid).first()
    win_rate, average_guesses, total_guesses, user_winrate = get_puzzle_statistics(dtype, user)

    # Returns the statistics that were requested.
    return jsonify({"success": True,
                    "userGuesses": user.game_guesses,
                    "totalGuesses": total_guesses,
                    "userwinrate": user_winrate,
                    "winrate": win_rate,
                    "averageGuesses": average_guesses})

