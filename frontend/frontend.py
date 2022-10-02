from flask import Flask, redirect, g, request, flash, render_template
import requests

DEBUG = True # debug flag to print error information
SECRET_KEY = "a41014794565ebf9f22b99e2" # Used for cookies / session variables

app = Flask(__name__)
app.config.from_object(__name__) # loads workspace values

# Redirects to '/login' path
@app.route('/')
def initial():
    try:
        requests.get('http://localhost:5000/')
    except:
        pass
    return redirect('/login')

# Start page for new connection, sign in with username and password (if user does not exists it gets created) and goes to '/profile' path through html form.
@app.route('/login', methods=['GET', 'POST'])
def login():
    payload = {"method": request.method}
    if request.method == 'POST':
        payload["data"] = request.form
    try:
        try:
            r = requests.post('http://localhost:5000/login', json=payload)
            if r.text == 'PROFILE':
                return redirect('/profile')
            elif r.text == 'TAKEN':
                flash("That username is already taken") # Flask method to show messages to user (errors, other feedback)
                return render_template('login.html')
            else:
                raise RuntimeError
        except:
            return render_template('login.html')
    except:
        return 'FAIL'

@app.route('/profile', methods=['GET', 'POST'])
def homepage():
    payload = {"method": request.method}
    if request.method == 'POST':
        payload["data"] = request.form
        try:
            user = requests.post('http://localhost:5000/profile', json=payload).json()
            current = user["current"]
        except:
            flash("User does not exist")
            return redirect("/profile")
    else:
        try:
            user = requests.get('http://localhost:5000/currentUser').json()
            if user == 'FAILURE':
                raise RuntimeError
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
    payload = {"method": request.method}
    if request.method == 'POST':
        payload["data"] = request.form
        try:
            requests.post('http://localhost:5000/edit', json=payload)
            return redirect('/profile')
        except:
            return "FAIL"
    try:
        user = requests.get('http://localhost:5000/currentUser').json()
        if user == 'FAILURE':
            raise RuntimeError
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
    payload = {"method": request.method}
    if request.method == 'POST':
        payload["data"] = request.form
        try:
            requests.post('http://localhost:5000/editbg', json=payload)
            return redirect('/profile')
        except:
            return "FAIL"
    try:
        user = requests.get('http://localhost:5000/currentUser').json()
        if user == 'FAILURE':
            raise RuntimeError
    except:
        return redirect('/login')

    return render_template('editBackground.html',
        bg = user["bg"]
    )

@app.route('/delete')
def delete():
    try:
        user = requests.get('http://localhost:5000/currentUser').json()
        if user == 'FAILURE':
            raise RuntimeError
    except:
        return redirect('/login')
    
    # If user does not exist in table, go back to profile
    try:
        requests.get('http://localhost:5000/delete')
    except:
        flash('Could not remove user')
        return redirect('/profile')

    # If all passes go to login.
    flash("Deleted user")
    return redirect('/login')


if __name__ == '__main__':
    app.run(port=8080)