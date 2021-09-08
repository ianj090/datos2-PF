from flask import Flask, redirect, g, request, flash, render_template
from peewee import * # ORM for Sqlite
from hashlib import md5 # Encoder for password
import memcache # Cache
import requests # api calls
import os # random string method
import random

# Set workspace values / app config
DATABASE = 'profiles.db' # Database name for sqlite3
DEBUG = True # debug flag to print error information
SECRET_KEY = os.urandom(12) # Used for cookies / session variables

app = Flask(__name__)
app.config.from_object(__name__) # loads workspace values

# Sqlite connection (using peewee ORM from now on, not Sqlite directly)
# Peewee queries docs: https://docs.peewee-orm.com/en/latest/peewee/querying.html 
database = SqliteDatabase(DATABASE)

# Start cache connection
client = memcache.Client([('127.0.0.1', 11211)])
cacheTime = 60

global session 
session = {'logged_in':False, 'username':''}

# Parent Class containing metadata (in case other classes are used)
class BaseModel(Model):
    class Meta:
        database = database

# Class for users with profiles, contains all values to be displayed
class User(BaseModel):
    username = CharField(unique=True) # primary key
    password = CharField() 
    profilepic = CharField()
    mood = CharField()
    description = CharField()
    email = CharField()
    firstName = CharField()
    lastName = CharField()
    country = CharField()
    birthday = CharField()
    occupation = CharField()
    relationship_status = CharField()
    mobile_number = CharField()
    phone_number = CharField()
    my_journal = CharField()
    bg = CharField()

# Creates table in database, ignored if it exists
def create_table():
    with database:
        database.create_tables([User])

# Set session variable, used to record which user is currently signed in
def auth_user(user):
    session['logged_in'] = True
    session['username'] = user.username

# gets the user from the current session
def get_current_user():
    if session['logged_in']:
        return User.get(User.username == session['username'])
    else:
        raise RuntimeError

def cache_user(user):
    client.set("current_user", user, time=cacheTime)

# Api tokens: G5O5mE74Ey3YNnbNYMlgeg / 6tu2dks70riHqBKPIrDtTA / 4zI_9ibRnO_U3sUGrBj1fw / RM3JTB7Fz4BcLbEKvGilfQ	/ 0S-48tYujOzkcOUSLjJ3nQ / x4WffQ8A0BaqJ2X-gje7Ig
def generate_users():
    body = {
        # 'token': 'x4WffQ8A0BaqJ2X-gje7Ig',
        'data': {
            'username': 'name',
            'password': 'personPassword',
            'profilepic': 'personAvatar',
            'mood': "Relaxed", # default mood is 'Relaxed'
            'description': 'stringShort',
            'email': 'internetEmail',
            'firstName': 'nameFirst',
            'lastName': 'nameLast',
            'country': 'addressCountry',
            'birthday': 'dateDOB',
            'occupation': 'personTitle',
            'relationship_status': 'personMaritalStatus',
            'mobile_number': 'phoneMobile',
            'phone_number': 'phoneHome',
            'my_journal' : 'stringLong',
            'bg': 'colorHEX',
            '_repeat': 2 # Max for free tier of api plan
        }
    }

    r = requests.post('https://app.fakejson.com/q', json = body)
    return r

def create_user(user):
    with database.atomic(): # Peewee best practice
        test = User.create(
            username = ''.join(random.sample(user['username'], len(user['username']))),
            password = md5((user['password']).encode('utf-8')).hexdigest(),
            profilepic = user['profilepic'],
            mood = user['mood'],
            description = user['description'],
            email = user['email'],
            firstName = user['firstName'],
            lastName = user['lastName'],
            country = user['country'],
            birthday = user['birthday'],
            occupation = user['occupation'],
            relationship_status = user['relationship_status'],
            mobile_number = user['mobile_number'],
            phone_number = user['phone_number'],
            my_journal = user['my_journal'],
            bg = user['bg']
        )

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
            cache_user(user)
            
            return redirect('/profile') # Returns user's profile

        # If user does not exist then it creates the new user.
        except:
            try:
                with database.atomic(): # Peewee best practice
                    # Create user with empty fields
                    user = User.create(
                        username = request.form['inputUsername'],
                        password = md5((request.form['inputPassword']).encode('utf-8')).hexdigest(),
                        profilepic = "https://d3ipks40p8ekbx.cloudfront.net/dam/jcr:3a4e5787-d665-4331-bfa2-76dd0c006c1b/user_icon.png",
                        mood = "Relaxed",
                        description = "",
                        email = "",
                        firstName = "",
                        lastName = "",
                        country = "",
                        birthday = "",
                        occupation = "",
                        relationship_status = "",
                        mobile_number = "",
                        phone_number = "",
                        my_journal = "",
                        bg = "#f1f2f7"
                    )
                auth_user(user)
                cache_user(user)


                return redirect('/profile')

            # If user exists and password does not match, reload the login page and show message.
            except:
                flash("That username is already taken") # Flask method to show messages to user (errors, other feedback)
                return render_template('login.html')
        
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def homepage():
    # if method is post, search for user in DB using form, if method is get use session variable
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
        # Checks if user exists
        try:
            user = client.get("current_user")
            if user == None:
                user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        current = True

    return render_template('profile.html',
        username = user.username,
        profilepic = user.profilepic,
        mood = user.mood,
        description = user.description,
        email = user.email,
        firstName = user.firstName,
        lastName = user.lastName,
        country = user.country,
        birthday = user.birthday,
        occupation = user.occupation,
        relationship_status = user.relationship_status,
        mobile_number = user.mobile_number,
        phone_number = user.phone_number,
        my_journal = user.my_journal,
        bg = user.bg,
        current = current
    )

# Create / Edit Profile information
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    # Submit button calls itself, if POST, updates user info.
    if request.method == "POST":
        # Finds user and updates info, returns number of rows affected for debugging purposes
        try:
            current_user = client.get("current_user")
            if current_user == None:
                current_user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        if (request.form['editProfilePic'] != ""):
            query = User.update(
                profilepic = request.form['editProfilePic'],
                mood = request.form['editMood'],
                email = request.form['editEmail'],
                description = request.form['editDescription'],
                firstName = request.form['editFirstName'],
                lastName = request.form['editLastName'],
                country = request.form['editCountry'],
                birthday = request.form['editBirthday'],
                occupation = request.form['editOccupation'],
                relationship_status = request.form['editRelationship_status'],
                mobile_number = request.form['editMobileNumber'],
                phone_number = request.form['editPhoneNumber'],
                my_journal = request.form['editJournal']
            ).where(User.username == current_user.username).execute()
        else:
           query = User.update(
                mood = request.form['editMood'],
                email = request.form['editEmail'],
                description = request.form['editDescription'],
                firstName = request.form['editFirstName'],
                lastName = request.form['editLastName'],
                country = request.form['editCountry'],
                birthday = request.form['editBirthday'],
                occupation = request.form['editOccupation'],
                relationship_status = request.form['editRelationship_status'],
                mobile_number = request.form['editMobileNumber'],
                phone_number = request.form['editPhoneNumber'],
                my_journal = request.form['editJournal']
            ).where(User.username == current_user.username).execute() 

        # Replace cached user with new data
        try:
            user = get_current_user()
            cached_user = client.get("current_user") 
            if cached_user == None:
                cache_user(user)
            else:
                client.replace("current_user", user, time=cacheTime)
        except:
            pass

        return redirect('/profile')

    # Checks if user exists
    try:
        user = client.get("current_user")
        if user == None:
            user = get_current_user()
            print("from DB")
    except:
        return redirect('/login')

    return render_template('editProfile.html',
        # username = user.username,
        profilepic = user.profilepic,
        mood = user.mood,
        description = user.description,
        email = user.email,
        firstName = user.firstName,
        lastName = user.lastName,
        country = user.country,
        birthday = user.birthday,
        occupation = user.occupation,
        relationship_status = user.relationship_status,
        mobile_number = user.mobile_number,
        phone_number = user.phone_number,
        my_journal = user.my_journal
    )
# To Just change the background of the profile
@app.route('/editbg', methods=['GET', 'POST'])
def editbg():
    # Submit button calls itself, if POST, updates user info.
    if request.method == "POST":
        # Finds user and updates info, returns number of rows affected for debugging purposes
        try:
            current_user = client.get("current_user")
            if current_user == None:
                current_user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        query = User.update(
            bg = request.form['editBgprofile'],
        ).where(User.username == current_user.username).execute()
        
        # Replace cached user with new data
        try:
            user = get_current_user()
            cached_user = client.get("current_user") 
            if cached_user == None:
                cache_user(user)
            else:
                client.replace("current_user", user, time=cacheTime)
        except:
            pass

        return redirect('/profile')

    # Checks if user exists
    try:
        user = client.get("current_user")
        if user == None:
            user = get_current_user()
            print("from DB")
    except:
        return redirect('/login')

    return render_template('editBackground.html',
        bg = user.bg
    )


@app.route('/delete')
def delete():
    # If user session does not exist, go to login.
    try:
        user = client.get("current_user")
        if user == None:
            user = get_current_user()
            print("from DB")
    except:
        return redirect('/login')
    
    # If user does not exist in table, go back to profile
    try:
        user.delete_instance()
        session['logged_in'] = False
        session['username'] = ''
    except:
        flash('Could not remove user')
        return redirect('/profile')

    # If all passes go to login.
    flash("Deleted user")
    return redirect('/login')


if __name__ == '__main__':
    create_table() # Creates table in DB if it does not exist
    try:
        data = generate_users().json() # Creates random users to populate DB through api
        for user in data:
            print("user", user)
            create_user(user)
    except:
        print("api limit reached")
        pass
    app.run()