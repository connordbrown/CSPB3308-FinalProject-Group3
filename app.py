from flask import Flask, request, render_template, session, redirect, url_for
from markupsafe import escape


app = Flask(__name__)
app.secret_key = "Incredibly-private-and-secure-key"

@app.route("/")
def index():
    """Dashboard, will show filterable list of job applications"""
    return render_template("dashboard.html", username=session.get("username"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route('/logout')
def logout():
    # remove username
    session.pop('username', None)
    return redirect(url_for('index'))
        

@app.route('/user/<username>')
def profile(username):
    return f'{escape(username)}\'s profile'
