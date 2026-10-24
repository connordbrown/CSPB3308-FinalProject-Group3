from flask import Flask, request, render_template, session, redirect, url_for

from markupsafe import escape
import json


app = Flask(__name__)
app.secret_key = "Incredibly-private-and-secure-key"

@app.route("/")
def index():
    """Dashboard, will show filterable list of job applications"""

    path = app.static_folder + '/testing/sample_data.json'
    sample_data_file = open(path, "r")
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
        username=session.get("username"),
        jobs=jobs)

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
    """ Show details about the current user """
    return f'{escape(username)}\'s profile'

@app.route('/jobs/add')
def add_job():
    """ form for adding a new job application"""
    return f'Placeholder for form for adding new job'

@app.route('/jobs/<int:job_id>')
def job(job_id):
    """show details of saved job application"""
    return f"Job {job_id} details - placeholder for now"

@app.route('/contacts/<int:person_id>')
def contact(person_id):
    """show details of saved contact"""
    return f"Person {person_id} details - placeholder for now"

@app.route('/contacts/add')
def add_contact():
    """Display a form for adding a new contact to the saved contacts list"""
    return f'Placeholder for form for adding new contact'

@app.route('/contacts')
def contacts():
    """ display a list of contacts """
    return f'Place holder for page showing list of saved contacts'
