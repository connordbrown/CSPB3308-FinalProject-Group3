"""
Data access layer for Prospex.

Routes call these functions instead of writing SQL directly.
Each function to be specified in SQL_TESTING.md (Data Access Methods) and PAGE_TESTING.md (Data Needed).

Every function takes the logged-in user's id, so a user can only read or change their own data.

Stubs: raise NotImplementedError until implemented.
"""

import sqlite3

DESIGNATIONS = ("recruiter", "referrer", "interviewer", "hiring manager", "other")
# Added since last SCRUM meeting
STATUSES = ("saved", "applied", "interviewing", "offer", "rejected",
            "accepted", "declined", "withdrawn")
# Added since last SCRUM meeting
WORK_TYPES = ("remote", "hybrid", "in person")


def get_connection(db_path):
    """Open a connection with foreign keys enforced and rows accessible by column name."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Users ----------

# Added since last SCRUM meeting
def get_user_by_email(conn, email):
    """
    Return one user by email for login.

    Parameters:
        conn (sqlite3.Connection)
        email (str): lowercased and trimmed by the route before the call

    Returns:
        one row with: id, first_name, last_name, email, password_hash, display_name
        - Match is case-insensitive (email column is COLLATE NOCASE)
        - None if no user has that email
    """
    raise NotImplementedError

def generate_password_hash(password):
    """
    Generate a password hash from a user's password.
    Parameters:
        password (string)
    Returns:
        - Password hash (string) of original password
    """
    raise NotImplementedError

# Added since last SCRUM meeting
def create_user(conn, first_name, last_name, email, password_hash, display_name=None):
    """
    Insert a new user at signup.
    The route hashes the password with generate_password_hash before calling.

    Parameters:
        conn (sqlite3.Connection)
        first_name (str, required)
        last_name (str, required)
        email (str, required): lowercased and trimmed
        password_hash (str, required)
        display_name (str, optional): empty string stored as NULL

    Returns:
        int: the new user's id

    Raises:
        ValueError if a required field is empty.
        sqlite3.IntegrityError if the email (any case) or display_name is already
        in use; the route catches it and shows a friendly error.
    """
    raise NotImplementedError


# Added since last SCRUM meeting
def get_user(conn, user_id):
    """
    Return the user's details for the Profile page. Never returns password_hash.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)

    Returns:
        one row with: id, first_name, last_name, email, display_name,
        or None if the user does not exist.
    """
    raise NotImplementedError


# Added since last SCRUM meeting
def update_user(conn, user_id, first_name, last_name, email):
    """
    Save changes to the user's name and email from the Profile page.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        first_name (str, required)
        last_name (str, required)
        email (str, required): lowercased and trimmed

    Returns:
        bool: True if the user was updated, False if the user does not exist.

    Raises:
        ValueError if a field is empty.
        sqlite3.IntegrityError if another user already has that email (any case).
    """
    raise NotImplementedError


# Added since last SCRUM meeting
def change_password(conn, user_id, current_password, new_password):
    """
    Change the user's password if current_password is correct.
    Checks with check_password_hash and stores generate_password_hash(new_password).
    The route checks that new_password matches its confirmation before calling.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        current_password (str)
        new_password (str, required)

    Returns:
        bool: True if the password was changed,
              False if current_password is wrong or the user does not exist.

    Raises:
        ValueError if new_password is empty.
    """
    raise NotImplementedError


# ---------- Jobs ----------

# Added since last SCRUM meeting
def get_job(conn, user_id, job_id):
    """
    Return one job with its company, only if it belongs to the user.
    Used by Job Details and to prefill the Edit Job form.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        job_id (int)

    Returns:
        one row with: id, title, status, work_type, link, notes, date_applied,
        company_id, company_name, city, region,
        or None if the job does not exist or belongs to another user.
    """
    raise NotImplementedError


# Added since last SCRUM meeting
def create_job(conn, user_id, company_id, title, status="saved", work_type=None,
               link=None, notes=None, date_applied=None):
    """
    Insert a new job for the user.
    If the user typed a new company, the route calls get_or_create_company first
    (same transaction) and passes its id.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        company_id (int, required)
        title (str, required)
        status (str): defaults to 'saved'
        work_type, link, notes (str, optional)
        date_applied (str 'YYYY-MM-DD', optional)

    Returns:
        int: the new job's id

    Raises:
        ValueError if title is empty, status is not in STATUSES,
        work_type is not in WORK_TYPES, or company_id does not belong to the user.
    """
    raise NotImplementedError


# Added since last SCRUM meeting
def update_job(conn, user_id, job_id, company_id, title, status="saved", work_type=None,
               link=None, notes=None, date_applied=None):
    """
    Replace an existing job's fields, only if it belongs to the user.

    Parameters:
        same as create_job, plus job_id (int)

    Returns:
        bool: True if the job was updated,
              False if it does not exist or belongs to another user.

    Raises:
        ValueError for the same validation rules as create_job.
    """
    raise NotImplementedError


# ---------- Contacts ----------

def get_contacts_for_user(conn, user_id):
    """
    Return all of the user's contacts for the Contacts list page.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)

    Returns:
        list of rows with: id, name, title, company_name
        - Includes contacts with no company (company_name is None) -> LEFT JOIN
        - Sorted by name
        - Empty list if the user has no contacts or does not exist
    """

    return conn.execute(
        """
        SELECT c.id, c.name, c.title, co.name AS company_name 
        FROM contacts c
        LEFT JOIN companies co ON c.company_id = co.id
        WHERE c.user_id = ?
        ORDER BY c.name
    """, (user_id,)).fetchall() 


def get_contacts_for_job(conn, user_id, job_id):
    """
    Return the contacts linked to one job, only if the job and contacts belong to the user.
    Used by Job Details and the Edit Job form.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        job_id (int)

    Returns:
        list of rows with: id, name, title, designation
        - Sorted by name
        - Empty list if no contacts are linked, or the job does not exist
          or belongs to another user
    """
    return conn.execute(
        """
        SELECT c.id, c.name, c.title, c.designation
        FROM contacts c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.id = ? AND j.user_id = ?
        ORDER BY c.name
    """, (job_id, user_id)).fetchall()


def get_contact(conn, user_id, contact_id):
    """
    Return one contact, only if it belongs to the user.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        contact_id (int)

    Returns:
        one row with all contact fields plus company_name and job_title -> LEFT JOIN
        (None if not linked), or None if the contact does not exist
        or belongs to another user.
    """
    return conn.execute(
        """
        SELECT c.*, co.name AS company_name, j.title AS job_title
        FROM contacts c
        LEFT JOIN companies co ON c.company_id = co.id
        LEFT JOIN jobs j ON c.job_id = j.id
        WHERE c.id = ? AND c.user_id = ?
        """, (contact_id, user_id)).fetchone()


def create_contact(conn, user_id, name, title=None, designation=None,
                   company_id=None, job_id=None, email=None, phone=None,
                   linkedin_url=None, notes=None):
    """
    Insert a new contact for the user.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        name (str, required)
        all other fields optional (None stored as NULL)

    Returns:
        int: the new contact's id

    Raises:
        ValueError if name is empty, designation is not in DESIGNATIONS,
        or company_id / job_id does not belong to the user.
    """
    if name is None or not isinstance(name, str) or name.strip() == "":
        raise ValueError("Name is required and cannot be empty.")
    if designation == "":
        designation = None  # Treat empty string as None
    if designation is not None and designation not in DESIGNATIONS:
        raise ValueError("Invalid designation.")
    # Check if the provided job_id and company_id belong to the user
    if job_id is not None:
        job = conn.execute(
            "SELECT id FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)
        ).fetchone()
        if job is None:
            raise ValueError("Job does not belong to the user.")
    if company_id is not None:
        company = conn.execute(
            "SELECT id FROM companies WHERE id = ? AND user_id = ?", (company_id, user_id)
        ).fetchone()
        if company is None:
            raise ValueError("Company does not belong to the user.")
    # Insert the new contact
    contact_id = conn.execute(
        """
        INSERT INTO contacts (user_id, name, title, designation, company_id, job_id,
                              email, phone, linkedin_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, title, designation, company_id, job_id, email, phone, linkedin_url, notes)
    ).lastrowid
    return contact_id


def update_contact(conn, user_id, contact_id, name, title=None, designation=None,
                   company_id=None, job_id=None, email=None, phone=None,
                   linkedin_url=None, notes=None):
    """
    Replace an existing contact's fields, only if it belongs to the user.

    Parameters:
        same as create_contact, plus contact_id (int)

    Returns:
        bool: True if the contact was updated,
              False if it does not exist or belongs to another user.

    Raises:
        ValueError for the same validation rules as create_contact.
    """
    # Check if company_id and job_id belong to the user
    if company_id is not None:
        company = conn.execute(
            "SELECT id FROM companies WHERE id = ? AND user_id = ?", (company_id, user_id)
        ).fetchone()
        if company is None:
            raise ValueError("Company does not belong to the user.")
    if job_id is not None:
        job = conn.execute(
            "SELECT id FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)
        ).fetchone()
        if job is None:
            raise ValueError("Job does not belong to the user.")

    # Validate name and designation
    if name is None or not isinstance(name, str) or name.strip() == "":
        raise ValueError("Name is required and cannot be empty.")
    if designation == "":
        designation = None  # Treat empty string as None
    if designation is not None and designation not in DESIGNATIONS:
        raise ValueError("Invalid designation.")
        
    cursor = conn.execute(
        """
        UPDATE contacts
        SET name = ?, title = ?, designation = ?, company_id = ?, job_id = ?, email = ?, phone = ?, linkedin_url = ?, notes = ?
        WHERE id = ? AND user_id = ?
        """, (name, title, designation, company_id, job_id, email, phone, linkedin_url, notes, contact_id, user_id)
    )

    return cursor.rowcount == 1  # True if one row was updated, False otherwise


def delete_contact(conn, user_id, contact_id):
    """
    Deletes an existing contact only if it belongs to the user.
    The contact's linked company and job are not affected

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        contact_id (int)

    Returns:
        bool: True if the contact was deleted,
            False if the contact doesn't exist or belongs to another user
    
    """
    raise NotImplementedError

# ---------- Companies ----------
 
def get_or_create_company(conn, user_id, name):
    """
    Return the id of the user's company with this name, creating it if needed.
    Used by the inline "+ Add new company" option on the Add/Edit Contact
    and Add/Edit Job forms.
 
    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        name (str): leading/trailing whitespace is stripped
 
    Returns:
        int: id of the existing or newly created company
        - Name match is case-insensitive ("spotify" reuses "Spotify")
        - Only matches the user's own companies; another user's company
          with the same name is never reused
 
    Raises:
        ValueError if name is empty or only whitespace.
    """
    raise NotImplementedError

# ---------- Dropdown data ----------

def get_companies_for_user(conn, user_id):
    """
    Return the user's companies for dropdowns.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)

    Returns:
        list of rows with: id, name
        - Sorted by name
        - Empty list if none
    """
    raise NotImplementedError


def get_jobs_for_user(conn, user_id):
    """
    Return the user's jobs for dropdowns.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)

    Returns:
        list of rows with: id, title, company_name, status
        (company name helps tell apart jobs with the same title)
        - Sorted by company name, then title
        - Empty list if none
    """
    raise NotImplementedError