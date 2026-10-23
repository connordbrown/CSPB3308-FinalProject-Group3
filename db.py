"""
Data access layer for Prospex.

Routes call these functions instead of writing SQL directly.
Each function to be specified in SQL_TESTING.md (Data Access Methods) and PAGE_TESTING.md (Data Needed).

Every function takes the logged-in user's id, so a user can only read or change their own data.

Stubs: raise NotImplementedError until implemented.
"""

import sqlite3

DESIGNATIONS = ("recruiter", "referrer", "interviewer", "hiring manager", "other")


def get_connection(db_path):
    """Open a connection with foreign keys enforced and rows accessible by column name."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- User ----------

def create_user(conn, first_name, last_bame, email, password_hash):
    """
    Create a user with supplied data.
        Parameters:
            conn (sqlite3.Connection)
            first_name (string)
            last_name (string)
            email (string)
            password_hash (string)
            display_name=None
        Returns:
            - (User object/User dictionary, "") if successful
            - (None, Exception) if failure
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

def login():
    """
    Log the user in to the system.
    """
    raise NotImplementedError

def logout():
    """
    Log the user out of the system.
    """
    raise NotImplementedError

# ---------- Contacts ----------

def get_contacts_for_job(conn, user_id, job_id):
    """
    Returns all associated contacts for a user's job.
        Parameters:
            conn (sqlite3.Connection)
            user_id (int)
            job_id (int)
        Returns:
            - List of contacts
            - Empty list if no contacts
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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

# ---------- Jobs ----------

def get_jobs(conn, user_id, job_id):
    """
    Returns a job with a given id associated with the user.

    Parameters:
        conn (sqlite3.Connection)
        user_id (int)
        job_id (int)

    Returns:
        - Dictionary containing data for job
        - None if job does not exist
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
        list of rows with: id, title, company_name
        (company name helps tell apart jobs with the same title)
        - Sorted by company name, then title
        - Empty list if none
    """
    raise NotImplementedError