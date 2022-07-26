# **Word Trinity**
## Description
Word Trinity is a daily word puzzle game that revolves around discovering a trinity of hidden words that change every day. Through the strategic placement of letters on a triangle containing 12 slots, users can gradually reveal the solution's letters. Indicators, such as a green, red, orange or yellow colour are used to indicate a letter's true positioning in the triangle. 

Users can also track their overall statistics, with data such as their win-rate%, the entire playerbase's win-rate% and average guesses per win, or even the distribution of guesses per win for themselves.

## Execution
Activate the virtual environment via its respective command:<br/>
```source venv/Scripts/activate```

To run the application you are required to be in the project directory:<br/>
```cd project```

Run the app through the command:<br/>
```flask run```

Stop the app through:<br/>
```^C```

*Additional commands are displayed via the use of the following command:*<br/>
```flask help-p```

The app should execute on localhost:5000, to run it on your local IP address use the following command:<br/>
```flask run --host=0.0.0.0```

## Table of Contents

* [Design](#design)
* [Development of the puzzle](#development)
  * [Back-end](#back-end)
  * [Front-end](#front-end)
* [Build instructions](#build-instructions)
* [Testing instructions](#testing-instructions)
* [Authors](#authors)
* [Acknowledgements](#acknowledgements)


## Design
The application involves a daily word puzzle in which users must uncover three hidden words every day, through the use of strategic word selections. Users ony have a limited amount of letters they can use and they are required to match these to the slots on the game's screen. More info on how to play can be displayed in the HOW TO PLAY section in the top left section of the game.

Users are tracked on the server through two ways, session cookies that locally store a player's unique UserID and in the database, through a specific UserID. Players can load their game data or save data onto another device by copying their UserID and entering it into the prompt in the settings option. This is in the top right of the game screen. Similarly, session variables also tracks a user's current GameID, ensuring that all of the data for a user is valid and up to date.

Submitting a puzzle can end the game in one turn, but any wrong submissions will result in a loss! Be sure to only use Submit All when you're completely sure of your guesses.

## Development
### Back-end
The puzzle's backend was developed via Flask, alongside the usage of tools, such as SQLite (via SQLAlchemy). The website utilises a single page, which sends different requests to the server to grab data, allowing for it to dynamically reload the page as required. Several API calls exist, allowing for statistics to be generated, guesses to be validated, new users, games or puzzles to be generated and so on.

Admins can also use flask commands, which are visible via the `flask help-p` command, to generate puzzles and update puzzles to vet and track future games. Any updated puzzles remove all old game data to ensure the database is consistent with the new puzzle.

### Front-end
The front end was developed with HTML, CSS, JavaScript, Bootstrap and JQuery. The JavaScript is separated into two files (puzzle.js and modal.js). Majority of the puzzle functionality is contained within the puzzle.js file. It contains a series of classes (Puzzle, Word, Slot, Unique Letter, Letter), each of which holds a reference to one or more DOM elements, or a reference to another class object. All puzzle content (with the exception of buttons and modal content) is dynamically added via JavaScript in order to pass DOM references upon object creation and implement fallback pages. Puzzle responsiveness was implemented using a mix of flexboxes, Bootstrap classes, and media queries. Notifications and alerts were created using toasts and modals. This was implemented alongside a minimal UI design and keyboard inputs, to ensure that user has an intuitive, distraction free gaming experience.

## Build instructions
### Prerequisites
Requires [Python 3](https://www.python.org/downloads/) and [SQLite3](http://www.sqlitetutorial.net/download-install-sqlite/) to execute the application.

### Build
Open a terminal inside the directory of the downloaded application files.<br/>
```
cd <files>
```

Install virtualenv if it is not already installed.<br/>
```
pip install virtualenv
```
Create a new virtual environment and activate it.<br/>
```
virtualenv venv
source venv/bin/activate
```
Install the requirements via the requirements.txt.<br/>
```
pip install -r requirements.txt
```
Change the current directory to the project folder:<br/>
```
cd project
```
Initialise the database with the following commands:<br/>
```
flask db init
flask db upgrade
```
Next, populate the database with the word-lists.<br/>
```
flask populate-words
```
<br/>Entering `flask run` will now allow you to run the application.

## Testing instructions
First activate your python virtual environment via its respective command. For example:<br/>
```source venv/Scripts/activate```

To run the unit and system tests you need to be in the project directory:<br/>
```cd project```

Next, within the actual app/\__init__.py file itself, change the line:<br/>
```app.config.from_object(Config)```   to   ```app.config.from_object('config.TestConfig')```

Remember to change this line back when returning to regular use cases.
Next, run the following commands:<br/>
```python -m tests.unit_tests```  to run unit tests.<br/>
```python -m tests.systemtest```  to run system tests.
 
## Authors
* [Sckaeth](https://github.com/Sckaeth)
* [Ophicus](https://github.com/ophixus)
 
## Acknowledgements
* Built with reference to the CITS3403 lectures and the [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) by **Miguel Grinberg**.
* The modal background image by Peter Olexa was obtained via [Unsplash](https://unsplash.com/photos/Ax6ggq8cSxw).
* Fonts and icons obtained via [Google Fonts](https://fonts.google.com/).
* The word-lists for the database were originally from the following respositories ([a](https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b) & [b](https://gist.github.com/cfreshman/cdcdf777450c5b5301e439061d29694c)), which both utilise word-lists extracted from the [Wordle game](https://www.nytimes.com/games/wordle/index.html).

