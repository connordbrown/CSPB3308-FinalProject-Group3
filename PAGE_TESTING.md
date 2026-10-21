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

**Description:** Fields for password and username allow user to either log in or create a new account using the respective buttons. Successful login/account creation takes user to dahsboard, otherwise they stay on this page.

**Parameters:** TODO
**Data needed:** TODO
**Links:** TODO
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

**Description:** Shows logged-in user's first name, last name, email in pre-filled editable forms with save buttons to change either. Change password form also displayed. The password and hash are never shown. Possibly display some additional stats as a stretch goal for this page.


**Parameters:** 

- Route Parameters: None (user comes from session)

- Form data on edits (POST):
    - `first_name` (required)
    - `last_name` (required)
    - `email` (required)
- password form:   `(profile/password)`
    - `current_password` (required)
    - `new_password` (required)
    - `confirmation` (required, must match new)

**Data needed:** 

- Session: `user_id`
- Database:
    - `get_user(user_id)` to fill forms with `email`, `first_name`, `last_name`.
    - `update_user(user_id, first_name, last_name, email)` to change email and/or name
    - `change_password(user_id, current_password, new_password)` change the password

**Links:** 

- Edit → `/profile` GET shows the saved info, POST updates name, email and redirects back to profile
- Change password → `/profile/password` changes password and redirects back to profile

**Tests:** 

1. Logged in GET for `/profile` returns 200
2. Logged out GET or POST does not change db and redirects to `/login`
3. Shows the correct first name, last name and email for the logged in user
4. password not accessible in html

- Editing
5. valid inputs for name, email save to db, redirect to `/profile` and page shows new info
6. if any required field is empty on POST, error displayed, nothing saved to db
7. email already in use: error displayed, nothing saved
8. email in different case (M.cspb vs m.cspb): error, no save
9. changing other fields without changing email does not result in error

- Password

10. unchanged password results in no changes on save
11. matching new passwords result new saved password  with displayed message "password changed"
12. wrong current password entered: Error, no change in db
13. new and confirmation don't match: Error, no change
