from flask import json
from app import db
from app.models import User, Word, Puzzle, Game
import app.api.load as load
from datetime import date, timedelta
import random


# Returns a string summarising a single puzzle's data when input with a puzzle object.
def get_puzzle_data(puzzle):
    words = load.get_puzzle_words(None, puzzle)

    return_string = "Puzzle: "
    if puzzle.puzzleid is not None:
        return_string = "Puzzle " + str(puzzle.puzzleid) + ": "

    for word in words:
        return_string += word + " "
    return_string += "(" + str(puzzle.date) + ")"

    return return_string


# Loads the Word table with all the words in the word lists.
# Words are loaded in alphabetical order, per list, to prevent any puzzles breaking from previous populations.
# Word lists were obtained from (which were originally extracted from Wordle):
# https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b
# https://gist.github.com/cfreshman/cdcdf777450c5b5301e439061d29694c
def populate_database():
    # Clears all words from the database.
    words = Word.query.all()
    for word in words:
        db.session.delete(word)

    db.session.commit()

    # Defines two word lists that are located in the words folder.
    # The first list must only contain potential answers to puzzles. (commonly used words)
    wordlists = ['app/api/words/word-answers.txt','app/api/words/word-guesses.txt']
    answer = True
    count = 0

    # For each wordlist, load the words within it into the database.
    for index, wordlist in enumerate(wordlists):
        wordlist = open(wordlist, 'r')
        for word in wordlist:
            # If it is the first list, all the words are answers.
            if index == 1:
                answer = False

            word = word.strip()
            if len(word) == 5:
                word = Word(wordname=word, firstletter=word[0], lastletter=word[-1], answer=answer)
                count += 1
                db.session.add(word)
        wordlist.close()

    db.session.commit()
    return count

# Generates a puzzle for an input date. Each date has a puzzle that is the same, no matter how many times it is
# generated for that day.
def generate_puzzle(day):
    # Sets the seed for random generation to the date as a string. (ensures that each date always has the same puzzle)
    random.seed(str(day))

    while True:
        # Generates a list of every word object and then shuffles the list.
        words = Word.query.filter_by(answer=True).all()
        random.shuffle(words)
        # Generates a random word from this list.
        index = random.randint(0, 50000) % len(words)
        word1 = words[index]

        # Selects only words with a matching connecting letter.
        words = Word.query.filter_by(firstletter=word1.lastletter, answer=True).all()
        random.shuffle(words)
        # If the length of the list is 0, the entire loop continues
        # to ensure that the function does not get stuck on an impossible starting/ending letter combination.
        if len(words) > 0:
            index = random.randint(0, 50000) % len(words)
            word2 = words[index]
        else:
            continue

        words = Word.query.filter_by(firstletter=word2.lastletter, lastletter=word1.firstletter, answer=True).all()
        random.shuffle(words)
        if len(words) > 0:
            index = random.randint(0, 50000) % len(words)
            word3 = words[index]
        else:
            continue

        break

    puzzle = Puzzle(wordid1=word1.wordid, wordid2=word2.wordid, wordid3=word3.wordid, date=day)
    return puzzle


# Generates several puzzles for "n" number of days, starting from the initial input date.
# These puzzles are committed to the database automatically.
def generate_puzzles(puzzle_date, n):
    # Reduces the date input by 1 so that a puzzle is generated for the input date too.
    puzzle_date -= timedelta(days=1)

    # Generates a puzzle for every subsequent day.
    for day in range(0, n):
        puzzle_date += timedelta(days=1)

        # Checks if a puzzle for the day already exists.
        puzzle = Puzzle.query.filter_by(date=puzzle_date).first()
        if puzzle is None:
            db.session.add(generate_puzzle(puzzle_date))

    # Commits the puzzles to the database.
    db.session.commit()


# Updates an input puzzle. If the puzzle has any games attached to it, these games are deleted and any user data
# attached to these games is also reverted.
def update_puzzle(puzzle, update_words):
    # Grabs every game attached to the puzzle.
    games = puzzle.games.all()
    for game in games:
        # If the game has ended, remove statistics that have been added to users.
        if game.status > 0:
            user = User.query.filter_by(userid=game.userid).first()
            # If the game has been won, remove a win and guesses for the win.
            if game.status == 2:
                user_guesses = json.loads(user.game_guesses)
                user_guesses[game.guesses - 1] -= 1
                user.game_guesses = json.dumps(user_guesses)
                user.games_won -= 1
            # If the game has been lost, remove a loss.
            elif game.status == 1:
                user.games_lost -= 1

        db.session.delete(game)

    # Updates the puzzle's WordIDs with the input word's IDs.
    puzzle.wordid1 = update_words[0].wordid
    puzzle.wordid2 = update_words[1].wordid
    puzzle.wordid3 = update_words[2].wordid

    db.session.commit()
