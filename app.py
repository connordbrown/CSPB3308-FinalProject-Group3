import db
from flask import Flask, request, render_template, session, redirect, url_for, flash, abort
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

def blank_to_none(value):
    """Strip whitespace; return None for missing or blank values."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def to_int_or_none(value):
    """Convert a dropdown value like "3" to 3; blank becomes None."""
    value = blank_to_none(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError("Invalid selection.")



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


@app.route('/contacts/add', methods=['GET', 'POST'])
@require_login
def add_contact():
    """Display a form for adding a new contact to the saved contacts list"""
    user_id = session["user_id"]
    error = None
    status = 200 
    form_values = {}       
    with closing(get_conn()) as conn:
        if request.method == "POST":
            form_values = request.form.to_dict()
            try:
                # read and clean each field
                name = request.form.get("name", "")
                title = blank_to_none(request.form.get("title"))
                designation = blank_to_none(request.form.get("designation"))
                email = blank_to_none(request.form.get("email"))
                phone = blank_to_none(request.form.get("phone"))
                linkedin_url = blank_to_none(request.form.get("linkedin_url"))
                notes = blank_to_none(request.form.get("notes"))
                company_id = to_int_or_none(request.form.get("company_id"))
                job_id = to_int_or_none(request.form.get("job_id"))
                new_company_name = blank_to_none(request.form.get("new_company_name"))


                # handle adding a new company from Contacts form
                if new_company_name is not None:
                    company_id = db.get_or_create_company(conn, user_id, new_company_name)

                # save contact
                db.create_contact(
                    conn, user_id, name=name, title=title, designation=designation,
                    company_id=company_id, job_id=job_id, email=email, phone=phone,
                    linkedin_url=linkedin_url, notes=notes
                )
                # commit, flash, redirect
                conn.commit()
                flash("Contact saved")
                return redirect(url_for("contacts"))

            except ValueError as e:
                conn.rollback()
                error = str(e)
                status = 400

        companies = db.get_companies_for_user(conn, user_id)
        jobs = db.get_jobs_for_user(conn, user_id)
        
    return render_template("contact_form.html", contact=None, form=form_values, error=error,
                            companies=companies, jobs=jobs, designations=db.DESIGNATIONS), status

@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_contact(contact_id):    
    """Display a form for editing an existing contact"""
    user_id = session["user_id"]
    error = None
    status = 200

    with closing(get_conn()) as conn:
        contact = db.get_contact(conn, user_id, contact_id)
        if contact is None:
            abort(404, description="Contact not found")
        form_values = dict(contact)  # pre-fill form with existing contact data

        companies = db.get_companies_for_user(conn, user_id)
        jobs = db.get_jobs_for_user(conn, user_id)

        if request.method == "POST":
            form_values = request.form.to_dict()
            try:
                # read and clean each field
                name = request.form.get("name", "")
                title = blank_to_none(request.form.get("title"))
                designation = blank_to_none(request.form.get("designation"))
                email = blank_to_none(request.form.get("email"))
                phone = blank_to_none(request.form.get("phone"))
                linkedin_url = blank_to_none(request.form.get("linkedin_url"))
                notes = blank_to_none(request.form.get("notes"))
                company_id = to_int_or_none(request.form.get("company_id"))
                job_id = to_int_or_none(request.form.get("job_id"))
                new_company_name = blank_to_none(request.form.get("new_company_name"))

                # handle adding a new company from Contacts form
                if new_company_name is not None:
                    company_id = db.get_or_create_company(conn, user_id, new_company_name)

                # save contact
                updated = db.update_contact(
                    conn, contact_id=contact_id, user_id=user_id, name=name, title=title, designation=designation,
                    company_id=company_id, job_id=job_id, email=email, phone=phone,
                    linkedin_url=linkedin_url, notes=notes
                )
                if not updated:
                    conn.rollback()
                    abort(404, description="Contact not found")

                # commit, flash, redirect
                conn.commit()
                flash("Contact saved")
                return redirect(url_for("contact", contact_id=contact_id))

            except ValueError as e:
                conn.rollback()
                error = str(e)
                status = 400

    return render_template("contact_form.html", contact=contact, form=form_values, error=error,
                            companies=companies, jobs=jobs, designations=db.DESIGNATIONS), status

@app.route('/contacts')
def contacts():
    """ display a list of contacts """
    return f'Place holder for page showing list of saved contacts'

