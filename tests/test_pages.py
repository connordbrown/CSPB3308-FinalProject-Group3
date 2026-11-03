import unittest
import os
import sqlite3
import tempfile

from werkzeug.security import generate_password_hash
from app import app
import db
from tests.test_db import USER_A, USER_B, SCHEMA_PATH

USER_C = {
    "first_name": "Henry",
    "last_name": "Case",
    "email": "henry.demo@example.com",
    "password": "DemoPass1234!",
    "display_name": "Case",
    }

class PageTestCase(unittest.TestCase):
    """Base class, sets up temporary db with users  A and B an a test client"""
    def setUp(self):
        # temp db for each test
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        app.config["DATABASE"] = self.db_path
        app.config["TESTING"] = True

        self.conn = db.get_connection(self.db_path)
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())
        self.user_a = self._insert_user(**USER_A)
        self.user_b = self._insert_user(**USER_B)
        self.conn.commit()

        self.client = app.test_client()

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    # ------------------------------------------------------------------
    # Helpers we are re-using from test_db: insert one row with raw SQL and return its id. Pass keyword
    # arguments to override any column; the rest get valid defaults.
    # ------------------------------------------------------------------

    def _insert_user(self, first_name, last_name, email, password, display_name=None):
        # A low-cost hash method
        password_hash = generate_password_hash(password, method="pbkdf2:sha256:1000")
        return self.conn.execute(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first_name, last_name, email, password_hash, display_name),
        ).lastrowid

    def _insert_company(self, user_id, name="Spotify", city=None, region=None,
                        website=None, notes=None):
        return self.conn.execute(
            """
            INSERT INTO companies (user_id, name, city, region, website, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, city, region, website, notes),
        ).lastrowid

    def _insert_job(self, user_id, company_id, title="Software Engineer", status="saved",
                    work_type=None, link=None, notes=None, date_applied=None):
        return self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, status, work_type, link, notes, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, title, status, work_type, link, notes, date_applied),
        ).lastrowid

    def _insert_contact(self, user_id, name="Jordan Rivera", title=None, designation=None,
                        company_id=None, job_id=None, email=None, phone=None,
                        linkedin_url=None, notes=None):
        return self.conn.execute(
            """
            INSERT INTO contacts (user_id, company_id, job_id, name, title, designation,
                                  email, phone, linkedin_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, job_id, name, title, designation,
             email, phone, linkedin_url, notes),
        ).lastrowid

    def _fetch(self, table, row_id):
        """Return one row from `table` by id (or None), read directly without db.py."""
        return self.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()

    def _count(self, table, where="1", params=()):
        """Return the number of rows in `table` matching the WHERE clause."""
        return self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]

    def _login(self, user=USER_A):
        return self.client.post("/login", data={
            "action": "login", "email": user["email"], "password": user["password"]
        })

    def _signup(self, user=USER_C):
        return self.client.post("/login", data={
            "action": "signup", "first_name": user["first_name"], "last_name": user["last_name"], "email": user["email"], "password": user["password"]
        })
    

class TestLogin(PageTestCase):
    """tests for /login """


    # 1. GET /login returns 200 and shows the form with both buttons.
    def test_login_returns_200_and_buttons(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<button type="submit">Log in</button>', html)
        self.assertIn('<button type="submit">Sign up</button>', html)


    # 2. Log in with a valid email and password (e.g., alex.demo@example.com / DemoPass123!) redirects to / and the session holds Alex's user_id.
    def test_valid_login_redirects_and_sets_session(self):
        response = self._login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user_id"), self.user_a)

    
    # 3. Log in with the right email in different case (ALEX.DEMO@example.com) succeeds.
    def test_email_dif_case_works(self):
        response = self._login({**USER_A, "email": USER_A["email"].upper()})
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user_id"), self.user_a)
    
    # 4. Log in with a wrong password stays on /login, shows an error, and creates no session.
    def test_wrong_pass_errors_changes_nothing(self):
        response = self._login({**USER_A, "password": "WrongPassword1"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid login information", response.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))
    
    # 5. Log in with an unknown email gives the same generic error as test 4, so the page doesn't reveal which emails exist.
    def test_unknown_email_doesnt_reveal_data(self):
        response = self._login({**USER_A, "email": "Wrong@email.com"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid login information", response.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))
    
    # 6. Sign up with valid fields creates one new users row, logs the user in, and redirects to /.
    def test_signup_success(self):
        response = self._signup()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (USER_C["email"],)
        ).fetchone()
        self.assertIsNotNone(row)

        # 7. The new row's password_hash is a hash, not the plain password.
        self.assertNotEqual(row["password_hash"], USER_C["password"])


    # 8. Sign up with an email that already exists (including different case) stays on /login, shows an error, and adds no row.
    def test_signup_email_exists(self):
        before = self._count("users")
        response = self._signup({**USER_A, "email": USER_A["email"].upper()})
        self.assertEqual(response.status_code, 409)
        self.assertIn("That account already exists", response.get_data(as_text=True))
        after = self._count("users")
        self.assertEqual(before, after)

    # 9. Sign up with a missing first_name, last_name, or password shows an error and adds no row.
    def test_missing_signup_data(self):
        for field in ("first_name", "last_name", "email", "password"):
            for blank in ("", " ", None):
                with self.subTest(field=field, value=blank):
                    before = self._count("users")
                    response = self._signup({**USER_C, field: blank})
                    self.assertEqual(response.status_code, 400)
                    after = self._count("users")
                    self.assertEqual(before, after)


    # 12. A logged-in user who opens /login is redirected to /.
    def test_logged_in_user_directed_away_from_login(self):
        self._login()
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    # 13. /logout clears the session; the nav bar goes back to its logged-out state.
    def test_logout_succeeds(self):
        response = self.client.get("/logout", follow_redirects=True)
        self.assertIn("Please log in to use Prospex", response.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("user_id"))
            self.assertIsNone(sess.get("first_name"))



class TestProfile(PageTestCase):
    """tests for /profile """

    # 1. Logged in GET for `/profile` returns 200
    def test_profile_returns(self):
        # make sure login works
        login = self._login()
        self.assertEqual(login.status_code, 302)
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<h2>Profile</h2>' , html)

    # 2. Logged out GET or POST does not change db and redirects to `/login`
    def test_logged_out_request_no_change_to_db(self):
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        # check post
        before = dict(self._fetch("users", self.user_a))
        response = self.client.post('/profile', data = {
            "first_name": "bad_name", "last_name": "bad_lastname", "email": "bill@bad.com"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(dict(self._fetch("users", self.user_a)), before)

    # 3. Shows the correct first name, last name and email for the logged in user
    def test_correct_user_info(self):
        login = self._login()
        html = self.client.get("/profile").get_data(as_text=True)
        # check that user a in fields
        self.assertIn(USER_A["email"], html)
        self.assertIn(USER_A["first_name"], html)
        self.assertIn(USER_A["last_name"], html)
        # and not user b
        self.assertNotIn(USER_B["email"], html)


    # 4. password not accessible in html
    def test_password_not_accessible(self):
        login = self._login()
        html = self.client.get("/profile").get_data(as_text=True)
        # check both raw password and hash
        self.assertNotIn(USER_A["password"], html)
        hash = self._fetch("users", self.user_a)["password_hash"]
        self.assertNotIn(hash, html)


    # 5. valid inputs for name, email save to db, redirect to `/profile` and page shows new info
    def test_valid_inputs_save_appropriately(self):
        self._login()
        data = {
            "first_name": USER_C["first_name"], "last_name": USER_C["last_name"], "email": USER_C["email"], "action": "update_user"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profile")
        row = self._fetch("users", self.user_a)
        self.assertEqual(row["first_name"], data["first_name"])
        self.assertEqual(row["last_name"], data["last_name"])
        self.assertEqual(row["email"], data["email"])

        # check that user C in fields
        html = self.client.get("/profile").get_data(as_text=True)
        self.assertIn(USER_C["email"], html)
        self.assertIn(USER_C["first_name"], html)
        self.assertIn(USER_C["last_name"], html)
        # and not user A
        self.assertNotIn(USER_A["email"], html)



    # 6. if any required field is empty on POST, error displayed, nothing saved to db
    def test_error_on_empty_field(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "first_name": USER_C["first_name"], "last_name": USER_C["last_name"], "email": "", "action": "update_user"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(before, dict(self._fetch("users", self.user_a)))

    # 7. email already in use: error displayed, nothing saved even if # 8 different case
    def test_dup_email_error(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "first_name": USER_C["first_name"], "last_name": USER_C["last_name"], "email": USER_B["email"].upper(), "action": "update_user"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 409)

        self.assertEqual(before, dict(self._fetch("users", self.user_a)))

    # 9. changing other fields without changing email does not result in error
    def test_change_fields_independently(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "first_name": USER_C["first_name"], "last_name": USER_C["last_name"], "email": USER_A["email"], "action": "update_user"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 302)

        row = self._fetch("users", self.user_a)
        self.assertEqual(row["first_name"], USER_C["first_name"])
        self.assertEqual(row["last_name"], USER_C["last_name"])
        self.assertEqual(row["email"], USER_A["email"])
    
    # 10. unchanged password results in no changes on save
    def test_same_password_no_change(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "password": USER_A["password"], "new_password": USER_A["password"], "confirmation": USER_A["password"], "action": "change_password"
        }
        response = self.client.post('/profile', data=data)

        after = dict(self._fetch("users", self.user_a))
        # make sure the passwords still match
        self.assertTrue(db.check_password_hash(after["password_hash"], USER_A["password"]))
        # and none of the other columns changed
        before.pop("password_hash")
        after.pop("password_hash")
        self.assertEqual(before, after)


    # 11. matching new passwords result new saved password  with displayed message "password changed"
    def test_change_password_success(self):
        self._login()
        data = {
            "password": USER_A["password"], "new_password": USER_C["password"], "confirmation": USER_C["password"], "action": "change_password"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 302)
        after = dict(self._fetch("users", self.user_a))
        # make sure the password changed successfully
        self.assertTrue(db.check_password_hash(after["password_hash"], USER_C["password"]))


    # 12. wrong current password entered: Error, no change in db
    def test_error_on_wrong_password(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "password": USER_C["password"], "new_password": USER_B["password"], "confirmation": USER_B["password"], "action": "change_password"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 400)
        after = dict(self._fetch("users", self.user_a))
        self.assertEqual(before, after)

    # 13. new and confirmation don't match: Error, no change
    def test_password_no_match(self):
        self._login()
        before = dict(self._fetch("users", self.user_a))
        data = {
            "password": USER_A["password"], "new_password": USER_B["password"], "confirmation": USER_C["password"], "action": "change_password"
        }
        response = self.client.post('/profile', data=data)
        self.assertEqual(response.status_code, 400)
        after = dict(self._fetch("users", self.user_a))
        self.assertEqual(before, after)





class TestDashboard(PageTestCase):
    """tests for '/' """

    # we need job data to display for this:
    def setUp(self):
        super().setUp()
        self.maas = self._insert_company(self.user_a, name="Maas Biolabs")
        self.hosaka = self._insert_company(self.user_a, name = "Hosaka")
        self.tessier = self._insert_company(self.user_a, name= "Tessier-Ashpool")
        self.sense = self._insert_company(self.user_b, name= "Sense/Net")

        # add jobs for user A 
        self.job_1 = self._insert_job(self.user_a, self.tessier, title="AI Security", status="declined")
        self.job_2 = self._insert_job(self.user_a, self.hosaka, title="Firmware Dev", status = "applied")
        # and one for  user B
        self.job_3 = self._insert_job(self.user_b, self.tessier, title="AI Administrator")
        self.conn.commit()

    # 1. User not logged in - redirect to (`/login`).
    def test_login_redirect(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
    

    # 2. Page displays list of all jobs
    def test_jobs_list_shows(self):
        self._login()
        html = self.client.get("/").get_data(as_text=True)
        # check that logged in user A's jobs are showing
        self.assertIn("AI Security", html)
        self.assertIn("Firmware Dev", html)
        # double check that no jobs from other users are showing
        self.assertNotIn("AI Administrator", html)


    # 3. Each job card shows Role, Company, and Status (indicated by color)
    def test_job_cards_accurate(self):
        self._login()
        html = self.client.get("/").get_data(as_text=True)

        # check that logged in user A's jobs are showing
        self.assertIn("AI Security", html)
        self.assertIn("Firmware Dev", html)
        # double check that no jobs from other users are showing
        self.assertNotIn("AI Administrator", html)

    # 4. Filter status selection appears above job list
    #     - Changing filter value updates job list
    def test_filter_selection(self):
        self._login()
        html = self.client.get("/?status=applied").get_data(as_text=True)

        # check that selector appears
        self.assertIn("ALL", html)
        # applied job is showing
        self.assertIn("Firmware Dev", html)
        # declined job is not
        self.assertNotIn("AI Security", html)

    # 5. individual job cards link correctly to their specific job detail page
    def test_jobs_link_to_details(self):
        self._login()
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn(f'href="/jobs/{self.job_1}"', html)
        # make sure the link goes somewhere
        response = self.client.get(f'/jobs/{self.job_1}')
        self.assertEqual(response.status_code, 200)

    # 6. add job button links correctly
    #     - Add Job button displays if job list is empty
    def test_empty_list(self):
        self._insert_user(**USER_C)
        self.conn.commit()
        self._login(USER_C) # no jobs
        html = self.client.get("/").get_data(as_text=True)

        # check that add job button appears
        self.assertIn('href="/jobs/add"', html)
        # make sure the link goes somewhere
        response = self.client.get('/jobs/add')
        self.assertEqual(response.status_code, 200)


    # 7. Navigation / Header - Page should display navigation with project title, links to contacts and profile pages, and a logout button.
    def test_nav(self):
        self._login()
        html = self.client.get("/").get_data(as_text=True)

        # check that project title appears
        self.assertIn("Prospex", html)
        # link to contacts, profile and logout button showing
        self.assertIn("Contacts", html)
        self.assertIn("Profile", html)
        self.assertIn("Log out", html)
        # login not showing for logged in user
        self.assertNotIn("Log in", html)


if __name__ == '__main__':
    unittest.main()