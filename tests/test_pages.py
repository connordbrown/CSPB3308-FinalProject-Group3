import unittest
import os
import sqlite3
import tempfile

from werkzeug.security import generate_password_hash
from app import app
import db
from tests.test_db import USER_A, USER_B, SCHEMA_PATH, NONEXISTENT_ID

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


class TestJobDetails(PageTestCase):
    """tests for /jobs/<id> """
 
    def setUp(self):
        super().setUp()
        # User A: one fully filled job at a company with a location
        self.company_a = self._insert_company(self.user_a, name="Acme Corp", city="Denver", region="CO")
        self.job_a = self._insert_job(
            self.user_a, self.company_a, title="Junior Backend Developer", status="interviewing",
            work_type="hybrid", link="https://www.acme-example.com/careers/junior-backend",
            notes="Python and Flask stack.", date_applied="2026-09-10")
        # User B: one job
        self.company_b = self._insert_company(self.user_b, name="Beta Ltd")
        self.job_b = self._insert_job(self.user_b, self.company_b, title="Data Analyst")
 
    def _open_job(self, job_id, user=USER_A):
        """Save the test data, log in as `user` and request the job page.
        The data must be committed first: the app reads the file through its own connection."""
        self.conn.commit()
        self._login(user)
        return self.client.get(f"/jobs/{job_id}")

        # 1. A logged-in user opening one of their own jobs gets a 200 and sees the title, company, status, work type, link, and notes.
    def test_owner_sees_job_details(self):
        response = self._open_job(self.job_a)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for expected in ("Junior Backend Developer", "Acme Corp", "Interviewing", "Hybrid",
                         "2026-09-10", "https://www.acme-example.com/careers/junior-backend",
                         "Python and Flask stack."):
            with self.subTest(expected=expected):
                self.assertIn(expected, html)
 
    # 2. A job with linked contacts lists each of them, and each one links to /contacts/<id>.
    def test_linked_contacts_listed_with_links(self):
        first = self._insert_contact(self.user_a, name="Jordan Rivera", job_id=self.job_a, designation="hiring manager")
        second = self._insert_contact(self.user_a, name="Sam Okafor", job_id=self.job_a, title="Software Engineer")
        html = self._open_job(self.job_a).get_data(as_text=True)
        for contact_id, name in ((first, "Jordan Rivera"), (second, "Sam Okafor")):
            with self.subTest(name=name):
                self.assertIn(name, html)
                self.assertIn(f'href="/contacts/{contact_id}"', html)
        self.assertNotIn("No contacts linked", html)

    # 3. A job with no linked contacts shows an empty-contacts message instead of a blank list.
    def test_no_contacts_shows_message(self):
        html = self._open_job(self.job_a).get_data(as_text=True)
        self.assertIn("No contacts linked to this job yet.", html)
 
    # 4. A job with empty optional fields (link, notes, work type, date applied) returns 200 and shows no "None" text.
    def test_empty_optional_fields_show_no_none(self):
        company = self._insert_company(self.user_a, name="Summit Cloud")
        bare_job = self._insert_job(self.user_a, company, title="Support Engineer")
        response = self._open_job(bare_job)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Support Engineer", html)
        self.assertNotIn("None", html)
 
    # 5. A company with no city or region shows just the company name, with no stray comma.
    def test_company_location_shown_when_present(self):
        html = self._open_job(self.job_a).get_data(as_text=True)
        self.assertIn("Denver, CO", html)
 
    def test_company_without_location_has_no_stray_comma(self):
        company = self._insert_company(self.user_a, name="Summit Cloud")
        bare_job = self._insert_job(self.user_a, company, title="Support Engineer")
        html = self._open_job(bare_job).get_data(as_text=True)
        self.assertIn("Summit Cloud", html)
        self.assertNotIn("company-location", html)
        self.assertNotIn("Summit Cloud,", html)
 
    # Only a city or only a region is shown without a comma
    def test_company_with_only_a_city_has_no_stray_comma(self):
        company = self._insert_company(self.user_a, name="Fernhill Studio", city="Toronto")
        job_id = self._insert_job(self.user_a, company, title="Front-End Developer")
        html = self._open_job(job_id).get_data(as_text=True)
        self.assertIn("Toronto", html)
        self.assertNotIn("Toronto,", html)
 
    # 6. A job id that doesn't exist returns 404.
    def test_missing_job_returns_404(self):
        response = self._open_job(NONEXISTENT_ID)
        self.assertEqual(response.status_code, 404)

    # 7. A job owned by another user returns the same 404 and shows none of its data.
    def test_other_users_job_returns_404_and_shows_nothing(self):
        response = self._open_job(self.job_b)  # logged in as user A
        self.assertEqual(response.status_code, 404)
        html = response.get_data(as_text=True)
        self.assertNotIn("Data Analyst", html)
        self.assertNotIn("Beta Ltd", html)
        # The owner can still open it
        self.client = app.test_client()
        self.assertEqual(self._open_job(self.job_b, USER_B).status_code, 200)

    #TODO: specify in schema whether contacts can be shared
    # 8. Contacts belonging to another user never appear, even if a contact row points at this job.
    # def test_other_users_contacts_never_appear(self):
    #     self._insert_contact(self.user_a, name="Jordan Rivera", job_id=self.job_a)
    #     # The schema lets user B's contact point at user A's job
    #     self._insert_contact(self.user_b, name="Priyas Private Contact", job_id=self.job_a)
    #     html = self._open_job(self.job_a).get_data(as_text=True)
    #     self.assertIn("Jordan Rivera", html)
    #     self.assertNotIn("Priyas Private Contact", html)
 
    # 9. A logged-out visitor is redirected to /login.
    def test_logged_out_redirects_to_login(self):
        self.conn.commit()
        response = self.client.get(f"/jobs/{self.job_a}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
 
    # 10. A non-numeric id (e.g., /jobs/abc) returns 404.
    def test_non_numeric_id_returns_404(self):
        self.conn.commit()
        self._login()
        for bad_id in ("abc", "1.5", "-1"):
            with self.subTest(bad_id=bad_id):
                self.assertEqual(self.client.get(f"/jobs/{bad_id}").status_code, 404)

    # 11. The Edit button points to /jobs/<id>/edit for the right job.
    def test_edit_button_points_to_edit_page(self):
        html = self._open_job(self.job_a).get_data(as_text=True)
        self.assertIn(f'href="/jobs/{self.job_a}/edit"', html)
 
    # The Edit page the button points to exists, and also needs a login
    def test_edit_page_requires_login(self):
        response = self.client.get(f"/jobs/{self.job_a}/edit")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
 
    # 12. A job link starting with http:// or https:// opens in a new tab; any other kind of link is not rendered as clickable.
    def test_http_links_open_in_new_tab(self):
        for link in ("https://www.acme-example.com/jobs/1", "http://www.acme-example.com/jobs/1", "HTTPS://WWW.ACME-EXAMPLE.COM/JOBS/1"):
            with self.subTest(link=link):
                job_id = self._insert_job(self.user_a, self.company_a, title="Linked Job", link=link)
                html = self._open_job(job_id).get_data(as_text=True)
                self.assertIn(f'href="{link}"', html)
                self.assertIn('target="_blank"', html)
                self.assertIn('rel="noopener noreferrer"', html)

    def test_other_links_are_not_clickable(self):
        for link in ("javascript:alert(1)", "  javascript:alert(1)", "data:text/html,hi", "ftp://example.com/file"):
            with self.subTest(link=link):
                job_id = self._insert_job(self.user_a, self.company_a, title="Odd Link Job", link=link)
                html = self._open_job(job_id).get_data(as_text=True)
                self.assertNotIn('target="_blank"', html)
                self.assertNotIn('href="javascript', html)
                self.assertNotIn('href="data', html)
                self.assertNotIn('href="ftp', html)
                self.assertIn(link.strip(), html, "The link should still be shown as plain text")
 
    # Text typed by users is escaped, so it cannot add HTML or scripts to the page
    def test_user_text_is_escaped(self):
        job_id = self._insert_job(self.user_a, self.company_a, title="<script>alert(1)</script>",
                                  notes="<b>bold</b>")
        html = self._open_job(job_id).get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertNotIn("<b>bold</b>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
 
    # The page has a way back to the dashboard
    def test_back_to_dashboard_link(self):
        html = self._open_job(self.job_a).get_data(as_text=True)
        self.assertIn("Back to dashboard", html)
 


if __name__ == '__main__':
    unittest.main()