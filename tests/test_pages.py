import unittest
from app import app

class Page_Tests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True # so that our tests fail loudly
        self.client = app.test_client()


    def check_page_loads(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_pages_load(self):
        urls = ["/", "/login", "/contacts", "/contacts/add", "/contacts/1", "/user/John_Doe", "/jobs/add", "/jobs/1", 
                "jobs/THIS SHOULD FAIL"]   # added just to make sure it fails appropriately.
        for url in urls:
            with self.subTest(url=url):
                self.check_page_loads(url)

        

if __name__ == '__main__':
    unittest.main()