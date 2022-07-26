from flask import request, json, jsonify, session
from app import app, db
from app.models import User, Game, Puzzle, Word
from app.api import bp
import app.api.load as load
from app.api.errors import error_response

# The guess limit for all puzzles.
guess_limit = 10


# Processes a user's won game, changing their internally stored statistics as required.
def process_win():
    user = User.query.filter_by(userid=session['userid']).first()
    user.games_won += 1

    # The game status is set to 2, denoting it has been won.
    game = load.get_game()
    game.status = 2

    user_guesses = json.loads(user.game_guesses)
    user_guesses[game.guesses - 1] += 1
    user.game_guesses = json.dumps(user_guesses)

    db.session.commit()


# Processes a user's lost game, changing their interally stored statistics as required.
def process_loss():
    user = User.query.filter_by(userid=session['userid']).first()
    user.games_lost += 1

    # The game status is set to 1, denoting it has been lost.
    game = load.get_game()
    game.status = 1

    db.session.commit()


# Updates the letter positions stored within the current game.
# The positions are stored in the format of a list of 12 characters, each representing a slot in the game.
def get_letter_pos(lpositions):
    # Converts a string of each character in each guessed word to a list. (15 characters long)
    # Any characters that are a '0' represent a slot that was not submitted as a guess.
    lpositions = list(lpositions)
    g_lpositions = json.loads(load.get_game().lpositions)

    # Replaces every connecting letter (between two words) with a '#', prioritising those that are a '0'.
    for num in range(0, 3):
        if num == 0:
            if not lpositions[-1] == '0':
                lpositions[0] = lpositions[-1]
            lpositions[-1] = '#'
        else:
            if lpositions[5 * num - 1] == '0':
                lpositions[5 * num - 1] = '#'
            else:
                lpositions[5 * num] = '#'

    # Creates a new list with the letters that are not '#'s, to generate a 12 character list.
    lpositions = [letter for letter in lpositions if letter != '#']

    # Replaces only the letters that are not '0'.
    for index, letter in enumerate(lpositions):
        if not letter == '0':
            g_lpositions[index] = letter

    return g_lpositions


# Updates the guess positions stored within the current game.
# This is stored in a list of twelve lists (representing a puzzle slot), each containing
# an element for a unique letter in the puzzle.
def get_guess_pos(game, data, guesses):
    # Gets the current guess positions and a list of the puzzle's unique letters.
    gpositions = json.loads(game.gpositions)
    unique_letters = load.get_unique_letters()

    # Iterates through every word in the stored results of the guess check.
    for word_index, word in enumerate(data):
        if word == "None":
            continue

        # Iterates through every guess-letter value (0, 1, 2, 3, 4) in the word.
        for letter_index, letter in enumerate(word):
            # If the current letter being checked isn't in the puzzle, it is ignored.
            curr_letter = guesses[word_index][letter_index]
            if curr_letter not in unique_letters:
                continue

            # If the value of the current guess-letter is above the existing value in the guess positions list,
            # it is replaced with the current guess-letter value.
            # Thus, values of 3 (correct letter and word) are prioritised, and so on.
            curr_index = unique_letters.index(curr_letter)
            existing_index = ((word_index * 5) - word_index + letter_index) % 12

            if letter > gpositions[existing_index][curr_index]:
                gpositions[existing_index][curr_index] = letter

    return gpositions


# Validates the words input into the server.
# Should receive '["guess1","guess2","guess3"]' via the POST request.
@bp.route('/game/guess', methods=['POST'])
def check_guess():
    if session['userid'] is None or session['gameid'] is None:
        error_message = "Something went wrong! Try reloading the page."
        return error_response(400, error_message)

    # Check if current game is valid for the day's puzzle.
    if load.get_game() is None:
        error_message = "The current game is invalid, please reload the page."
        return error_response(None, error_message)

    # Checks if the current game has already ended.
    game = load.get_game()
    if game.status > 0:
        error_message = "The game has already ended."
        return error_response(None, error_message)

    # Loads the JSON/String array from the request into Python list.
    guesses = request.get_json()

    # Intialises success (whether the check ended successfully), lpositions (to form a new lpositions list)
    # and numcorr to track the number of correct letters.
    success = True
    lpositions = ""
    numcorr = 0

    # Initialises two empty lists, containing the guess data and the letters with values of '0's to check against other
    # words.
    data, blankletters = [], []
    current_words = load.get_puzzle_words()

    # Checks every word in the list of guesses.
    for index, word in enumerate(guesses):
        # If the word is None, ignore it.
        if word == "None":
            data.append("None")
            lpositions += '00000'
            continue
        # If any word is under 5 characters, ignore it and mark success as False.
        if len(word) != 5:
            success = False
            error_message = "Words must contain 5 letters!"
            continue
        # If any word is not a valid word, ignore it and mark success as false.
        word_db = Word.query.filter_by(wordname=word).first()
        if word_db is None:
            success = False
            error_message = "An invalid word was entered!"
            continue

        wordcheck = []
        wordcorrect = []

        # Checks every letter in each guess word, from back to front.
        for i in range(4, -1, -1):
            # If the letter matches the same letter in the list of puzzle words, it is correct. (value of 4)
            if word[i] == current_words[index][i]:
                wordcheck.append(4)
                numcorr = numcorr + 1
                wordcorrect.append(word[i])

            # If not, the letter is either in the correct word (but different position) or correct position (but
            # different word).
            else:
                wordocc = len(current_words[index].split(word[i])) - 1
                guessocc = len(word.split(word[i])) - 1
                wordcorrect.append('0')

                # If the occurrences of same word, different positions in the guess word exceeds the amount in the
                # actual word then the current letter is a blank position. (value of 1)
                if guessocc > wordocc:
                    word = word[:i] + "#" + word[i + 1:]
                    wordcheck.append(1)
                    blankletters.append((index, i))

                # Else, the current letter is in the correct word but different position. (value of 3)
                else:
                    wordcheck.append(3)

        # Both lists are reversed as the process occurs from back to front.
        wordcheck.reverse()
        data.append(wordcheck)

        wordcorrect.reverse()
        lpositions += "".join(wordcorrect)

    # Scan all data to implement checking exact positions between words. (value of 2)
    for blank in blankletters:
        index = blank[0]
        char = blank[1]

        letter = guesses[index][char]
        for words in current_words:
            if words[char] == letter:
                data[index][char] = 2

    # Status codes:
    # 0 -> Game in progress.
    # 1 -> Game lost.
    # 2 -> Game won.
    if success:
        # Update gpositions and lpositions in the games data.
        game.gpositions = json.dumps(get_guess_pos(game, data, guesses))
        game.lpositions = json.dumps(get_letter_pos(lpositions))
        game.guesses += 1

        db.session.commit()

        puzzle_lpositions = "".join([current_words[0],current_words[1][1:],current_words[2][1:4]])
        game_lpositions = "".join(str(letter) for letter in json.loads(game.lpositions))
        # If the game's correct letter positions matches the puzzle's letters, the game has been won.
        if puzzle_lpositions == game_lpositions:
            process_win()
            return jsonify({"success": True,
                            "response": json.dumps(data),
                            "status": 2})

        # If the number of guesses exceeds the guess limit or submit has occurred (no 'None' present in the guesses)
        # then the game is a loss if a win has not already occurred.
        if game.guesses >= guess_limit or 'None' not in guesses:
            process_loss()
            return jsonify({"success": True,
                            "response": json.dumps(data),
                            "status": 1})

        return jsonify({"success": True, "response": json.dumps(data), "status": 0})
    return error_response(None, error_message)
