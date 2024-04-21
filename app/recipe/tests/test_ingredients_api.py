"""
Test Ingredients API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredients
from recipe.serializers import IngredientsSerializer

INGREDIENTS_URL = reverse('recipe:ingredients-list')

def detail_url(id):
    """Detail url"""
    return reverse('recipe:ingredients-detail', args=[id])

def create_user(email='test@example.com',password='test123'):
    """Helper functino to create users."""
    return get_user_model().objects.create_user(email, password)

class PublicIngredientsApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def list_ingredients_unauthorized(self):
        """Retrieve a list of ingredients without auth."""
        user = create_user()
        Ingredients.objects.create(user=user, name='col')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_list_ingredients(self):
        """Test listing ingredients with auth."""

        Ingredients.objects.create(user=self.user, name='col')
        Ingredients.objects.create(user=self.user, name='vanilla')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredients.objects.all().order_by('-name')
        serializer = IngredientsSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test retrieving a list of ingredients is limites to auth user."""
        user2 = create_user(email='user2@example.com', password='test1234')
        Ingredients.objects.create(user = user2, name='test')
        ingredient = Ingredients.objects.create(user=self.user, name='goodIngredient')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_updating_ingredients(self):

        ingredient = Ingredients.objects.create(user=self.user, name='vanilla')

        payload ={'name': 'new_name'}

        url = detail_url(ingredient.id)
        res = self.client.patch(url,payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_deleting_ingredien(self):
        """Test for deleteing ingredients."""
        ingredient =Ingredients.objects.create(user=self.user, name='try')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredients.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())




