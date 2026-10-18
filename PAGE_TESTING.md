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

**Tests:**
1. GET `/login` returns 200 and shows the form with both buttons.
2. Log in with a valid email and password (e.g., `alex.demo@example.com` / `DemoPass123!`) redirects to `/` and the session holds Alex's `user_id`.
3. Log in with the right email in different case (`ALEX.DEMO@example.com`) succeeds.
4. Log in with a wrong password stays on `/login`, shows an error, and creates no session.
5. Log in with an unknown email gives the same generic error as test 4, so the page doesn't reveal which emails exist.
6. Sign up with valid fields creates one new `users` row, logs the user in, and redirects to `/`.
7. The new row's `password_hash` is a hash, not the plain password.
8. Sign up with an email that already exists (including different case) stays on `/login`, shows an error, and adds no row.
9. Sign up with a missing `first_name`, `last_name`, or `password` shows an error and adds no row.
10. Sign up with a `display_name` already in use shows an error and adds no row.
11. Two sign-ups with a blank `display_name` both succeed (stored as NULL).
12. A logged-in user who opens `/login` is redirected to `/`.
13. `/logout` clears the session; the nav bar goes back to its logged-out state.

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

**Parameters:**
- `job_id` (int, URL path): must be a whole number.
- Session `user_id`: required. A logged-out visitor is redirected to `/login`.

**Data needed:**
- Tables accessed: `jobs`, `companies`, `contacts`. Every query also filters on the session `user_id`.
- Job: `title`, `status`, `work_type`, `link`, `notes`, `date_applied`, joined to the company's `name`, `city`, `region`.
- Linked contacts: `id`, `name`, `title`, `designation` for contacts where `job_id` = the job and `user_id` = the session user.
- Access methods needed: `get_job(user_id, job_id)` (returns the job with its company, or None) and `get_contacts_for_job(user_id, job_id)` (returns a list, possibly empty).
- Empty values (NULL `link`, `work_type`, `notes`, `date_applied`, or company `city`/`region`) are left out or shown as a dash. The page never shows "None".

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