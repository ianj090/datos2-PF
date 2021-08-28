from flask import Flask, redirect, g, request, flash, render_template
from peewee import * # ORM for Sqlite
from hashlib import md5 # Encoder for password

# Set workspace values
DATABASE = 'profiles.db'
DEBUG = True
SECRET_KEY = 'EfWpZjEJVD1UOyUCau50lQqzPDzMDZcpun0gB4NuOdw'

app = Flask(__name__)
app.config.from_object(__name__)

# Sqlite connection (using peewee ORM from now on, not Sqlite directly)
database = SqliteDatabase(DATABASE)

# Parent Class containing metadata (in case other classes are used)
class BaseModel(Model):
    class Meta:
        database = database

# Class for users with profiles, contains all value to be displayed
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField()

# Creates table in database
def create_table():
    with database:
        database.create_tables([User])

# Open and close database connection with every request
@app.before_request
def before_request():
    g.db = database
    g.db.connect()

@app.after_request
def after_request(response):
    g.db.close()
    return response

# Redirects to '/login' path
@app.route('/')
def initial():
    return redirect('/login')

# Start page for new connection, sign in with username and password (if user does not exists it gets created) and goes to '/profile' path through html form.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Checks if username exists and if password matches.
        try:
            pw_hash = md5(request.form['inputPassword'].encode('utf-8')).hexdigest()
            user = User.get(
                (User.username == request.form['inputUsername']) &
                (User.password == pw_hash))
            return redirect('/profile')

        # If user does not exist then it creates the new user.
        except:
            try:
                with database.atomic():
                    user = User.create(
                        username = request.form['inputUsername'],
                        password = md5((request.form['inputPassword']).encode('utf-8')).hexdigest(),
                        email = ""
                    )
                return redirect('/profile')

            # If user exists and password does not match, reload the login page.
            except:
                flash("That username is already taken")
                return render_template('login.html')
        
    return render_template('login.html')

@app.route('/profile')
def homepage():
    
    return render_template('profile.html')

# Create / Edit Profile information
@app.route('/create')
def create():
    return render_template('createProfile.html')


if __name__ == '__main__':
    create_table()
    app.run()