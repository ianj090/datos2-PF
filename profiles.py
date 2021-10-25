from flask import Flask, redirect, request, flash, render_template #, g
from hashlib import md5 # Encoder for password
import memcache # Cache
from os import urandom # random string method
import flask_profiler 
# from peewee import * # ORM for Sqlite
# import requests # api calls
# import random

from elasticsearch import Elasticsearch # New DB

# Set workspace values / app config
# DATABASE = 'profiles.db' # Database name for sqlite3
DEBUG = True # debug flag to print error information
SECRET_KEY = urandom(12) # Used for cookies / session variables

app = Flask(__name__)
app.config.from_object(__name__) # loads workspace values

# Sqlite connection (using peewee ORM from now on, not Sqlite directly)
# Peewee queries docs: https://docs.peewee-orm.com/en/latest/peewee/querying.html
# database = SqliteDatabase(DATABASE)

es = Elasticsearch([{'host': '127.0.0.1', 'port': 9200}]) # Connects to ES DB.

# Start cache connection
client = memcache.Client([('127.0.0.1', 11211)])
cacheTime = 60 # In seconds, how long an item stays in cache

global session 
session = {'logged_in':False, 'username':''} # Stores logged-in user.

# Method to delete all instances in ElasticSearch if DB error
# es.delete_by_query(index="user", body={"query": {"match_all": {}}})

# Set session variable, used to record which user is currently signed in
def auth_user(username):
    session['logged_in'] = True
    session['username'] = username

# gets the user from the current session
def get_current_user():
    if session['logged_in']:
        res = es.search(index="user", query={"term": {"username.keyword": {"value": session['username']}}}) # Method to find user by username in DB

        for hit in res["hits"]["hits"]: # Required for json return format
            user = hit["_source"]
        
        if not user: # Request still returns but empty if not found so we force an error (try, except handling)
            raise RuntimeError

        return user
    else:
        raise RuntimeError

def cache_user(user): # Caches user with specific lifetime
    client.set("current_user", user, time=cacheTime)

# Redirects to '/login' path
@app.route('/')
def initial():
    return redirect('/login')

# Start page for new connection, sign in with username and password (if user does not exists it gets created) and goes to '/profile' path through html form.
@app.route('/login', methods=['GET', 'POST'])
def login():
    try: client.delete("current_user") # attempts to clear cache before anything, used to clear cache when user gets deleted and to handle logged in errors
    except: pass

    # Submit button calls the same route, handle request.form through POST method.
    if request.method == 'POST':
        # Checks if username exists.
        try:
            res = es.search(index="user", query={"term": {"username.keyword": {"value": request.form['inputUsername']}}})
            
            pw_hash = md5(request.form['inputPassword'].encode('utf-8')).hexdigest()

            for hit in res["hits"]["hits"]:
                password = hit["_source"]["password"]

            if password == pw_hash: # If password matches go to profile
                auth_user(request.form['inputUsername'])

                return redirect('/profile') # Returns user's profile
                
            else: # If password doesn't match reload with message
                flash("That username is already taken") # Flask method to show messages to user (errors, other feedback)
                return render_template('login.html')

        # If user does not exist then it creates the new user.
        except:
            try:
                # Create user with empty fields
                user_obj = {
                    'username': request.form['inputUsername'],
                    'password': md5((request.form['inputPassword']).encode('utf-8')).hexdigest(),
                    'profilepic': "https://d3ipks40p8ekbx.cloudfront.net/dam/jcr:3a4e5787-d665-4331-bfa2-76dd0c006c1b/user_icon.png",
                    'mood': "Relaxed",
                    'description': "",
                    'email': "",
                    'firstName': "",
                    'lastName': "",
                    'country': "",
                    'birthday': "",
                    'occupation': "",
                    'relationship_status': "",
                    'mobile_number': "",
                    'phone_number': "",
                    'my_journal': "",
                    'bg': "#f1f2f7"
                }
                result = es.index(index = "user", id = user_obj["username"], document = user_obj)
                print(result) # Adds user to DB

                auth_user(user_obj["username"]) # Changes session variable values
                cache_user(user_obj) # Adds user to cache

                return redirect('/profile')

            # If user doesn't exist and can't add a new user.
            except:
                flash("DB or Cache Error") # Flask method to show messages to user (errors, other feedback)
                return render_template('login.html')
        
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def homepage():
    # if method is POST, search for user in DB using form, if method is GET use session variable
    if request.method == "POST":
        try:
            # Find user in DB
            res = es.search(index="user", query={"term": {"username.keyword": {"value": request.form['searchUsername']}}})

            for hit in res["hits"]["hits"]:
                user = hit["_source"]
            
            if not user:
                raise RuntimeError

            # Checks if user is the current session user
            if request.form['searchUsername'] == session['username']:
                current = True # Variable which handles permissions (edit or delete user, if user is not current then these are not allowed)
            else:
                current = False
        except:
            flash("User does not exist")
            return redirect("/profile")
    else:
        # Checks if user exists
        try:
            user = client.get("current_user") # Attempts to get from Cache
            print(user)
            if user == None: # If not in cache from DB
                user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        current = True

    return render_template('profile.html',
        username = user["username"],
        profilepic = user["profilepic"],
        mood = user["mood"],
        description = user["description"],
        email = user["email"],
        firstName = user["firstName"],
        lastName = user["lastName"],
        country = user["country"],
        birthday = user["birthday"],
        occupation = user["occupation"],
        relationship_status = user["relationship_status"],
        mobile_number = user["mobile_number"],
        phone_number = user["phone_number"],
        my_journal = user["my_journal"],
        bg = user["bg"],
        current = current
    )

# Create / Edit Profile information
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    # Submit button calls itself, if POST, updates user info.
    if request.method == "POST":
        # Tries to find user in cache or DB
        try:
            current_user = client.get("current_user")
            if current_user == None:
                current_user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        if (request.form['editProfilePic'] != ""):
            user_obj = {
                "profilepic": request.form['editProfilePic'],
                "mood": request.form['editMood'],
                "email": request.form['editEmail'],
                "description": request.form['editDescription'],
                "firstName": request.form['editFirstName'],
                "lastName": request.form['editLastName'],
                "country": request.form['editCountry'],
                "birthday": request.form['editBirthday'],
                "occupation": request.form['editOccupation'],
                "relationship_status": request.form['editRelationship_status'],
                "mobile_number": request.form['editMobileNumber'],
                "phone_number": request.form['editPhoneNumber'],
                "my_journal": request.form['editJournal']
            }
            es.update(index = "user", id = session["username"], body = {"doc": user_obj}) # Updates DB with new user info
        else:
            user_obj = {
                "mood": request.form['editMood'],
                "email": request.form['editEmail'],
                "description": request.form['editDescription'],
                "firstName": request.form['editFirstName'],
                "lastName": request.form['editLastName'],
                "country": request.form['editCountry'],
                "birthday": request.form['editBirthday'],
                "occupation": request.form['editOccupation'],
                "relationship_status": request.form['editRelationship_status'],
                "mobile_number": request.form['editMobileNumber'],
                "phone_number": request.form['editPhoneNumber'],
                "my_journal": request.form['editJournal']
            }
            es.update(index = "user", id = session["username"], body = {"doc": user_obj}) # Updates DB with new user info

        # Replace cached user with new data
        try:
            user = get_current_user()
            cache_user(user)
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
        # username = user["username"],
        profilepic = user["profilepic"],
        mood = user["mood"],
        description = user["description"],
        email = user["email"],
        firstName = user["firstName"],
        lastName = user["lastName"],
        country = user["country"],
        birthday = user["birthday"],
        occupation = user["occupation"],
        relationship_status = user["relationship_status"],
        mobile_number = user["mobile_number"],
        phone_number = user["phone_number"],
        my_journal = user["my_journal"]
    )

# To Just change the background of the profile
@app.route('/editbg', methods=['GET', 'POST'])
def editbg():
    # Submit button calls itself, if POST, updates user info.
    if request.method == "POST":
        # Tries to find user in cache or db.
        try:
            current_user = client.get("current_user")
            if current_user == None:
                current_user = get_current_user()
                print("from DB")
        except:
            return redirect('/login')

        user_obj = {
            "bg": request.form['editBgprofile']
        }
        es.update(index = "user", id = session["username"], body = {"doc": user_obj}) # Updates user in DB
        
        # Replace cached user with new data
        try:
            user = get_current_user()
            cache_user(user)
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
        bg = user["bg"]
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
        res = es.delete_by_query(index="user", body={"query": {"term": {"username.keyword": {"value": session['username']}}}}) # deletes user from DB
        session['logged_in'] = False # Resets session values
        session['username'] = ''
    except:
        flash('Could not remove user') # error handler
        return redirect('/profile')

    # If all passes go to login.
    flash("User deleted")
    return redirect('/login')

# Configurations for profiler
app.config["flask_profiler"] = {
    "enabled": app.config["DEBUG"],
    "storage": {
        "engine": "sqlite" # Profiler requires an engine but it doesn't affect measurements
    },
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
	    "^/static/.*"
	]
}

# Starts profiler in http://127.0.0.1:5000/flask-profiler/ 
# username and password = "admin"
flask_profiler.init_app(app)

if __name__ == '__main__':
    # create_table() # Creates table in DB if it does not exist
    # try:
    #     data = generate_users().json() # Creates random users to populate DB through api
    #     for user in data:
    #         print("user", user)
    #         create_user(user)
    # except:
    #     print("api limit reached")
    #     pass
    app.run()


# Sqlite classes and methods no longer in use

# Parent Class containing metadata (in case other classes are used)
# class BaseModel(Model):
#     class Meta:
#         database = database

# # Class for users with profiles, contains all values to be displayed
# class User(BaseModel):
#     username = CharField(unique=True) # primary key
#     password = CharField() 
#     profilepic = CharField()
#     mood = CharField()
#     description = CharField()
#     email = CharField()
#     firstName = CharField()
#     lastName = CharField()
#     country = CharField()
#     birthday = CharField()
#     occupation = CharField()
#     relationship_status = CharField()
#     mobile_number = CharField()
#     phone_number = CharField()
#     my_journal = CharField()
#     bg = CharField()

# # Creates table in database, ignored if it exists
# def create_table():
#     with database:
#         database.create_tables([User])


# # Api tokens: G5O5mE74Ey3YNnbNYMlgeg / 6tu2dks70riHqBKPIrDtTA / 4zI_9ibRnO_U3sUGrBj1fw / RM3JTB7Fz4BcLbEKvGilfQ	/ 0S-48tYujOzkcOUSLjJ3nQ / x4WffQ8A0BaqJ2X-gje7Ig
# def generate_users():
#     body = {
#         # 'token': 'x4WffQ8A0BaqJ2X-gje7Ig',
#         'data': {
#             'username': 'name',
#             'password': 'personPassword',
#             'profilepic': 'personAvatar',
#             'mood': "Relaxed", # default mood is 'Relaxed'
#             'description': 'stringShort',
#             'email': 'internetEmail',
#             'firstName': 'nameFirst',
#             'lastName': 'nameLast',
#             'country': 'addressCountry',
#             'birthday': 'dateDOB',
#             'occupation': 'personTitle',
#             'relationship_status': 'personMaritalStatus',
#             'mobile_number': 'phoneMobile',
#             'phone_number': 'phoneHome',
#             'my_journal' : 'stringLong',
#             'bg': 'colorHEX',
#             '_repeat': 2 # Max for free tier of api plan
#         }
#     }

#     r = requests.post('https://app.fakejson.com/q', json = body)
#     return r

# def create_user(user):
#     with database.atomic(): # Peewee best practice
#         test = User.create(
#             username = ''.join(random.sample(user['username'], len(user['username']))),
#             password = md5((user['password']).encode('utf-8')).hexdigest(),
#             profilepic = user['profilepic'],
#             mood = user['mood'],
#             description = user['description'],
#             email = user['email'],
#             firstName = user['firstName'],
#             lastName = user['lastName'],
#             country = user['country'],
#             birthday = user['birthday'],
#             occupation = user['occupation'],
#             relationship_status = user['relationship_status'],
#             mobile_number = user['mobile_number'],
#             phone_number = user['phone_number'],
#             my_journal = user['my_journal'],
#             bg = user['bg']
#         )

# # Open and close database connection with every request (peewee best practices)
# @app.before_request
# def before_request():
#     g.db = database
#     g.db.connect()

# @app.after_request
# def after_request(response):
#     g.db.close()
#     return response