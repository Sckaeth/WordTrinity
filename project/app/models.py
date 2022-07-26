import datetime
import json
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(32), index=True, unique=True)
    games_won = db.Column(db.Integer, default=0)
    games_lost = db.Column(db.Integer, default=0)
    game_guesses = db.Column(db.Text, default=json.dumps([0]*10))
    games = db.relationship('Game', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.userid)

class Word(db.Model):
    wordid = db.Column(db.Integer, primary_key=True)
    wordname = db.Column(db.String(5), index=True, unique=True)
    firstletter = db.Column(db.String(1), index=True)
    lastletter = db.Column(db.String(1), index=True)
    answer = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Word {}>'.format(self.wordname)

class Puzzle(db.Model):
    puzzleid = db.Column(db.Integer, primary_key=True)
    wordid1 = db.Column(db.Integer, db.ForeignKey('word.wordid'))
    wordid2 = db.Column(db.Integer, db.ForeignKey('word.wordid'))
    wordid3 = db.Column(db.Integer, db.ForeignKey('word.wordid'))
    date = db.Column(db.Date, index=True, unique=True)
    games = db.relationship('Game', backref='puzzle', lazy='dynamic')

    def __repr__(self):
        return '<Puzzle {}>'.format(self.puzzleid)

class Game(db.Model):
    gameid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(32), db.ForeignKey('user.userid'))
    puzzleid = db.Column(db.Integer, db.ForeignKey('puzzle.puzzleid'))
    guesses = db.Column(db.Integer, default=0)
    gpositions = db.Column(db.Text)
    lpositions = db.Column(db.Text, default=json.dumps([0]*12))
    status = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Game {}>'.format(self.gameid)

