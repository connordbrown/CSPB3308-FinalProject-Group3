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

**Description:** Provides a list of contacts with name, title and company displayed. An 'add new button' takes user to the add new contact page, see below. Clicking on a contact takes the user to the details page for that particular contact. 

**Parameters:** 

- Route: none
- Query: none (filtering is a possible stretch goal)
- Session: logged-in `user_id` (required; otherwise redirect to `/login`)

**Data needed:** 

Session: `user_id`
- Database: `get_contacts_for_user(user_id)` returns each contact's id, name, title, and company name
  - Uses a LEFT JOIN to companies so contacts with no company still appear
  - Sorted alphabetically by name

**Links:** 

- Contact row →`/contacts/<id>`
- + Add new → `/contacts/add`
- Log out → `/logout`
- Nav bar → per `base.html`

**Tests:** 

1. Not logged in redirects to `/login`
2. Page loads with "Contacts" heading and "Add new" button
3. Each contact shows name, title, and company
4. Only the logged-in user's contacts appear
5. Contact with no title or company still appears; empty fields are blank, not "None"
6. User with no contacts sees an empty-state message; Add button still shows
7. Clicking a contact opens its detail page
8. "Add new" opens `/contacts/add`

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