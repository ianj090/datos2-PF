from flask import Flask, redirect, g, request, flash, render_template, session
from peewee import * # ORM for Sqlite
from hashlib import md5 # Encoder for password

# Set workspace values / app config
DATABASE = 'profiles.db' # Database name for sqlite3
DEBUG = True # debug flag to print error information
SECRET_KEY = 'EfWpZjEJVD1UOyUCau50lQqzPDzMDZcpun0gB4NuOdw' # Used for cookies / session variables

app = Flask(__name__)
app.config.from_object(__name__) # loads workspace values

# Sqlite connection (using peewee ORM from now on, not Sqlite directly)
# Peewee queries docs: https://docs.peewee-orm.com/en/latest/peewee/querying.html 
database = SqliteDatabase(DATABASE)

# Parent Class containing metadata (in case other classes are used)
class BaseModel(Model):
    class Meta:
        database = database

# Class for users with profiles, contains all values to be displayed
class User(BaseModel):
    username = CharField(unique=True) # primary key
    password = CharField() 
    description = CharField()
    email = CharField()
    firstName = CharField()
    lastName = CharField()
    country = CharField()
    birthday = CharField()
    occupation = CharField()
    mobile_number = CharField()
    phone_number = CharField()

# Creates table in database, ignored if it exists
def create_table():
    with database:
        database.create_tables([User])

# Set Flask session variable, used to record which user is currently signed in
def auth_user(user):
    session['logged_in'] = True
    session['username'] = user.username

# gets the user from the current session
def get_current_user():
    if session.get('logged_in'):
        return User.get(User.username == session['username'])

# Open and close database connection with every request (peewee best practices)
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
    # Submit button calls the same route, handle request.form through POST method.
    if request.method == 'POST':
        # Checks if username exists and if password matches.
        try:
            # Encode password into DB
            pw_hash = md5(request.form['inputPassword'].encode('utf-8')).hexdigest()
            user = User.get(
                (User.username == request.form['inputUsername']) &
                (User.password == pw_hash))
            auth_user(user)
            
            return redirect('/profile') # Returns user's profile

        # If user does not exist then it creates the new user.
        except:
            try:
                with database.atomic(): # Peewee best practice
                    # Create user with empty fields
                    user = User.create(
                        username = request.form['inputUsername'],
                        password = md5((request.form['inputPassword']).encode('utf-8')).hexdigest(),
                        description = "",
                        email = "",
                        firstName = "",
                        lastName = "",
                        country = "",
                        birthday = "",
                        occupation = "",
                        mobile_number = "",
                        phone_number = ""
                    )
                
                auth_user(user)

                return redirect('/profile')

            # If user exists and password does not match, reload the login page and show message.
            except:
                flash("That username is already taken") # Flask method to show messages to user (errors, other feedback)
                return render_template('login.html')
        
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def homepage():
    # if method is post, search for user in DB using form, if method is get use flask session variable
    if request.method == "POST":
        try:
            # Find user in db
            user = User.get(User.username == request.form['searchUsername'])

            # Checks if user is the current session user
            if user.username == session['username']:
                current = True
            else:
                current = False
        except:
            flash("User does not exist")
            return redirect("/profile")
    else:
        user = get_current_user()
        current = True

    return render_template('profile.html',
        username = user.username,
        description = user.description,
        email = user.email,
        firstName = user.firstName,
        lastName = user.lastName,
        country = user.country,
        birthday = user.birthday,
        occupation = user.occupation,
        mobile_number = user.mobile_number,
        phone_number = user.phone_number,
        current = current
    )

# Create / Edit Profile information
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    # Submit button calls itself, if POST, updates user info.
    if request.method == "POST":
        # Finds user and updates info, returns number of rows affected for debugging purposes
        current_user = get_current_user()
        query = User.update(
            email = request.form['editEmail'],
            description = request.form['editDescription'],
            firstName = request.form['editFirstName'],
            lastName = request.form['editLastName'],
            country = request.form['editCountry'],
            birthday = request.form['editBirthday'],
            occupation = request.form['editOccupation'],
            mobile_number = request.form['editMobileNumber'],
            phone_number = request.form['editPhoneNumber']
        ).where(User.username == current_user.username).execute()

        return redirect('/profile')

    user = get_current_user()

    return render_template('editProfile.html',
        # username = user.username,
        description = user.description,
        email = user.email,
        firstName = user.firstName,
        lastName = user.lastName,
        country = user.country,
        birthday = user.birthday,
        occupation = user.occupation,
        mobile_number = user.mobile_number,
        phone_number = user.phone_number
    )


if __name__ == '__main__':
    create_table() # Creates table in DB if it does not exist
    app.run()