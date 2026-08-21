import unittest
from app import app

class LoginTestCase(unittest.TestCase):
    def setUp(self):

        app.testing = True
        self.client = app.test_client()



    def test_valid_login(self):
        response = self.client.post('/login', data=dict(
            username='admin',
            password='123456'
        ))
        self.assertEqual(response.status_code, 200)

    def test_invalid_password(self):

        response = self.client.post('/login', data=dict(
            username='admin',
            password='mksai'
        ))
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_user(self):
        response = self.client.post('/login', data=dict(
            username='unknown_user',
            password='123456'
        ))
        self.assertEqual(response.status_code, 401)



if __name__ == '__main__':
    unittest.main()