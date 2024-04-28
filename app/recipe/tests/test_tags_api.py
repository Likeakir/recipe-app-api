"""
Tests for the tags API.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Tag,Recipe)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """Create and returnb a tag detail URL"""
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='test@example.com', password='test123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicTagsApiTests(TestCase):
    """Test unauthenticates API"""

    def setUp(self):
        self.client = APIClient()

    def test_tag_list_not_authenticated(self):
        """Test error when not authenticated"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """Test authenticated Api requests."""

    def setUp(self):
        self.client= APIClient()
        self.user= create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        Tag.objects.create(name='fruity', user= self.user)
        Tag.objects.create(name='vegan', user= self.user)

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated Users."""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='vegan')
        tag = Tag.objects.create(user=self.user, name='fruity')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'],tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user = self.user, name='vegan')

        payload = {'name': 'dessert'}

        detailed_url = detail_url(tag.id)
        res = self.client.patch(detailed_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = Tag.objects.create(user = self.user, name='vegan')

        detailed_url = detail_url(tag.id)
        res = self.client.delete(detailed_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        """Test listing ingredients by those asssigned to reciipes"""
        in1 = Tag.objects.create(user=self.user, name='Apple')
        in2 = Tag.objects.create(user=self.user, name='Pera')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('5.50'),
            user=self.user,
        )
        recipe.tags.add(in1)
        res = self.client.get(TAGS_URL, {'assigned_only':1})

        s1 = TagSerializer(in1)
        s2 = TagSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients return a uniqye list"""
        ing = Tag.objects.create(user=self.user, name='eggs')
        Tag.objects.create(user=self.user, name='herbs')
        recipe1 = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('5.50'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=5,
            price=Decimal('5.50'),
            user=self.user,
        )
        recipe1.tags.add(ing)
        recipe2.tags.add(ing)

        res =self.client.get(TAGS_URL, {'assigned_only':1})

        self.assertEqual(len(res.data),1)
