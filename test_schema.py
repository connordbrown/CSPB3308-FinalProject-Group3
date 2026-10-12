import sqlite3
import unittest
from datetime import datetime


class TestUsers(unittest.TestCase):

    def setUp(self):
        # Connect to a fresh in-memory database
        self.conn = sqlite3.connect(":memory:")
    
        # Turn on foreign keys (PRAGMA)
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Read schema.sql and run it with executescript
        with open("schema.sql") as f:
            schema = f.read()
        self.conn.executescript(schema)

        
## Tests for Users table
        
   

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
            # test goes here
            pass

    def tearDown(self):
           # Close the connection
           self.conn.close()
         
    
if __name__ == "__main__":
    unittest.main()