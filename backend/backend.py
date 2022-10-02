from flask import Flask, redirect, g, request, flash, render_template
import pymongo
from hashlib import md5 # Encoder for password
# import os # random string method

# Set workspace values / app config
DATABASE = 'profiles.db' # Database name for sqlite3
DEBUG = True # debug flag to print error information

app = Flask(__name__)
app.config.from_object(__name__) # loads workspace values

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["flask_db"]
users = db["users"]

global session 
session = {'logged_in':False, 'username':''}

# Set session variable, used to record which user is currently signed in
def auth_user(user):
    session['logged_in'] = True
    session['username'] = user["username"]

# gets the user from the current session
def get_current_user():
    if session['logged_in']:
        return users.find_one({'username': session['username']})
    else:
        raise RuntimeError

#### From route /
def reset_session():
    session['logged_in'] = False
    session['username'] = ''

@app.route('/reset_session/')
def reset():
    reset_session()
    return 'SUCCESS'

# Redirects to '/login' path
@app.route('/login', methods=["POST"])
def login():
    reset_session()
    payload = request.json
    if payload["method"] == "POST":
        try:
            try:
                pw_hash = md5(payload["data"]['inputPassword'].encode('utf-8')).hexdigest()
                user = users.find_one({'username': payload["data"]['inputUsername'], 'password': pw_hash})
                auth_user(user)
                return 'PROFILE'
            except:
                try:
                    user_dict = {
                        "username": payload["data"]['inputUsername'],
                        "password": md5((payload["data"]['inputPassword']).encode('utf-8')).hexdigest(),
                        "profilepic": "https://d3ipks40p8ekbx.cloudfront.net/dam/jcr:3a4e5787-d665-4331-bfa2-76dd0c006c1b/user_icon.png",
                        "mood": "Relaxed",
                        "description": "",
                        "email": "",
                        "firstName": "",
                        "lastName": "",
                        "country": "",
                        "birthday": "",
                        "occupation": "",
                        "relationship_status": "",
                        "mobile_number": "",
                        "phone_number": "",
                        "my_journal": "",
                        "bg": "#f1f2f7"
                    }
                    users.insert_one(user_dict)
                    auth_user(user_dict)
                    return 'PROFILE'
                except:
                    return 'TAKEN'
        except:
            return 'FAILURE'
    return 'LOGIN'

@app.route('/profile', methods=["POST"])
def homepage():
    payload = request.json
    user = users.find_one({'username': payload["data"]["searchUsername"]})
    del user['_id']
    # Checks if user is the current session user
    if user["username"] == session['username']:
        current = True
    else:
        current = False
    user["current"] = current
    return user

@app.route('/currentUser')
def currentUser():
    try:
        user = get_current_user()
        del user['_id']
        return user
    except:
        return 'FAILURE'

@app.route('/edit', methods=['POST'])
def edit():
    payload = request.json
    current_user = get_current_user()
    if (payload["data"]['editProfilePic'] != ""):
        users.update_one({'username': current_user["username"]}, {"$set": {
            "profilepic": payload["data"]['editProfilePic'],
            "mood": payload["data"]['editMood'],
            "email": payload["data"]['editEmail'],
            "description": payload["data"]['editDescription'],
            "firstName": payload["data"]['editFirstName'],
            "lastName": payload["data"]['editLastName'],
            "country": payload["data"]['editCountry'],
            "birthday": payload["data"]['editBirthday'],
            "occupation": payload["data"]['editOccupation'],
            "relationship_status": payload["data"]['editRelationship_status'],
            "mobile_number": payload["data"]['editMobileNumber'],
            "phone_number": payload["data"]['editPhoneNumber'],
            "my_journal": payload["data"]['editJournal']
        }})
    else:
        users.update_one({'username': current_user["username"]}, {"$set": {
            "mood": payload["data"]['editMood'],
            "email": payload["data"]['editEmail'],
            "description": payload["data"]['editDescription'],
            "firstName": payload["data"]['editFirstName'],
            "lastName": payload["data"]['editLastName'],
            "country": payload["data"]['editCountry'],
            "birthday": payload["data"]['editBirthday'],
            "occupation": payload["data"]['editOccupation'],
            "relationship_status": payload["data"]['editRelationship_status'],
            "mobile_number": payload["data"]['editMobileNumber'],
            "phone_number": payload["data"]['editPhoneNumber'],
            "my_journal": payload["data"]['editJournal']
        }})
    return "SUCCESS"

@app.route('/editbg', methods=['POST'])
def editbg():
    payload = request.json
    current_user = get_current_user()
    users.update_one({'username': current_user["username"]}, {"$set": {
        "bg": payload["data"]['editBgprofile']
    }})
    return "SUCCESS"
    

@app.route('/delete')
def delete():
    users.delete_one({'username': session["username"]})
    session['logged_in'] = False
    session['username'] = ''
    return 'SUCCESS'


if __name__ == '__main__':
    app.run()