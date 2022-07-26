import click
from datetime import date, datetime, timedelta
from app import app, db
from app.models import User, Word, Puzzle, Game
from app.api import words


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Word': Word, 'Puzzle': Puzzle, 'Game': Game}

# Flask Commands #

# Displays puzzle commands.
# --> Example: flask help-p
@app.cli.command("help-p")
def help_command():
    """Displays puzzle commands.\n
       --> Example: flask help-p"""

    # Displays help for the puzzle commands.
    click.echo("COMMANDS:\nflask clear - clears all puzzles or data in the database.\n" +
               "flask populate-words - populates the database with all of the words.\n" +
               "flask view-p - views a specific puzzle's info.\n" +
               "flask view - views a certain number of puzzles.\n" +
               "flask generate - inserts a certain numbere of puzzles into the database.\n" +
               "flask update - updates a specific puzzle with new words.")


# Only use this in urgent situations. This deletes all puzzles in the database.
# Example: flask clear confirm
@app.cli.command("clear")
@click.argument("check")
def clear_puzzles(check):
    """Only use this in urgent situations. This deletes all puzzles in the database.\n
       --> Example: flask clear confirm
       --> flask clear all may optionally be used to delete all data in the database."""

    # Checks if the parameter is confirming puzzle deletion.
    # 'confirm' deletes only the puzzles.
    # 'all' deletes all the data in the database.
    if check == "confirm":

        puzzles_deleted = Puzzle.query.delete()
        db.session.commit()

        click.echo("Successfully deleted " + str(puzzles_deleted) + " puzzles.")
    elif check == "all":
        click.echo("Removed " + str(User.query.delete()) + " users.")
        click.echo("Removed " + str(Word.query.delete()) + " words.")
        click.echo("Removed " + str(Puzzle.query.delete()) + " puzzles.")
        click.echo("Removed " + str(Game.query.delete()) + " games.")

        db.session.commit()
    else:
        click.echo("No confirmation was given to clear puzzles. Refer to flask clear --help for more info.")


# Populates the Words table with the words located in the word-answers.txt and word guesses.txt files.
# Both files must be present in the app/api/words folder.
@app.cli.command("populate-words")
def populate_words():
    """Populates the Words table with the words located in the word-answers.txt and word guesses.txt files.\n
       Both files must be present in the app/api/words folder."""

    # Populates the database with the words in the wordlists of word-answers.txt and word-guesses.txt.
    try:
        count = words.populate_database()
        click.echo('Successfully populated the database with ' + str(count) + ' words.')
    except:
        click.echo("Something went wrong. Refer to flask populate-words --help for more info.")


# Displays the puzzle of the given ID or date.
# If a puzzle does not exist, an alternative message is displayed.
# --> flask view-p [ptype] [value]
# --> [ptype] must be either id or date
# --> [value] must be an integer or date
# --> Example: flask view-p 1/5/2022
@app.cli.command("view-p")
@click.argument("ptype")
@click.argument("value")
def view_puzzle(ptype, value):
    """Displays the puzzle of the given ID or date.\n
       If a puzzle does not exist, an alternative message is displayed.\n
       --> flask view-p [ptype] [value]\n
       --> [ptype] must be either id or date\n
       --> [value] must be an integer or date\n
       --> Example: flask view-p 1/5/2022"""

    # Checks the input type.
    if ptype == "id":
        # If a non-integer value is entered, a ValueError is triggered.
        try:
            puzzle = Puzzle.query.get(int(value))
        except ValueError:
            click.echo('An integer must be entered for IDs. Refer to flask view-p --help for more info.')
            return

        # Checks if the puzzle exists before grabbing the data for it.
        if puzzle is None:
            click.echo('Invalid puzzle ID was entered.')
        else:
            click.echo(words.get_puzzle_data(puzzle))
    elif ptype == "date":
        # Converts the value to the format used in the database. If an exception occurs an invalid format was used.
        try:
            value = datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            click.echo('An invalid date format was used. Refer to flask view-p --help for more info.')
            return

        # Checks if the puzzle exists before grabbing the data for it. Ones that do not exist have data generated
        # for it.
        puzzle = Puzzle.query.filter_by(date=value).first()
        if puzzle is None:
            click.echo('No puzzle with this date exists, the generated puzzle for that date is:\n')
            puzzle = words.generate_puzzle(value)
            click.echo(words.get_puzzle_data(puzzle))
        else:
            click.echo(words.get_puzzle_data(puzzle))
    else:
        click.echo('Invalid type was entered. Refer to flask view-p --help for more info.')


# Displays the "number" amount of puzzles, starting from the current day and onwards.
# If a puzzle does not exist, an alternative message is displayed.
# --> flask view [number]
# --> [number] must be an integer
# --> Example: flask view 30
@app.cli.command("view")
@click.argument("number")
def view_puzzles(number):
    """Displays the "number" amount of puzzles, starting from the current day and onwards.\n
       If a puzzle does not exist, an alternative message is displayed.\n
       --> flask view [number]\n
       --> [number] must be an integer\n
       --> Example: flask view 30"""

    # Checks if any words exist in the database.
    wordlist = Word.query.all()
    if len(wordlist) == 0:
        click.echo('No words exist in the database, refer to flask populate-words for more info.')
        return

    # If a non-integer value is entered, a ValueError is triggered.
    try:
        number = int(number)
    except ValueError:
        click.echo('Any entered numbers must be integers. Refer to flask view --help for more info.')
        return

    # Views the number of puzzles starting from the current day.
    day = date.today() - timedelta(days=1)
    for num in range(0, number):
        day = day + timedelta(days=1)

        puzzle = Puzzle.query.filter_by(date=day).first()
        if puzzle is None:
            puzzle = words.generate_puzzle(day)
        click.echo(words.get_puzzle_data(puzzle))


# Generates the "number" amount of puzzles, starting from the current day and onwards.
# If a puzzle already exists, no puzzle is generated for that specific day.
# --> flask generate [number]
# --> [number] must be an integer
@app.cli.command("generate")
@click.argument("number")
def generate_puzzles(number):
    """Generates the "number" amount of puzzles, starting from the current day and onwards.\n
       If a puzzle already exists, no puzzle is generated for that specific day.\n
       --> flask generate [number]\n
       --> [number] must be an integer"""

    # Checks if any words exist in the database.
    wordlist = Word.query.all()
    if len(wordlist) == 0:
        click.echo('No words exist in the database, refer to flask populate-words for more info.')
        return

    # If a non-integer value is entered, a ValueError is triggered.
    try:
        number = int(number)
    except ValueError:
        click.echo('Any entered numbers must be integers. Refer to flask generate --help for more info.')
        return

    # Generates the specific number of puzzles.
    words.generate_puzzles(date.today(), number)
    click.echo('Successfully generated ' + str(number) + ' puzzles.')


# Updates a specific puzzle based on the given values.
# If no puzzle exists for the input given, an error is displayed.
# --> flask update [ptype] [value]
# --> [ptype] must be either id or date
# --> [value] must match the given type and be an integer id or a D/M/Y date
# --> [word1], [word2] and [word3] must be 5 letter words
# --> Example: flask update date 1/5/2022
@app.cli.command("update")
@click.argument("ptype")
@click.argument("value")
@click.argument("word1")
@click.argument("word2")
@click.argument("word3")
def update_puzzles(ptype, value, word1, word2, word3):
    """Updates a specific puzzle based on the given values.\n
       If no puzzle or word exists for the input given, an error is displayed.\n
       --> flask update [ptype] [value] [word1] [word2] [word3]\n
       --> [ptype] must be either id or date\n
       --> [value] must match the given type and be an integer id or a D/M/Y date\n
       --> [word1], [word2] and [word3] must be 5 letter words that exist in the database\n
       --> Words must also be allowed answer words, check word-answers.txt for valid words.\n
       --> Example: flask update date 1/5/2022 trade ether react"""

    # Checks if any words exist in the database.
    wordlist = Word.query.all()
    if len(wordlist) == 0:
        click.echo('No words exist in the database, refer to flask populate-words for more info.')
        return

    # Checks if the connecting letters in the words are valid.
    if word1[-1] != word2[0] or word2[-1] != word3[0] or word3[-1] != word1[0]:
        click.echo("The starting and end letters of the words must match.")
        return

    word1 = Word.query.filter_by(wordname=word1, answer=True).first()
    word2 = Word.query.filter_by(wordname=word2, answer=True).first()
    word3 = Word.query.filter_by(wordname=word3, answer=True).first()
    update_words = [word1,word2,word3]

    # Checks if any of the words do not exist in the database.
    if any(word is None for word in update_words):
        if word1 is None: click.echo("The first word entered is not an allowed answer word.")
        if word2 is None: click.echo("The second word entered is not an allowed answer word.")
        if word3 is None: click.echo("The third word entered is not an allowed answer word.")
        click.echo("Valid answer words are listed in word-answers.txt.")
        return

    # Checks the input type.
    if ptype == "id":
        # If a non-integer value is entered, a ValueError is triggered.
        try:
            puzzle = Puzzle.query.get(int(value))
        except ValueError:
            click.echo('An integer must be entered for IDs. Refer to flask upgrade --help for more info.')
            return

        # Checks if the puzzle exists and updates it.
        if puzzle is None:
            click.echo('Invalid Puzzle ID was entered.')
        else:
            words.update_puzzle(puzzle, update_words)
            click.echo('Puzzle was successfully updated.')

    elif ptype == "date":
        # Converts the value to the format used in the database. If an exception occurs an invalid format was used.
        try:
            value = datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            click.echo('An invalid date format was used. Refer to flask update --help for more info.')
            return

        # Checks if the puzzle exists and updates it.
        puzzle = Puzzle.query.filter_by(date=value).first()
        if puzzle is None:
            click.echo('No puzzle with this date exists.')
        else:
            words.update_puzzle(puzzle, update_words)
            click.echo('Puzzle was successfully updated.')
    else:
        click.echo('Invalid type was entered. Refer to flask update --help for more info.')