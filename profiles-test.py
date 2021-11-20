from flask import Flask, redirect, request, flash, render_template # All relevant Flask imports
from hashlib import md5 # Encoder for password
import memcache # Cache
from os import urandom # random string method for Flask
from elasticsearch import Elasticsearch # New DB
import flask_profiler # Profiler for Flask apps, does not work with ES
from kafka import KafkaProducer # Kafka Server
import json # used for kafka loading
from time import sleep # used to handle async logstash
import mysql.connector as mysql # used for connecting to MySQL

# Set workspace values / app config
DEBUG = True # debug flag to print error information, must be true for profiler
TESTING = True
SECRET_KEY = urandom(12) # Used for Flask cookies / session variables

app = Flask(__name__) # loads as Flask
app.config.from_object(__name__) # loads workspace values

es = Elasticsearch([{'host': '127.0.0.1', 'port': 9200}]) # Connects to ES DB.

# Start cache connection
client = memcache.Client([('127.0.0.1', 11211)])
cacheTime = 60 # In seconds, how long an item stays in cache

# Start Kafka Server Vars and clients
TOPIC_NAME = "users" # topic is similar to channel name, says what topic it should send to, logstash listens to the same topic
KAFKA_SERVER = "127.0.0.1:9092"

# Set Kafka Producer, sends to logstash
producer = KafkaProducer(
    bootstrap_servers = KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8') # Formatted as JSON
)

# Connect to MySQL Database
db = mysql.connect(
    host = "localhost",
    user = "admin", # Defined when downloading MySQL
    passwd = "Datos2-Password123", # Defined when downloading MySQL
    database = "profiles", # Comment out if db not created yet
    autocommit = True # Used to handle logstash async
)
cursor = db.cursor(dictionary=True, buffered=True) # cursor is used to create queries and read returns, sets return as a dict and buffered is required for logstash async handling

# Create database, not needed if already created
# cursor.execute("CREATE DATABASE profiles")

# cursor.execute("SHOW DATABASES") # Lists all dbs, some are created on setup, only use our db created above
# databases = cursor.fetchall()
# print(databases)

# Create table, not needed if already created
# cursor.execute("""
# CREATE TABLE users(
#     username VARCHAR(250) PRIMARY KEY,
#     password VARCHAR(250),
#     profilepic VARCHAR(250),
#     mood VARCHAR(250),
#     description VARCHAR(250),
#     email VARCHAR(250),
#     firstName VARCHAR(250),
#     lastName VARCHAR(250),
#     country VARCHAR(250),
#     birthday VARCHAR(250),
#     occupation VARCHAR(250),
#     relationship_status VARCHAR(250),
#     mobile_number VARCHAR(250),
#     phone_number VARCHAR(250),
#     my_journal VARCHAR(1000),
#     bg VARCHAR(250)
# )
# """) # We pass all vars as strings since they won't be mutated here anyway

# cursor.execute("SHOW TABLES") # Shows all tables in our db
# tables = cursor.fetchall()
# print(tables)

# Set our global variables
global cache
cache = True # Used to enable or disable cache (for jmeter or debugging)

global session
session = {'logged_in':False, 'username':''} # Stores logged-in user.

# Method to delete all instances in ElasticSearch for debugging
# es.delete_by_query(index="logstash", body={"query": {"match_all": {}}})
# cursor.execute("DELETE FROM users")
# db.commit()

# Set session variable, used to record which user is currently signed in
def auth_user(username):
    session['logged_in'] = True
    session['username'] = username

# gets the user from the current session
def get_current_user(useCache = True):
    if session['logged_in']:
        try:
        # res = es.search(index="logstash", query={"match_all": {}}) # Method to find all users
            try:
                # First try to find in ES, if not available then uses MySQL and Cache
                user = None
                count = 0
                while user is None:
                    if count != 0:
                        sleep(0.1)
                    res = es.search(index="logstash", query={"term": {"username.keyword": {"value": session['username']}}}) # Method to find user by username in DB
                    for hit in res["hits"]["hits"]: # Required for json return format
                        user = hit["_source"]
                    count += 1
                    if count >= 50:
                        break
                print(count)
                if user is None:
                    raise RuntimeError
                print("From ES")
            except:
                # First check cache and if not then MySQL
                if cache == True and useCache == True:
                    user = client.get("current_user")
                    print("From Cache")
                else:
                    user = None
                if user == None:
                    count = 0
                    while user is None or user == []:
                        if count != 0:
                            sleep(0.1)
                        cursor.execute("SELECT * FROM users where username=%s", (session["username"],))
                        user = cursor.fetchall()
                        user = user[0]
                        count += 1
                        if count >= 50:
                            break
                    print("From MySQL")
        except:
            raise RuntimeError

        if not user or user == []: # Request still returns but empty if not found so we force an error (try, except handling)
            raise RuntimeError
        
        return user # user is a dict, a user_obj
    else:
        raise RuntimeError

def deleteUser():
    # Deletes from both DBs and Cache
    try: 
        res = es.delete_by_query(index="logstash", refresh = 'true', body={"query": {"term": {"username.keyword": {"value": session['username']}}}}) # deletes user from ES
    except: pass
    try:
        cursor.execute("DELETE FROM users WHERE username=%s", (session["username"],)) # deletes user from MySQL
        rows_affected = cursor.rowcount
        if rows_affected != 1:
            db.commit()
    except: pass
    if cache == True:
        try: client.delete("current_user") # attempts to clear cache if still up
        except: pass

def cache_user(user): # Caches user with specific lifetime
    if cache == True:
        client.set("current_user", user, time=cacheTime)

# Redirects to '/login' path
@app.route('/')
def initial():
    return redirect('/login')

# Start page for new connection, sign in with username and password (if user does not exists it gets created) and goes to '/profile' path through html form.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if cache == True:
        try: client.delete("current_user") # attempts to clear cache before anything, used to clear cache when user gets deleted and to handle logged in errors
        except: pass
    session['logged_in'] = False 
    session['username'] = ''

    # Submit button calls the same route, handle request.form through POST method.
    if request.method == 'POST':
        # Checks if username exists.
        try:
            # First try from ES, if ES is down then goes to MySQL, no cache exists yet
            try:
                res = es.search(index="logstash", query={"term": {"username.keyword": {"value": request.form['inputUsername']}}})
                for hit in res["hits"]["hits"]:
                    user = hit["_source"]
                password = user["password"]
                print("From ES")
            except:
                cursor.execute("SELECT * FROM users where username=%s", (request.form['inputUsername'],))
                user = cursor.fetchall()
                user = user[0]
                if user is None: raise RuntimeError # Small startup handler
                print("From MySQL")
                password = user["password"]

            pw_hash = md5(request.form['inputPassword'].encode('utf-8')).hexdigest()

            if password == pw_hash: # If password matches go to profile
                auth_user(request.form['inputUsername'])
                cache_user(user) # Adds user to cache

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

                try: 
                    producer.send(TOPIC_NAME, user_obj)
                    producer.flush()
                except Exception:
                    flash("DB or Cache Error") # Flask method to show messages to user (errors, other feedback)
                    return render_template('login.html')

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
            try:
                # Find user in DB
                res = es.search(index="logstash", query={"term": {"username.keyword": {"value": request.form['searchUsername']}}})

                for hit in res["hits"]["hits"]:
                    user = hit["_source"]
                if user is None: raise RuntimeError
                print("From ES")
            except:
                cursor.execute("SELECT * FROM users where username=%s", (request.form['searchUsername'],)) # if ES fails check MySQL
                user = cursor.fetchall()
                user = user[0]
                print(request.form['searchUsername'])
                print(user)
                if user is None: raise RuntimeError
            username = user['username'] # Simple handler, fails if it can't parse

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
            user = get_current_user()
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
            current_user = get_current_user(False)
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
        current_user.update(user_obj)

        deleteUser()
        producer.send(TOPIC_NAME, current_user)
        producer.flush()

        cache_user(current_user)

        return redirect('/profile')

    # Checks if user exists
    try:
        user = get_current_user()
    except:
        return redirect('/login')

    return render_template('editProfile.html',
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
            current_user = get_current_user(False)
        except:
            return redirect('/login')

        user_obj = {
            "bg": request.form['editBgprofile']
        }
        current_user.update(user_obj)

        deleteUser()
        producer.send(TOPIC_NAME, current_user)
        producer.flush()

        cache_user(current_user)

        return redirect('/profile')

    # Checks if user exists
    try:
        user = get_current_user()
    except:
        return redirect('/login')

    return render_template('editBackground.html',
        bg = user["bg"]
    )

@app.route('/delete')
def delete():
    # If user session does not exist, go to login.
    if session["username"] == '':
        return redirect('/login')
    
    # If user does not exist in table, go back to profile
    try:
        deleteUser()
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
        "engine": "sqlite" # Profiler requires an engine, elasticsearch is not supported but sqlite offers similar functionality
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
# flask_profiler.init_app(app) # Disabled for production, can cause some errors due to incorrect engine

if __name__ == '__main__':
    # create_table() # Creates table in DB if it does not exist
    app.run()
