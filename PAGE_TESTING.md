# PAGE_TESTING.md


**Nav bar** At the top of every page via shared 'base.html'
- links to dashboard, contacts, profile and log out when logged in. 

--- 

## 1. Dashboard
**Route:** `/`

![Dashboard mockup](docs/images/dashboard.jpg)

**Description:** The homepage. Logged-out users see a prompt to log in. Logged in users see a list of job applications with Role/Title and company filterable by status and optionally other criteria. A button allows users to add new job applications.

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 2. Login
**Route:** `/login`

![Login page mockup](docs/images/login.jpg)

**Description:** Fields for password and username allow user to either log in or create a new account using the respective buttons. Successful login/account creation takes user to dashboard, otherwise they stay on this page.

**Parameters:**
- GET: none.
- POST, form fields:
  - `email` (str, required): lowercased and trimmed by the app before lookup.
  - `password` (str, required).
  - `action` (str): "login" or "signup", set by the name/value of the button clicked.
  - Signup only: `first_name` (str, required), `last_name` (str, required), `display_name` (str, optional; an empty value is saved as NULL, not "").

**Data needed:**
- Table accessed: `users`.
- Log in: look up one user by lowercased `email`, then check `password` against `password_hash` (`check_password_hash`). On success, store `user_id` in the session (not only the username).
- Sign up: insert a user with `first_name`, `last_name`, `email`, `display_name`, and `generate_password_hash(password)`. Catch the UNIQUE violation on `email` or `display_name` and show a friendly error.
- Access methods needed: `get_user_by_email(email)`, `create_user(first_name, last_name, email, password_hash, display_name=None)`.

**Links:**
- Success (login or signup): redirect to Dashboard (`/`).
- Failure: stay on `/login` with an error message and the typed email kept in the field.
- A user who is already logged in and opens `/login` is redirected to `/`.
- Log out (`/logout`) clears the session and returns to `/`.

**Tests:** TODO

---
## 3. Contacts
**Route:** `/contacts`

![Contacts page mockup](docs/images/contacts.jpg)

**Description:** Provides a list of cnntacts with name, role and company displayed. An 'add new button' takes user to the add new contact page, see below. Clicking on a contact takes the user to the details page for that particular contact. 

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 4. Add / Edit Contact
**Route:** `/contacts/add`, `/contacts/<id>/edit`

![New Contact mockup](docs/images/contacts_new.jpg)

**Description:** Form allows user to save information about a new contact. Name is mandatory. Company, title, email, phone and Linked In are optional. A text field is provided for any relevant notes. Returns to /contacts on save or cancel. 

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 5. Contact Details
**Route:** `/contacts/<id>`

![Contact Details page mockup](docs/images/contacts_id.jpg)

**Description:** Displays saved details regarding a given contact. Name, company and associated job application as well as role, contact information and relevant notes.

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 6. Add / Edit Job
**Routes:** `/jobs/add`, `/jobs/<id>edit`

![Add Job mockup](docs/images/jobs_new.jpg)

**Description:** Form allowing user to save details of a new job application or edit current job. Has fields for role, company and a link to the application itself. Dropdowns for worktype and status. Date defaults to current. Search field or dropdown to add relevant contacts. Notes field allows free-form notes on job. Returns to dashboard on save or cancel.

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 7. Job Details
**Route:** `jobs/<id>`

![Job Details page mockup](docs/images/jobs_id.jpg)

**Description:** Displays details of a given job. Title, company, status, type, link, notes and a list of connected contacts. Edit button will be added to open same job in the add/edit form. 

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO

---
## 8. Profile
**Route:** `user/<username>`

![Profile page mockup](docs/images/profile.jpg)

**Description:** Currently just shows the username and password with buttons to edit each. Could add more details later. 

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
**Tests:** TODO