"""
Test for the User API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Creating a user is successful."""
        payload = {
            'email': 'testExample@example.com',
            'password': 'test123',
            'name': 'alfredo',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists(self):

        payload = {
            'email': 'testExample@example.com',
            'password': 'test123',
            'name': 'alfredo',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Error if password is lesser than 5 chars."""
        payload = {
            'email': 'testExample@example.com',
            'password': 'tes',
            'name': 'alfredo',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        """Test if token is created for new users."""
        user_detail = {
            'email': 'testExample@example.com',
            'password': 'test123',
            'name': 'alfredo',
        }
        create_user(**user_detail)
        payload = {
            'email': user_detail['email'],
            'password': user_detail['password'],
        }

        res = self.client.post(TOKEN_URL,payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test return false if credentials invalid"""
        create_user(email = 'test@example.com', password = 'goodpass')
        user_detail = {
            'email': 'testexample@example.com',
            'password': 'badpass',
        }
        res = self.client.post(TOKEN_URL,user_detail)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test return false if pass blank """
        user_detail = {
            'email': 'example@example.com',
            'password': '',
            'name': 'alfredo',
        }
        res = self.client.post(TOKEN_URL,user_detail)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)



class PrivateUserApiTest(TestCase):
    """Test User API for authenticated users."""

    def setUp(self):
        self.user = create_user(
            email= 'textExample@example.com',
            password='test123',
            name= 'testName',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    def test_retrieve_profile_successful(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile with PATCH"""
        payload = {'name': 'Updated name', 'password': 'newpass123'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
