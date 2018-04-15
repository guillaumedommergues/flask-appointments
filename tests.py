import unittest
from my_app import app
import datetime

what = 'Other' # a product in the initial data commit
where = 'Guam' # a market
when = datetime.datetime.now() + datetime.timedelta(days=1)
test_url = what + '/' + where + '/' + when.strftime('%Y-%m-%d')
test_phone_number = '12345678' # your phone number

class BasicTests(unittest.TestCase):

    def test_main_pages(self):
        """ Testing of the customer facing pages. """
        self.app=app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        response=self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        response=self.app.get('/thanks', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        response=self.app.get('/snap', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        response=self.app.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        response=self.app.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        response=self.app.get('/book/' + test_url, follow_redirects=True)
        self.assertEqual(response.status_code,200)

    def test_login(self):
        """ Testing that:
        - the admin user needs to log in
        - the admin user can log in
        - the admin user can change passwords
        - the admin user can change log out

        """
        self.app=app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        # trying invalid login/password combinations
        response = self.app.post(
                '/login',
                data={'email':'admin@example.com'},
                follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('Password not provided',response.data)
        response = self.app.post(
                '/login',
                data={'password':'pwd'},
                follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('Email not provided',response.data)
        # logging in, changing password
        response = self.app.post(
                '/login',
                data={'email':'admin@example.com','password':'pwd'},
                follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('Hi Admin User',response.data)
        response = self.app.post(
               '/change_password',
               data={'user_id':1,
                     'old_pwd':'pwd',
                     'new_pwd_1':'pwd2',
                     'new_pwd_2':'pwd2'},
               follow_redirects=True)
        self.assertEqual(response.status_code,200)        
        response = self.app.post('/logout', follow_redirects=True)
        response = self.app.get('/profile', follow_redirects=True)
        self.assertIn('Please log in to access this page',response.data)
        response = self.app.post(
               '/login',
               data={'email':'admin@example.com','password':'pwd2'},
               follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('Hi Admin User',response.data)
        # resetting the password
        self.app.post(
                '/login',
                data={'email':'admin@example.com','password':'pwd2'},
                follow_redirects=True)
        self.app.post(
               '/change_password',
               data={'user_id':1,
                     'old_pwd':'pwd2',
                     'new_pwd_1':'pwd',
                     'new_pwd_2':'pwd'},
               follow_redirects=True)

    def test_booking(self):
        """ Testing that:
        - the customers can book an appointment
        - the customers can cancel an appointment

        """
        self.app=app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        # # trying book an appointment
        response=self.app.post(
            '/book/' + test_url,
            data={
            'wtf_phone': test_phone_number,
            'wtf_user_id': 3,
            'wtf_time': datetime.datetime.combine(
                when, datetime.time(hour=10)).strftime("%Y-%m-%d-%H:%M:%S"),
            'wtf_date': when.strftime("%Y-%m-%d"),
            'wtf_topic': what,
            'wtf_name': 'test user'
            },
             follow_redirects=True)
        self.assertEqual(response.status_code,200)
        # trying to log in as employee and see appointment
        response = self.app.post(
                '/login',
                data={'email':'john.garapan@example.com','password':'pwd'},
                follow_redirects=True)
        response = self.app.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('booked_by_name="test user"',response.data)
        # trying cancel the appointment
        response=self.app.post(
            '/cancel',
            data={
            'From': '+18083864147',
            'Body': 'no appointment'
            },
             follow_redirects=True)
        self.assertEqual(response.status_code,200)
        # trying to log in as employee and not see appointment any longer
        response = self.app.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('booked_by_name="test user"',response.data)

if __name__ == "__main__":
    unittest.main()

