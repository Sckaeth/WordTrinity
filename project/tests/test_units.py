from flask import json
import unittest, os, uuid
from datetime import date, timedelta
from app import app, db
from app.models import User, Word, Puzzle, Game
from app.api import load, words, stats


# Tests database functionality, in particular with puzzle generation, users and statistics.
class PuzzleModelCase(unittest.TestCase):

    # Sets up the database at the start of each test function.
    def setUp(self):
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///' + os.path.join(basedir, 'test.db')
        db.create_all()
        db.session.commit()

    # Destroys the database at the end of each test function.
    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Tests database functionality by ensuring users are validly generated, old game statistics are removed and that
    # statistics as a whole are displayed accurately.
    def test_database(self):
        # Generates two users to insert into the test database.
        userid = str(uuid.uuid4()).replace("-", "")
        user1 = User(userid=userid)
        db.session.add(user1)

        userid = str(uuid.uuid4()).replace("-", "")
        user2 = User(userid=userid)
        db.session.add(user2)

        db.session.commit()

        # Test if both users are valid.
        self.assertTrue(load.is_valid_user(user1.userid))
        self.assertTrue(load.is_valid_user(user2.userid))

        # Populates the word lists.
        count = words.populate_database()

        # Tests if the word population was successful.
        self.assertEqual(len(Word.query.all()), count)

        # Generates two puzzles to enter into the database.
        puzzle1 = words.generate_puzzle(date.today())
        db.session.add(puzzle1)
        puzzle2 = words.generate_puzzle(date.today() + timedelta(days=1))
        db.session.add(puzzle2)
        db.session.commit()

        # Adds four games into the database, two for each user.
        game1 = Game(userid=user1.userid, puzzleid=1)
        game2 = Game(userid=user2.userid, puzzleid=1)
        game1.status = 2
        game1.guesses = 6
        game2.status = 1
        db.session.add(game1)
        db.session.add(game2)

        game1 = Game(userid=user1.userid, puzzleid=2)
        game1.status = 2
        game1.guesses = 3
        game2 = Game(userid=user2.userid, puzzleid=2)
        game2.status = 2
        game2.guesses = 1
        db.session.add(game1)
        db.session.add(game2)

        # Sets up a fake environment in which one user has won two games and one user has lost and won a game.
        user1.game_guesses = json.dumps([0, 0, 1, 0, 0, 1, 0, 0, 0, 0])
        user1.games_won += 2
        user2.game_guesses = json.dumps([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        user2.games_won += 1
        user2.games_lost += 1
        db.session.commit()

        # Generates statistics for both puzzles.
        win_rate1, average_guesses1 = stats.get_puzzle_statistics('population')
        win_rate2, average_guesses2 = stats.get_puzzle_statistics('user')

        # Tests if the statistics returned are accurate.
        self.assertEqual(75, win_rate1)
        self.assertEqual(50, win_rate2)
        self.assertEqual(3, average_guesses1)
        self.assertEqual(6, average_guesses2)

        # Updates a puzzle to remove old game data.
        word1 = Word.query.get(puzzle2.wordid1)
        word2 = Word.query.get(puzzle2.wordid2)
        word3 = Word.query.get(puzzle2.wordid3)

        words.update_puzzle(puzzle1, [word1,word2,word3])

        win_rate1, average_guesses1 = stats.get_puzzle_statistics('population')
        win_rate2, average_guesses2 = stats.get_puzzle_statistics('user')

        # Tests if the statistics returned reflect the removal of the old game data.
        self.assertEqual(100, win_rate1)
        self.assertEqual(0, win_rate2)
        self.assertEqual(2, average_guesses1)
        self.assertEqual(0, average_guesses2)

    # Tests if 7 puzzles are generated when no puzzle exists for the current day.
    def test_puzzle_database(self):
        # Populates the word lists.
        count = words.populate_database()

        # Tests if the word population was successful.
        self.assertEqual(len(Word.query.all()), count)

        # Attempts to get the current day's PuzzleID, instead generating puzzles for the next 7 days.
        load.get_current_puzzleid()

        # Tests if the total amount of puzzles is equivalent to 7.
        self.assertEqual(7, len(Puzzle.query.all()))

if __name__ == '__main__':
    unittest.main(verbosity=2)