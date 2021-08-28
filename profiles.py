from flask import Flask, redirect
from flask.templating import render_template
from peewee import *

DATABASE = 'profiles.db'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

database = SqliteDatabase(DATABASE)

class BaseModel(Model):
    class Meta:
        database = database

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField()
    join_date = DateTimeField()

def create_table():
    with database:
        database.create_tables(User)

@app.route('/')
def initial():
    return redirect('/login')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/create')
def create():
    return render_template('createProfile.html')

@app.route('/profile')
def homepage():
    return render_template('profile.html')



if __name__ == '__main__':
    app.run()