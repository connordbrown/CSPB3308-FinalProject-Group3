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

**Data needed:** 

Session: `user_id`
- Database: `get_contacts_for_user(user_id)` returns each contact's id, name, title, and company name
    - Uses a LEFT JOIN to companies so contacts with no company still appear
    - Sorted alphabetically by name

**Links:** 

- Contact row →`/contacts/<id>`
- Add new → `/contacts/add`
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

**Parameters:** 

- Add (`/contacts/add`): none
- Edit (`/contacts/<id>/edit`): route parameter `contact_id`
- Form data on submit (POST), both modes:
    - `name` (required)
    - `title`, `designation`, `company_id`, `job_id`, `email`, `phone`, `linkedin_url`, `notes` (optional)
  - `new_company_name` (used only when "+ Add new company" is selected)

**Data needed:** 

- Session: `user_id`
-Database:
    - `get_companies_for_user(user_id)` for Company dropdown
    - `new_company_name
    - `get_jobs_for_user(user_id)` for Job dropdown
    - Edit only: `get_contact(user_id, contact_id)` to prefill the form
    - On submit: `create_contact(...)` (add) or `update_contact(...)` (edit)
    - On submit, if "+ Add new company" is selected: `get_or_create_company(user_id, new_company_name)`, then its id is saved as the contact's `company_id`
        -(possible stretch goal → expand function to add city, region, website, notes or add an "Edit Companies" page)
- Static: designation options for dropdown
- Form state: validation error message and previously entered values

**Links:** 

- Save (add) → `/contacts`
- Save (edit) → `/contacts/<id>`
- Cancel → `/contacts` (add) or `/contacts<id>` (edit); nothing is saved
- Nav bar → (dashboard, contacts, profile) -> their pages
- Log Out → `/logout`

**Tests:** 

1. Not logged in: redirects to `/login`
2. All fields render; Name is required
3. Company and Job dropdowns list only the logged-in user's companies and jobs, plus a "None" option, and "+ Add Company" that shows a company name field for companies only 
4. Submitting without a name shows an error, saves nothing, and keeps the other entered values
5. Submitting with only a name succeeds
6. A valid submit creates the contact, redirects to `/contacts`, and the new contact appears in the list
7. Cancel saves nothing and returns to the previous page
8. Submitting a `company_id` or `job_id` belonging to another user is rejected
9. Edit: form is prefilled with the contact's current values
10. Edit: saving changes updates the contact and redirects to its details page
11. Edit: using another user's `contact_id` returns "not found"
12. Selecting "+ Add new company" with a name creates the company and links the contact to it
13. Entering an existing company's name in any capitalization reuses that company instead of creating a duplicate
14. Selecting "+ Add new company" with a blank name shows an error and saves nothing

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