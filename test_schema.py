import sqlite3
import unittest

class DatabaseTestCase(unittest.TestCase):
     def setUp(self):
        # Connect to a fresh in-memory database
        self.conn = sqlite3.connect(":memory:")
    
        # Turn on foreign keys (PRAGMA)
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Read schema.sql and run it with executescript
        with open("schema.sql") as f:
            schema = f.read()
        self.conn.executescript(schema)

     def _insert_default_user(self, email="ozzy@example.com"):
         user_id = self.conn.execute(
              """
              INSERT INTO users (first_name, last_name, email, password_hash, display_name) 
              VALUES (?, ?, ?, ?, ?)
              """,
             ("John", "Osbourne", email, "fakehash1234", "Ozzy")
            ).lastrowid
         return user_id

     def _insert_default_company(self, user_id, name="Black Sabbath"):
         company_id = self.conn.execute(
                 """
              INSERT INTO companies (user_id, name, city, region, website, notes)
              VALUES (?, ?, ?, ?, ?, ?)
              """, 
             (user_id, name, "Birmingham", "UK", "blacksabbath.com", "Forever # 1" )
            ).lastrowid
         return company_id

     def _insert_default_job(self, user_id, company_id):
         job_id = self.conn.execute(
                 """INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                 """, 
                (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                ).lastrowid
         return job_id 

     def _insert_default_contact(self, user_id, company_id=None, job_id=None):
         contact_id = self.conn.execute(
                 """
                 INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                 """,
                (user_id, company_id, job_id, "Geezer Butler", "Bassist", "hiring manager", "geezer@example.com", "555-666-7777", "https://linkedin.com/in/geezerbutler", "Some notes" )
                ).lastrowid
         return contact_id

     def tearDown(self):
           # Close the connection
           self.conn.close()

class TestUsers(DatabaseTestCase): 
    ## Tests for users table
        
   

    def test_insert_valid_user(self):
        self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("John", "Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy")
        )
        row = self.conn.execute("SELECT first_name, last_name, email, password_hash, display_name FROM users WHERE email = 'ozzy@example.com'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "John", "first_name not saved")
        self.assertEqual(row[1], "Osbourne", "last_name not saved")
        self.assertEqual(row[2], "ozzy@example.com", "email not saved")
        self.assertEqual(row[3], "fakehash1234", "password_hash not saved")
        self.assertEqual(row[4], "Ozzy", "display_name not saved")


    def test_insert_user_missing_email(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (first_name, last_name, password_hash, display_name) VALUES (?, ?, ?, ?)", ("John", "Osbourne", "fakehash1234", "Ozzy"))
           

    def test_insert_user_missing_name(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?)", ("Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy"))

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (first_name, email, password_hash, display_name) VALUES (?, ?, ?, ?)", ("John", "ozzy@example.com", "fakehash1234", "Ozzy"))
        

    def test_insert_user_missing_password(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (first_name, last_name, email, display_name) VALUES (?, ?, ?, ?)", ("John", "Osbourne", "ozzy@example.com", "Ozzy"))
            

    def test_insert_user_existing_email(self):
        self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("John", "Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy")
                    )

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("Ian", "Kilmister", "ozzy@example.com", "fakehash4321", "Lemmy"))

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("Ian", "Kilmister", "Ozzy@example.com", "fakehash4321", "Lemmy"))
            

    def test_id_timestamp_at_creation(self):
            self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("John", "Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy"))
            self.conn.execute("INSERT INTO users (first_name, last_name, email, password_hash, display_name) VALUES (?, ?, ?, ?, ?)", ("Ian", "Kilmister", "lemmy@example.com", "fakehash4321", "Lemmy"))
            row_1 = self.conn.execute("SELECT id, created_at FROM users WHERE email = 'ozzy@example.com'").fetchone()
            row_2 = self.conn.execute("SELECT id, created_at FROM users WHERE email = 'lemmy@example.com'").fetchone()

            self.assertIsNotNone(row_1[0], "user_id not generated")
            self.assertIsNotNone(row_1[0], "user_id not generated")
            self.assertIsInstance(row_1[0], int, "user_id must be type int")
            self.assertIsInstance(row_2[0], int, "user_id must be type int")


            self.assertIsNotNone(row_1[1], "created_at timestamp not generated")
            self.assertIsNotNone(row_2[1], "created_at timestamp not generated")
            self.assertRegex(row_1[1], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
            self.assertRegex(row_2[1], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


            self.assertNotEqual(row_1[0], row_2[0], "same user_id generated for separate profiles")

            

    def test_cascade_on_delete_user(self):

            #creates all four interconnected tables
            user_id = self.conn.execute(
                 """
                 INSERT INTO users (first_name, last_name, email, password_hash, display_name) 
                 VALUES (?, ?, ?, ?, ?)
                 """, 
                ("John", "Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy")
                ).lastrowid          

            company_id = self.conn.execute(
                 """
                 INSERT INTO companies (user_id, name, city, region, website, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, 
                (user_id, "Black Sabbath", "Birmingham", "UK", "blacksabbath.com", "Forever # 1" )
                ).lastrowid            

            job_id = self.conn.execute(
                 """INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                 """, 
                (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                ).lastrowid
            

            contact = self.conn.execute(
                 """
                 INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                 """,
                (user_id, company_id, job_id, "Geezer Butler", "Bassist", "hiring manager", "geezer@example.com", "555-666-7777", "https://linkedin.com/in/geezerbutler", "Some notes" )
                ).lastrowid

            #Check that there is one user asocciated with one of each table
            user_count = self.conn.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,)).fetchone()[0]
            company_count = self.conn.execute("SELECT COUNT(*) FROM companies WHERE user_id = ?", (user_id,)).fetchone()[0]
            job_count = self.conn.execute("SELECT COUNT(*) FROM jobs WHERE user_id = ?", (user_id,)).fetchone()[0]
            contact_count = self.conn.execute("SELECT COUNT(*) FROM contacts WHERE user_id = ?", (user_id,)).fetchone()[0]

            self.assertEqual(user_count, 1)
            self.assertEqual(company_count, 1)
            self.assertEqual(job_count, 1)
            self.assertEqual(contact_count, 1)

            #delete user
            self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.assertEqual(user_count, 1)
            self.assertEqual(company_count, 1)
            self.assertEqual(job_count, 1)
            self.assertEqual(contact_count, 1)
            

class TestJobs(DatabaseTestCase):
## Tests for jobs table

    def test_insert_valid_job(self):
         user_id = self._insert_default_user()
         company_id = self._insert_default_company(user_id=user_id)
         job_id = self.conn.execute(
                 """INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                 """, 
                (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                ).lastrowid
         
         row = self.conn.execute(
            """
            SELECT user_id, company_id, title, link, work_type, notes, status, date_applied 
            FROM jobs
            WHERE id = ?
            """, (job_id,)).fetchone()
         
         self.assertIsNotNone(row)
         self.assertEqual(row[0], user_id, "user_id not saved")
         self.assertEqual(row[1], company_id, "company_id not saved")
         self.assertEqual(row[2], "Singer", "title not saved" )
         self.assertEqual(row[3], "https://fakelink.blacksabbath.com", "link not saved" )
         self.assertEqual(row[4], "in person", "work_type not saved")
         self.assertEqual(row[5], "Singer wanted", "notes not saved")
         self.assertEqual(row[6], "applied", "status not saved")
         self.assertEqual(row[7], "1968-01-01", "date_applied not saved")


    def test_insert_job_nonexistent_userid(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.conn.execute(
                """
                INSERT INTO jobs
                (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?,?, ?, ?, ?, ?, ?, ?)
                """,
                (9999, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                )
    
        

    def test_insert_job_missing_title(self):
         user_id = self._insert_default_user()
         company_id = self._insert_default_company(user_id=user_id)
         with self.assertRaises(sqlite3.IntegrityError):
              self.conn.execute(
                   """
                   INSERT INTO jobs
                   (user_id, company_id, link, work_type, notes, status, date_applied)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   """,
                   (user_id, company_id, "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                   )

        

    def test_insert_job_missing_companyid(self):
         user_id = self._insert_default_user()
         with self.assertRaises(sqlite3.IntegrityError):
              self.conn.execute(
                   """
                   INSERT INTO jobs
                   (user_id, title, link, work_type, notes, status, date_applied)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   """,
                   (user_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                   )

    def test_insert_job_nonexistent_companyid(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.conn.execute(
                """
                INSERT INTO jobs
                (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?,?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, 9999, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "applied", "1968-01-01")
                )

    def test_insert_job_default_status(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self.conn.execute(
            """
            INSERT INTO jobs
            (user_id, company_id, title, link, work_type, notes, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "1968-01-01")
            ).lastrowid
        row = self.conn.execute(
            """
            SELECT status 
            FROM jobs
            WHERE id = ?
            """, (job_id,)).fetchone()
        
        self.assertEqual(row[0], "saved" )
        
            

    def test_insert_job_unlisted_status(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK"):
            self.conn.execute(
                """
                INSERT INTO jobs
                (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?,?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in person", "Singer wanted", "appiled", "1968-01-01") #added typo to status
                )

    def test_insert_job_unlisted_worktype(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK"):
            self.conn.execute(
                """
                INSERT INTO jobs
                (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?,?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com", "in persone", "Singer wanted", "applied", "1968-01-01") #added typo to worktype
                )

    def test_insert_job_missing_nullable_fields(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self.conn.execute(
            """INSERT INTO jobs (user_id, company_id, title, status) 
            VALUES (?, ?, ?, ?)
            """, 
            (user_id, company_id, "Singer",  "applied")
            ).lastrowid
         
        row = self.conn.execute(
            """
            SELECT * 
            FROM jobs
            WHERE id = ?
            """, (job_id,)).fetchone()
         
        self.assertIsNotNone(row)

    
    def test_delete_job(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)
        contact_id = self._insert_default_contact(user_id=user_id, company_id=company_id, job_id=job_id)

        row = self.conn.execute(
            """
            SELECT job_id
            FROM contacts
            WHERE id = ?
            """, (contact_id,)
        ).fetchone()

        #check that job_id is properly associated with contact
        self.assertEqual(row[0], job_id)

        #delete job
        self.conn.execute(
            """
            DELETE
            FROM jobs
            WHERE id = ?
            """, (job_id,)
        )
        # select fresh rows
        job_row = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM jobs
            """
        ).fetchone()
        contact_row = self.conn.execute(
                    """
                    SELECT job_id, company_id
                    FROM contacts
                    WHERE id = ?
                    """, (contact_id,)
                ).fetchone()

        self.assertEqual(job_row[0], 0, "job not deleted")
        self.assertIsNotNone(contact_row, "contact deleted with job")
        self.assertIsNone(contact_row[0])
        self.assertEqual(contact_row[1], company_id, "company_id affected by job deletion")


class TestContacts(DatabaseTestCase): 
    ## Tests for contacts table
        
    def test_insert_valid_contact(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)
        contact_id = self.conn.execute(
             """
             INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             """,
             (user_id, company_id, job_id, "Geezer Butler", "Bassist", "hiring manager", "geezer@example.com", "555-666-777", "https://linkedin.com/in/geezerbutler", "Some notes")
             ).lastrowid

        row = self.conn.execute(
            """   
            SELECT user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes
            FROM contacts
            WHERE id = ?
            """, (contact_id,)).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], user_id, "uset_id not saved")
        self.assertEqual(row[1], company_id, "company_id not saved" )
        self.assertEqual(row[2], job_id, "job_id not saved")
        self.assertEqual(row[3], "Geezer Butler", "name not saved")
        self.assertEqual(row[4], "Bassist", "title not saved")
        self.assertEqual(row[5], "hiring manager", "designation not saved")
        self.assertEqual(row[6], "geezer@example.com", "email not saved")
        self.assertEqual(row[7], "555-666-777", "phone number not saved")
        self.assertEqual(row[8], "https://linkedin.com/in/geezerbutler", "linkedin_url not saved")
        self.assertEqual(row[9], "Some notes", "notes not saved")

    def test_insert_contact_missing_name(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)
        with self.assertRaises(sqlite3.IntegrityError):
             self.conn.execute(
             """
             INSERT INTO contacts (user_id, company_id, job_id, title, designation, email, phone, linkedin_url, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
             """,
             (user_id, company_id, job_id, "Bassist", "hiring manager", "geezer@example.com", "555-666-777", "https://linkedin.com/in/geezerbutler", "Some notes")
             )

    def test_insert_contact_missing_nullables(self):
        user_id = self._insert_default_user()    
        contact_id = self.conn.execute(
            """
            INSERT INTO contacts (user_id, name)
            VALUES (?, ?)
            """,
            (user_id, "Geezer Butler")
            )
        row = (
             """
             SELECT * 
             FROM contacts
             WHERE id = ?
             """, (contact_id,)
        )
        self.assertIsNotNone(row)


    def test_insert_contact_nonexistent_companyid(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)

        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
             self.conn.execute(
             """
             INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             """,
             (user_id, 9999, job_id, "Geezer Butler", "Bassist", "hiring manager", "geezer@example.com", "555-666-777", "https://linkedin.com/in/geezerbutler", "Some notes")
             )
             


    def test_insert_conatact_nonexsitent_jobid(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)

        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
             self.conn.execute(
             """
             INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             """,
             (user_id, company_id, 9999, "Geezer Butler", "Bassist", "hiring manager", "geezer@example.com", "555-666-777", "https://linkedin.com/in/geezerbutler", "Some notes")
             )

    def test_insert_contact_unlisted_designation(self):
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)

        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK"):
             self.conn.execute(
             """
             INSERT INTO contacts (user_id, company_id, job_id, name, title, designation, email, phone, linkedin_url, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             """,
             (user_id, company_id, job_id, "Geezer Butler", "Bassist", "hiring managers", "geezer@example.com", "555-666-777", "https://linkedin.com/in/geezerbutler", "Some notes") #typo to designation
             )

    def test_insert_contact_duplicate_email(self):
        user_id = self._insert_default_user()
        self.conn.execute(
            "INSERT INTO contacts (user_id, name, email) VALUES (?, ?, ?)",
            (user_id, "Geezer Butler", "recruiting@example.com"))

        self.conn.execute(
            "INSERT INTO contacts (user_id, name, email) VALUES (?, ?, ?)",
            (user_id, "Tony Iommi", "recruiting@example.com"))

        count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE email = "recruiting@example.com"
            """
        ).fetchone()[0]

        self.assertEqual(count, 2)
        

     
    
if __name__ == "__main__":
    unittest.main()