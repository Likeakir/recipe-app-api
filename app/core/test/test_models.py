"""
Test for Model
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(**params):
    return get_user_model().objects.create_user(**params)



class ModelTests(TestCase):
    """Test Models."""
    def test_create_user_with_email_succesful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test e,ail is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email,expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)
    def test_new_user_without_email_raises_error(self):
        """Test that creatinf a user without an email raises a ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test123')
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_Recipe(self):
        """Test creating a recipe API model."""
        user = get_user_model().objects.create_user(email='test@example.com',password='pass123', name='hola')

        recipe = models.Recipe.objects.create(
            user=user,
            title='test title',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )

        tag = models.Tag.objects.create(user=user, name='Tag1')
        ingridient = models.Ingredients.objects.create(user=user, name='Kurkuma')

        self.assertEqual(str(tag),tag.name)
        self.assertEqual(str(ingridient),ingridient.name)


