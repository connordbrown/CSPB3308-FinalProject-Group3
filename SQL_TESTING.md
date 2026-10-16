# SQL_TESTING.md
## Project Milestone 5: SQL Design
**Project:** Prospex (Job Search Tracker)

**Team:** CSPB 3308 Group 3

**Purpose:** Database design and testing specification for developers

---

## Overview

This document describes the database design for Prospex: the tables, their fields and constraints, how they relate, the functions used to access the data, and the tests that verify each piece. It is written for the developers building the Flask backend and pages, so they can build against one agreed design.

**Database:** SQLite

**Accessed from:** Flask backend via Python's built-in `sqlite3` module, through a data access layer of Python functions that hide the SQL 

### Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Login | Users log in with email; email is UNIQUE and lowercased by the app before saving or lookup | Realistic, and allows password reset later; lowercasing prevents duplicate accounts that differ only by case |
| Jobs table | One `jobs` table. Status defaults to 'saved'; `date_applied` is nullable | Applying only adds a date and a status change, so a separate applications table would hold almost nothing |
| Status | Column on `jobs` with a CHECK constraint: saved, applied, interviewing, offer, rejected, accepted, declined, withdrawn | Short, fixed list with no data of its own; CHECK blocks invalid values at the database level |
| Companies | `companies` table referenced by `jobs` and `contacts`; UNIQUE per user on name | Reliable "who I know at this company"; prevents duplicate company names per user |
| Adding companies | App handles "pick existing or add company": the route looks up the company by name and creates it if missing, in the same transaction as the job insert | Keeps business logic in the app, not in database triggers |
| Contacts in MVP | Yes. Each contact has an optional link to one job, plus a designation (e.g., referrer, recruiter, interviewer, hiring manager) | The vision promises tracking "applications and connections"; one job per contact keeps the MVP simple |
| Deleting a user | ON DELETE CASCADE to all of their rows | Deleting an account removes all of that user's data |
| Deleting a company | `jobs.company_id` uses NO ACTION (SQLite default); `contacts.company_id` uses SET NULL | NO ACTION blocks deleting a company that still has jobs, but is checked at the end of the statement, so a user's cascade delete always succeeds. RESTRICT was rejected because it is checked immediately and can block the user cascade depending on table creation order. Contacts are kept when their company is deleted |
| Deleting a job | Contacts' `job_id` is SET NULL | The person stays in the user's network even if the job is removed |
| Contacts without a company | Allowed (`company_id` nullable) | Covers people met at meetups or events with no company tie |
| Location and work type | `city` and `region` on `companies`; `work_type` (remote, hybrid, in person) on `jobs` | Location is recorded once per company; work arrangement varies by job |
| Date applied | `date_applied` is nullable and set or edited manually by the user; no CHECK ties it to status | Users often log applications after the fact, so they need full control of the date; keeps the schema simple |
| Status history | Stretch goal (see below) | Adds a table beyond the agreed MVP scope |
| File uploads (CV, cover letter) | Stretch goal; would add a `documents` table (one job, many documents) | Upload handling and storage on free hosts is a project of its own |
| Database | SQLite | Matches Lab 7, so the whole team will know it; no install needed; fresh test databases are easy to create in unit tests |
| Foreign key enforcement | Every connection runs `PRAGMA foreign_keys = ON` | SQLite ignores foreign keys by default; without this, CASCADE, RESTRICT, and SET NULL silently do nothing |
| Primary keys | Explicit `id INTEGER PRIMARY KEY` on every table | Auto-generates ids without relying on SQLite's implicit rowid |
| Naming convention | Plural snake_case table names; primary key `id`; foreign keys `<singular table>_id` (e.g., `user_id`) | Standard practice; consistent across all tables |
| Data ownership | Every `companies`, `jobs`, and `contacts` row references `users.id` | Users only ever see their own data |

### Known Trade-offs (MVP)
- SQLite stores the database as a file on the server. Some free hosts wipe local files on restart or redeploy, so the deployment setup must keep the file (revisit when the course covers cloud deployment). A seed script will rebuild demo data in one command.
- A contact linked to more than one job must be entered twice (a `job_contacts` join table would fix this later).
- Only the applied date is stored, not when other status changes happened (see Stretch: Status History).
- A user must delete or move a company's jobs before deleting the company itself.
- Location is stored once per company, not per job. Jobs at a company's other offices can't show their own city (a per-job location field would fix this later).

### Stretch: Status History (possible addition)
Records the date of every status change, which enables stats like time from applied to interview.

**What would change:**
- **New table `job_status_history`:** one row per status change.
  - `id`: INTEGER, primary key
  - `job_id`: INTEGER, FK → `jobs.id`, NOT NULL, ON DELETE CASCADE
  - `status`: TEXT, NOT NULL, same CHECK list as `jobs.status`
  - `changed_at`: DATE, NOT NULL, DEFAULT today; editable, since users often log a change after it happened
- **`jobs.date_applied` would be removed.** The applied date becomes the history row where status = 'applied'. Storing it in both places lets them disagree.
- **`jobs.status` stays** as the current status, so dashboard queries don't need to search the history.
- **The app writes two rows on every status change:** it updates `jobs.status` and inserts a history row, in one transaction.
- **A history row is inserted when a job is created,** with status 'saved'.
- **New access methods and tests:** e.g., get the history for a job, plus a test that a status change creates exactly one history row.

### Entity Relationship Diagram
![Prospex ER diagram](docs/images/erd.png)

[View and edit on dbdiagram.io](https://dbdiagram.io/d/Prospex-database-schema-SQLite-6ac692d3a5ab28041913c48e)

---

# Database Tables

Tables in the MVP:
- `users`
- `companies`
- `jobs`
- `contacts`

### Relationships Summary
- A user has many companies, jobs, and contacts.
- A company has many jobs and many contacts.
- Each job belongs to one company.
- A job has zero or more contacts.
- A contact has zero or one job, and zero or one company.

---

## 1) Table: users

### Table Description
Stores individual users so that only an individuals own data is available to them. 

### Fields
| Field Name | Type | Description | Constraints |
|---|---|---|---|
| id | INTEGER | [auto-incremented id code ] | PRIMARY KEY (auto-generated) |
| first_name | TEXT | [the user's typed first name] | NOT NULL| 
|last_name | TEXT | [the user's typed last name] | NOT NULL |
| email | TEXT | [  the user's email address] | NOT NULL, UNIQUE; lowercased by the app |
| password_hash | TEXT | [hashkey to password for login ] | NOT NULL |
|display_name | the user's preferred display name | TEXT | UNIQUE |
| created_at | TIMESTAMP | [records date of user creation ] | NOT NULL, DEFAULT current timestamp |


### Relationships
- One-to-many with `companies`, `jobs`, and `contacts` (ON DELETE CASCADE)

### Table Tests

All tests are in `test_schema.py` (class `TestUsers`). Each test runs on a fresh in-memory database built from `schema.sql` with `PRAGMA foreign_keys = ON`.

#### Users #1

**Use Case Name:** Insert a valid user succeeds (`test_insert_valid_user`)  
**Pre-conditions:** Empty `users` table  
**Test Steps:**
1. Insert a user with first_name, last_name, email, password_hash, and display_name
2. Select the user by email

**Expected Result:** Row exists and every column matches the inserted values  
**Actual Result:** Row found; all five values saved unchanged  
**Status:** Pass

#### Users #2

**Use Case Name:** Insert user with missing email fails (`test_insert_user_missing_email`)  
**Pre-conditions:** Empty `users` table  
**Test Steps:**
1. Insert a user with every required field except email

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: users.email  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Users #3

**Use Case Name:** Insert user with missing first_name or last_name fails (`test_insert_user_missing_name`)  
**Pre-conditions:** Empty `users` table  
**Test Steps:**
1. Insert a user without first_name
2. Insert a user without last_name

**Expected Result:** Each insert raises `IntegrityError`: NOT NULL constraint failed on the missing column  
**Actual Result:** Both inserts raised `IntegrityError` naming `users.first_name` and `users.last_name`  
**Status:** Pass

#### Users #4

**Use Case Name:** Insert user with missing password hash fails (`test_insert_user_missing_password`)  
**Pre-conditions:** Empty `users` table  
**Test Steps:**
1. Insert a user with every required field except password_hash

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: users.password_hash  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Users #5

**Use Case Name:** Insert user with an existing email fails, including different case (`test_insert_user_existing_email`)  
**Pre-conditions:** One user exists with email `ozzy@example.com`  
**Test Steps:**
1. Insert a second user with `ozzy@example.com`
2. Insert a second user with `Ozzy@Example.com`
3. Count rows in `users`

**Expected Result:** Both inserts raise `IntegrityError`: UNIQUE constraint failed: users.email; only 1 user remains  
**Actual Result:** Both inserts rejected; user count is 1  
**Status:** Pass

#### Users #6

**Use Case Name:** New user gets an auto-generated id and created_at (`test_id_timestamp_at_creation`)  
**Pre-conditions:** Empty `users` table  
**Test Steps:**
1. Insert two users without supplying id or created_at
2. Select id and created_at for each

**Expected Result:** Each id is an integer and the two ids differ; each created_at is set in `YYYY-MM-DD HH:MM:SS` format  
**Actual Result:** Unique integer ids generated; both timestamps present in the expected format  
**Status:** Pass

#### Users #7

**Use Case Name:** Deleting a user deletes their company, job, and contact (`test_cascade_on_delete_user`)  
**Pre-conditions:** One user with one company, one job at that company, and one contact linked to both  
**Test Steps:**
1. Confirm one row per table belongs to the user
2. Delete the user
3. Count the user's rows in every table

**Expected Result:** Delete succeeds (CASCADE works even though the job still references the company); 0 rows remain in `users`, `companies`, `jobs`, and `contacts`  
**Actual Result:** Delete succeeded; all four counts are 0  
**Status:** Pass

---

## 2) Table: jobs

### Table Description
Stores individual jobs entered by the user.

### Fields
| Field Name | Type | Description | Constraints |
|---|---|---|---|
| id | INTEGER | auto-incremented id code | PRIMARY KEY (auto-generated) |
| user_id | INTEGER | id of the user that added job | FK → users.id, NOT NULL, ON DELETE CASCADE |
| company_id | INTEGER | id of company offering job | FK → companies.id, NOT NULL, ON DELETE NO ACTION |
| title | TEXT | job title | NOT NULL |
| link | TEXT | link to the post for added job | Nullable |
| work_type | TEXT | indicates remote work status of job | Nullable, CHECK (remote, hybrid, in person) |
| notes | TEXT | space for any notes a user wants to add | Nullable |
| status | TEXT | application status for job | NOT NULL, DEFAULT 'saved', CHECK (saved, applied, interviewing, offer, rejected, accepted, declined, withdrawn) |
| date_applied | DATE | date application sent | Nullable; entered or edited manually by the user |
| created_at (optional) | TIMESTAMP | job creation date | NOT NULL, DEFAULT current timestamp |

### Relationships
- Many-to-one with `users`
- Many-to-one with `companies`
- One-to-many with `contacts`

### Table Tests

All tests are in `test_schema.py` (class `TestJobs`). Each test starts with a fresh database containing one user and one company owned by that user.

#### Jobs #1

**Use Case Name:** Insert a valid job succeeds (`test_insert_valid_job`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with every column filled in (status 'applied', work_type 'in person')
2. Select the job by id

**Expected Result:** Row exists and every column matches the inserted values  
**Actual Result:** Row found; all eight values saved unchanged  
**Status:** Pass

#### Jobs #2

**Use Case Name:** Insert job with missing title fails (`test_insert_job_missing_title`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with every column except title

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: jobs.title  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #3

**Use Case Name:** Insert job with missing company_id fails (`test_insert_job_missing_companyid`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with every column except company_id

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: jobs.company_id  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #4

**Use Case Name:** Insert job with a company_id that doesn't exist fails (`test_insert_job_nonexistent_companyid`)  
**Pre-conditions:** One user and one company exist; no company has id 9999  
**Test Steps:**
1. Insert a job with company_id 9999

**Expected Result:** `IntegrityError`: FOREIGN KEY constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #5

**Use Case Name:** Insert job with a user_id that doesn't exist fails (`test_insert_job_nonexistent_userid`)  
**Pre-conditions:** One user and one company exist; no user has id 9999  
**Test Steps:**
1. Insert a job with user_id 9999

**Expected Result:** `IntegrityError`: FOREIGN KEY constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #6

**Use Case Name:** Insert job with no status gets 'saved' by default (`test_insert_job_default_status`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job without the status column
2. Select the job's status

**Expected Result:** status is 'saved'  
**Actual Result:** status is 'saved'  
**Status:** Pass

#### Jobs #7

**Use Case Name:** Insert job with a status not on the list fails (`test_insert_job_unlisted_status`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with status 'appiled' (misspelled)

**Expected Result:** `IntegrityError`: CHECK constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #8

**Use Case Name:** Insert job with a work_type not on the list fails (`test_insert_job_unlisted_worktype`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with work_type 'in persone' (misspelled)

**Expected Result:** `IntegrityError`: CHECK constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Jobs #9

**Use Case Name:** Insert job with no date_applied, link, notes, or work_type succeeds (`test_insert_job_missing_nullable_fields`)  
**Pre-conditions:** One user and one company exist  
**Test Steps:**
1. Insert a job with only user_id, company_id, title, and status
2. Select date_applied, link, notes, and work_type

**Expected Result:** Insert succeeds; all four optional columns are NULL  
**Actual Result:** Row found; all four columns are NULL  
**Status:** Pass

#### Jobs #10

**Use Case Name:** Deleting a job keeps its contacts but clears their job_id (`test_delete_job`)  
**Pre-conditions:** One user, one company, one job, and one contact linked to that job and company  
**Test Steps:**
1. Confirm the contact's job_id matches the job
2. Delete the job
3. Select the contact's job_id and company_id

**Expected Result:** Job is deleted; contact still exists with job_id NULL (SET NULL) and company_id unchanged  
**Actual Result:** Job deleted; contact kept with job_id NULL and the original company_id  
**Status:** Pass

---

## 3) Table: contacts

### Table Description
Stores network contacts that can be associated with specific jobs

### Fields
| Field Name | Type | Description | Constraints |
|---|---|---|---|
| id | INTEGER | auto-incremented id code | PRIMARY KEY (auto-generated) |
| user_id | INTEGER | id of user adding contact | FK → users.id, NOT NULL, ON DELETE CASCADE |
| company_id | INTEGER | id of company contact is from | FK → companies.id, nullable, ON DELETE SET NULL |
| job_id | INTEGER | job associated with contact | FK → jobs.id, nullable, ON DELETE SET NULL |
| name | TEXT | name of contact | NOT NULL |
| title | TEXT | job title of contact | Nullable |
| designation | TEXT | role of contact re. job appication | Nullable, CHECK (recruiter, referrer, interviewer, hiring manager, other) |
| email | TEXT | contact email address | Nullable (not unique) |
| phone | TEXT | contact phone number | Nullable; stored as text to keep +, dashes, parentheses |
| linkedin_url | TEXT | contact LinkedIn link  | Nullable |
| notes | TEXT | space for notes about the contact a user would like to add | Nullable |

### Relationships
- Many-to-one with `users`
- Many-to-one with `companies` (optional; link cleared if the company is deleted)
- Many-to-one with `jobs` (optional; link cleared if the job is deleted)

### Table Tests

All tests are in `test_schema.py` (class `TestContacts`). Each test starts with a fresh database containing one user, one company, and one job at that company.

#### Contacts #1

**Use Case Name:** Insert a valid contact succeeds (`test_insert_valid_contact`)  
**Pre-conditions:** One user, one company, and one job exist  
**Test Steps:**
1. Insert a contact with every column filled in, including phone `+1 (555) 666-7777`
2. Select the contact by id

**Expected Result:** Row exists and every column matches the inserted values; phone keeps its +, spaces, dashes, and parentheses  
**Actual Result:** Row found; all ten values saved unchanged  
**Status:** Pass

#### Contacts #2

**Use Case Name:** Insert contact with missing name fails (`test_insert_contact_missing_name`)  
**Pre-conditions:** One user, one company, and one job exist  
**Test Steps:**
1. Insert a contact with every column except name

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: contacts.name  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Contacts #3

**Use Case Name:** Insert contact with only a name succeeds (`test_insert_contact_missing_nullables`)  
**Pre-conditions:** One user exists  
**Test Steps:**
1. Insert a contact with only user_id and name
2. Select the contact by id

**Expected Result:** Insert succeeds; name is saved; company_id, job_id, title, designation, email, phone, linkedin_url, and notes are all NULL  
**Actual Result:** Row found; name saved; all eight optional columns are NULL  
**Status:** Pass

#### Contacts #4

**Use Case Name:** Insert contact with a company_id that doesn't exist fails (`test_insert_contact_nonexistent_companyid`)  
**Pre-conditions:** One user, one company, and one job exist; no company has id 9999  
**Test Steps:**
1. Insert a contact with company_id 9999

**Expected Result:** `IntegrityError`: FOREIGN KEY constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Contacts #5

**Use Case Name:** Insert contact with a job_id that doesn't exist fails (`test_insert_contact_nonexistent_jobid`)  
**Pre-conditions:** One user, one company, and one job exist; no job has id 9999  
**Test Steps:**
1. Insert a contact with job_id 9999

**Expected Result:** `IntegrityError`: FOREIGN KEY constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Contacts #6

**Use Case Name:** Insert contact with a designation not on the list fails (`test_insert_contact_unlisted_designation`)  
**Pre-conditions:** One user, one company, and one job exist  
**Test Steps:**
1. Insert a contact with designation 'hiring managers' (not on the list)

**Expected Result:** `IntegrityError`: CHECK constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Contacts #7

**Use Case Name:** Two contacts with the same email succeed (`test_insert_contact_duplicate_email`)  
**Pre-conditions:** One user exists  
**Test Steps:**
1. Insert two contacts with different names and the email `recruiting@example.com`
2. Count contacts with that email

**Expected Result:** Both inserts succeed; count is 2  
**Actual Result:** Both inserts succeeded; count is 2  
**Status:** Pass

---

## 4) Table: companies

### Table Description
Stores companies offering jobs in jobs table

### Fields
| Field Name | Type | Description | Constraints |
|---|---|---|---|
| id | INTEGER | auto-incremented id code | PRIMARY KEY (auto-generated) |
| user_id | INTEGER | id of user adding company | FK → users.id, NOT NULL, ON DELETE CASCADE |
| name | TEXT | Company name | NOT NULL; COLLATE NOCASE; UNIQUE together with user_id |
| city | TEXT | City where company is located | Nullable |
| region | TEXT | region where company is located | Nullable; state, province, or country (works for non-US locations) |
| website | TEXT | company website | Nullable |
| notes | TEXT | space for notes about company a user would add | Nullable |

### Relationships
- Many-to-one with `users`
- One-to-many with `contacts` (ON DELETE SET NULL)
- One-to-many with `jobs (ON DELETE NO ACTION)

### Table Tests

All tests are in `test_schema.py` (class `TestCompanies`). Each test starts with a fresh database containing one user.

#### Companies #1

**Use Case Name:** Insert a valid company succeeds (`test_insert_valid_company`)  
**Pre-conditions:** One user exists  
**Test Steps:**
1. Insert a company with every column filled in
2. Select the company by id

**Expected Result:** Row exists and every column matches the inserted values  
**Actual Result:** Row found; all six values saved unchanged  
**Status:** Pass

#### Companies #2

**Use Case Name:** Insert company with missing name fails (`test_insert_company_missing_name`)  
**Pre-conditions:** One user exists  
**Test Steps:**
1. Insert a company with every column except name

**Expected Result:** `IntegrityError`: NOT NULL constraint failed: companies.name  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Companies #3

**Use Case Name:** Insert company with a user_id that doesn't exist fails (`test_insert_company_nonexistent_userid`)  
**Pre-conditions:** One user exists; no user has id 9999  
**Test Steps:**
1. Insert a company with user_id 9999

**Expected Result:** `IntegrityError`: FOREIGN KEY constraint failed  
**Actual Result:** `IntegrityError` raised with the expected message  
**Status:** Pass

#### Companies #4

**Use Case Name:** Insert a company name the same user already has fails, including different case (`test_insert_company_duplicate_name`)  
**Pre-conditions:** The user already has a company named "Black Sabbath"  
**Test Steps:**
1. Insert "Black Sabbath" again for the same user
2. Insert "black sabbath" for the same user
3. Count rows in `companies`

**Expected Result:** Both inserts raise `IntegrityError`: UNIQUE constraint failed; only 1 company remains  
**Actual Result:** Both inserts rejected; company count is 1  
**Status:** Pass

#### Companies #5

**Use Case Name:** Two different users can each have a company with the same name (`test_insert_same_company_multiple_users`)  
**Pre-conditions:** Two users exist  
**Test Steps:**
1. Insert "Black Sabbath" for the first user
2. Insert "Black Sabbath" for the second user
3. Count companies named "Black Sabbath"

**Expected Result:** Both inserts succeed; count is 2  
**Actual Result:** Both inserts succeeded; count is 2  
**Status:** Pass

#### Companies #6

**Use Case Name:** New company gets an auto-generated id (`test_company_generated_id`)  
**Pre-conditions:** Two users exist  
**Test Steps:**
1. Insert two companies for the first user and one for the second, without supplying id
2. Select all company ids

**Expected Result:** Stored ids match the generated ids; each is an integer; all three are unique  
**Actual Result:** Three unique integer ids generated and stored  
**Status:** Pass

#### Companies #7

**Use Case Name:** Deleting a company that still has jobs fails (`test_delete_company_with_jobs`)  
**Pre-conditions:** One user, one company, and one job at that company  
**Test Steps:**
1. Confirm the company and job exist
2. Delete the company
3. Recount the company and its jobs

**Expected Result:** Delete raises `IntegrityError`: FOREIGN KEY constraint failed (NO ACTION); company and job both still exist  
**Actual Result:** Delete blocked; company and job counts are still 1  
**Status:** Pass

#### Companies #8

**Use Case Name:** Deleting a company with contacts (but no jobs) succeeds and clears their company_id (`test_delete_company_with_contacts`)  
**Pre-conditions:** One user, one company, and one contact linked to that company; no jobs  
**Test Steps:**
1. Confirm the contact's company_id matches the company
2. Delete the company
3. Recount the company, user, and contact, and select the contact's company_id

**Expected Result:** Company is deleted; user and contact still exist; contact's company_id is NULL (SET NULL)  
**Actual Result:** Company deleted; user and contact kept; contact's company_id is NULL  
**Status:** Pass


---

# Data Access Methods

<!--
Need at least one per table. Derive them from the user stories:
for each page/story, what query does it run? Each one becomes a method here.
Test each for: normal case, empty case, and "cannot see another user's data".
-->

---

## Access Method: [name]

### Description
[ ]

### Parameters
- [name] ([type])

### Return Values
- [ ]

### Used By
- [Page(s) / user story #]

### Tests

**Use Case Name:** [ ]
**Pre-conditions:** [ ]
**Test Steps:**
1. [ ]

**Expected Result:** [ ]
**Actual Result:** Pending
**Status:** Pending

---

## Access Method: [name]

### Description
[ ]

### Parameters
- [ ]

### Return Values
- [ ]

### Used By
- [ ]

### Tests

**Use Case Name:** [ ]
**Pre-conditions:** [ ]
**Test Steps:**
1. [ ]

**Expected Result:** [ ]
**Actual Result:** Pending
**Status:** Pending

---

# Page-to-Database Mapping

<!-- Coordinate with the Milestone 4 page designs. -->

| Page | Tables Accessed | Access Methods Used |
|---|---|---|
| [Login / Signup] | | |
| [Dashboard] | | |
| [Add / Edit Job] | | |
| [ ] | | |

---

# Page Data Access Tests

**Use Case Name:** [ ]
**Description:** [ ]
**Pre-conditions:** [ ]
**Test Steps:**
1. [ ]

**Expected Result:** [ ]
**Actual Result:** Pending
**Status:** Pending
**Post-conditions:** [ ]

---


