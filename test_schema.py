import sqlite3
import unittest

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
           # test goes here
           pass

    def test_insert_user_missing_name(self):
            # test goes here
            pass

    def test_insert_user_missing_password(self):
            # test goes here
            pass

    def test_insert_user_existing_email(self):
            # test goes here
            pass

    def test_id_timestamp_at_creation(self):
            # test goes here
            pass

    def test_cascade_on_delete_user(self):
            # test goes here
            pass

    def tearDown(self):
           # Close the connection
           self.conn.close()
         
    
if __name__ == "__main__":
    unittest.main()