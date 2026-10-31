import db
from flask import Flask, request, render_template, session, redirect, url_for
from markupsafe import escape
import json
from contextlib import closing
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "Incredibly-private-and-secure-key"
app.config["DATABASE"] = "prospex.db"

def get_conn():
    return db.get_connection(app.config["DATABASE"])

# Require login decorator use to require login for certain routes. If the user is not logged in, they will be redirected to the login page.
def require_login(func):
    """Decorator to require login for a route"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    """Dashboard, will show filterable list of job applications"""

    path = app.static_folder + '/testing/sample_data.json'
    with open(path, "r", encoding="utf-8") as sample_data_file:
        sample_data = json.load(sample_data_file)

    # Sort by status - in set order
    sort_order = {
        'saved': 1,
        'applied': 2,
        'interviewing': 3,
        'offer': 4,
        'accepted': 5,
        'declined': 6,
        'withdrawn': 7,
        'rejected': 8
    }
    jobs = sorted(sample_data['jobs'], key=lambda job: sort_order[job['status']])

    return render_template(
        "dashboard.html",
        jobs=jobs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))
    error = None
    status = 200
    if request.method == 'POST':
        email = request.form["email"].strip().lower()
        action = request.form.get("action")
        with closing(get_conn()) as conn:

            if action == 'login':
                user = db.get_user_by_email(conn, email)
                if user and db.check_password_hash(user["password_hash"], request.form["password"]):
                    session["user_id"] = user["id"]
                    session["first_name"] = user["first_name"]
                    return redirect(url_for('index'))
                error   = "Invalid login information"
                status = 401
            elif action == "signup":
                try: 
                    password = request.form["password"]
                    if len(password.strip()) < 8:
                        raise ValueError("Password must be longer than 8 characters")
                    hash = db.generate_password_hash(password)
                    first_name = request.form["first_name"]
                    last_name = request.form["last_name"]
                    db.create_user(conn, first_name, last_name, email, hash)
                    user = db.get_user_by_email(conn, email)
                    conn.commit()
                    session["user_id"] = user["id"]
                    session["first_name"] = first_name
                    return redirect(url_for('index'))
                except sqlite3.IntegrityError:
                    error = "That account already exists"
                    status = 409
                except ValueError as e:
                    error = str(e)
                    status = 400

    return render_template("login.html", error=error), status

@app.route('/logout')
def logout():
    # remove username
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    """ Show details about the current user """
    return f'Profile coming soon'

@app.route('/jobs/add')
def add_job():
    """ form for adding a new job application"""
    return f'Placeholder for form for adding new job'

@app.route('/jobs/<int:job_id>')
def job(job_id):
    """show details of saved job application"""
    return f"Job {job_id} details - placeholder for now"

@app.route('/contacts/<int:contact_id>')
def contact(contact_id):
    """show details of saved contact"""
    return f"Contact {contact_id} details - placeholder for now"

@app.route('/contacts/add')
def add_contact():
    @require_login
    """Display a form for adding a new contact to the saved contacts list"""
    return f'Placeholder for form for adding new contact'

@app.route('/contacts/edit/<int:contact_id>')
def edit_contact(contact_id):
    @require_login
    """Display a form for editing an existing contact"""
    return f'Placeholder for form for editing contact {contact_id}   '

@app.route('/contacts')
def contacts():
    """ display a list of contacts """
    return f'Place holder for page showing list of saved contacts'

