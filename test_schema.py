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

        

        
    def tearDown(self):
        # Close the connection
        self.conn.close()
        pass

    def test_insert_valid_user(self):
        # Your first test goes here
        pass

if __name__ == "__main__":
    unittest.main()