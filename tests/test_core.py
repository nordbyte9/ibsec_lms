from django.test import TestCase
from django.urls import reverse

from tests.utils import create_user


class CoreTests(TestCase):
    def test_home_page_is_accessible(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_user_login(self):
        create_user('testuser', password='password123')
        response = self.client.post('/accounts/login/', {'username': 'testuser', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')
        self.assertTrue('_auth_user_id' in self.client.session)
