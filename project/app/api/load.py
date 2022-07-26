from flask import request, json, jsonify, session
import uuid
from datetime import date
from app import app, db
from app.models import User, Game, Puzzle, Word
from app.api import bp
from app.api import words
from app.api.errors import error_response

# Checks if the current user exists in the database.
def is_valid_user(userid):
    user = User.query.filter_by(userid=userid).first()
    return user is not None


# Generates a UserID that does not exist in the database and inserts it into the database.
def generate_userid():
    while True:
        # A UserID is generated via the UUID4 function.
        new_userid = str(uuid.uuid4()).replace("-", "")
        # If the generated UserID does not already exist in the database it is stored in the session.
        if not is_valid_user(new_userid):
            session['userid'] = new_userid
            user = User(userid=new_userid)
            db.session.add(user)
            db.session.commit()
            break


# Changes the current UserID to a new one if it exists in the database.
# Should receive 'userid' via the PUT request.
@bp.route('/load/changeuser', methods=['PUT'])
def change_userid():
    if len(request.data) == 0:
        error_message = "No UserID was entered."
        return error_response(None, error_message)

    userid = request.get_json()

    if is_valid_user(userid):
        session['userid'] = userid
        return jsonify({"success": True})

    error_message = "This UserID is currently not linked to any account."
    return error_response(None, error_message)


# Gets the current puzzle's ID. Generates a puzzle for the current date if none exists.
def get_current_puzzleid():
    puzzle = Puzzle.query.filter_by(date=date.today()).first()
    if puzzle is None:
        words.generate_puzzles(date.today(), 7)
        puzzle = Puzzle.query.filter_by(date=date.today()).first()

    return puzzle.puzzleid


# Gets a word from an input WordID.
def get_word(wordid):
    word = Word.query.filter_by(wordid=wordid).first()
    return word


# Gets a list of the chosen puzzle's words in the format ['word1','word2','word3'].
def get_puzzle_words(puzzleid=None, puzzle=None):
    # If no PuzzleID is defined and no Puzzle is input, the current day's ID is used.
    if puzzleid is None and puzzle is None:
        puzzleid = get_current_puzzleid()

    # If no puzzle is defined, the current day's ID is used to generate a puzzle. (or any input PuzzleID)
    if puzzle is None:
        puzzle = Puzzle.query.filter_by(puzzleid=puzzleid).first()

    # The puzzle's current words are grabbed in their order.
    current_words = [get_word(puzzle.wordid1).wordname,
                     get_word(puzzle.wordid2).wordname,
                     get_word(puzzle.wordid3).wordname]

    return current_words


# Generates a list of letters used in the current puzzle.
def get_letters():
    current_words = get_puzzle_words()

    letters = list("".join(current_words))
    # Removes the first occurrence of each connecting puzzle letter from the array.
    for num in range(0,3):
        letters.remove(current_words[num][0])
    letters.sort()

    return letters


# Generates a list of unique letters used in the current puzzle.
def get_unique_letters():
    unique_letters = list(set("".join(get_puzzle_words())))
    unique_letters.sort()

    return unique_letters


# Returns the user's game for the current puzzle with a specific GameID.
def get_game():
    game = Game.query.filter_by(userid=session['userid'], gameid=session['gameid'], puzzleid=get_current_puzzleid()).first()
    return game


# Gets the user's game for the current puzzle, if it exists.
def get_user_game():
    game = Game.query.filter_by(userid=session['userid'], puzzleid=get_current_puzzleid()).first()
    return game


# Generates a game and inserts it into the database, also stores the generated game as the current game.
def generate_game():
    game = Game(userid=session['userid'], puzzleid=get_current_puzzleid())

    # Generates a gpositions list for the game, containing 12 lists each with an element for every individual
    # unique letter.
    gpositions = []
    unique_letters = len(set("".join(get_puzzle_words())))

    for num in range(0,12):
        gpositions.append([0]*unique_letters)
    game.gpositions = json.dumps(gpositions)

    # Commits the data to the database and stores the GameID as a session variable.
    db.session.add(game)
    db.session.commit()
    session['gameid'] = game.gameid

    return game


# Finds the current user's game (or generates one) and then returns data to allow for it to be loaded.
@bp.route('/load/game', methods=['PUT'])
def load_game():
    if session['userid'] is None or session['gameid'] is None:
        error_message = "Something went wrong! Try reloading the page."
        return error_response(400, error_message)

    # Checks if the current game is valid for the day's puzzle.
    if get_game() is None:
        game = get_user_game()
        # Checks if the user has a game for the current day already.
        if game is not None:
            session['gameid'] = game.gameid
        else:
            # Generates a new game if invalid.
            game = generate_game()
    else:
        # Finds the pre-existing game if it is valid.
        game = get_game()

    unique_letters = get_unique_letters()
    unique_indexes = get_letters()
    # Stores the indexes of each unique letter, used to refer to specific letters in the gpositions list.
    for index, letter in enumerate(unique_indexes):
        unique_indexes[index] = unique_letters.index(letter)

    return jsonify({"success": True,
                    "letters": json.dumps(get_letters()),
                    "uniqueletters": json.dumps(unique_indexes),
                    "guessCount": game.guesses,
                    "status": game.status,
                    "gpositions": game.gpositions,
                    "lpositions": game.lpositions})