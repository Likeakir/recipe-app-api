"""
Test Recipe Api.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Recipe,Tag,Ingredients)

from recipe.serializers import (RecipeSerializer, RecipeDetailSerializer,IngredientsSerializer)

RECIPES_URL = reverse('recipe:recipe-list')

def create_user(**params):
    return get_user_model().objects.create_user(**params)
def detail_url(recipe_id):
    """Return detailed url with ID"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """Create a return a sample recipe."""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API request."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res= self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client=APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            'otherexample@example.com',
            'password123',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user = self.user)
        serializer = RecipeSerializer(recipes, many= True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe Detail."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'sample Recipe',
            'time_minutes': 5,
            'price': Decimal('5.5')
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe =  Recipe.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link= 'https://example.com/recipe.pdf'
        recipe = create_recipe(user=self.user,title='sample recipe title', link=original_link)

        update = {'title': 'new_title'}
        url = detail_url(recipe.id)

        res = self.client.patch(url, update)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, update['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(self.user, recipe.user)

    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe description.',
        )

        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New Recipe description',
            'time_minutes': 10,
            'price': Decimal('2.5'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.23'),
            'tags': [{'name': 'vancity'}, {'name': 'meat'}]
        }
        res = self.client.post(RECIPES_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
    def test_creating_recipe_with_existing_tags(self):
        """Tewst creating a recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')

        payload = {
            'title': 'Thai prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.23'),
            'tags': [{'name': 'Indian'}, {'name': 'meat'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(tag_indian,recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_when_update(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        update = {'tags': [{'name': 'newTag'}]}

        detailed_url = detail_url(recipe.id)
        res = self.client.patch(detailed_url, update, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag= Tag.objects.get(user=self.user, name='newTag')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        spanish_tag = Tag.objects.create(user=self.user, name='OleOle')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(spanish_tag)

        new_tag= Tag.objects.create(user=self.user, name='newTag')
        update = {'tags': [{'name': 'newTag'}]}
        detailed_url = detail_url(recipe.id)
        res = self.client.patch(detailed_url, update, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_tag, recipe.tags.all())
        self.assertNotIn(spanish_tag, recipe.tags.all())

    def test_clear_recipes_tag(self):
        spanish_tag = Tag.objects.create(user=self.user, name='OleOle')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(spanish_tag)

        update = {'tags': []}
        detailed_url = detail_url(recipe.id)
        res = self.client.patch(detailed_url, update, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            'title': 'Thai prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.23'),
            'ingredients': [{'name': 'prawns'}, {'name': 'curry'}]
        }
        res = self.client.post(RECIPES_URL,payload,format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        for ingredient in payload['ingredients']:
            exists = recipe.ingredient.filter(
                name = ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test createinf a recipe with existing ingredients."""
        ingredient = Ingredients.objects.create(user=self.user, name='vanilla')

        payload = {
            'title': 'Thai prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.23'),
            'ingredients': [{'name': 'vanilla'}, {'name': 'kurkuma'}]
         }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredient.count(),2)
        self.assertIn(ingredient, recipe.ingredient.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredient.filter(
                name = ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient whrn updating a recipe"""
        recipe = Recipe.objects.create(user = self.user)
        payload = {'ingredients': [{'name':"vanilla"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url,payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = Ingredients.objects.get(user=self.user, name='vanilla')
        self.assertIn(ingredients, recipe.ingredient.all())

    def test_update_recipe_assign_ingredient(self):
        ingredient1 = Ingredients.objects.create(user=self.user,name='chili')
        recipe = create_recipe(user=self.user)
        recipe.ingredient.add(ingredient1)

        ingredient2 = Ingredients.objects.create(user=self.user,name='chili')
        payload = {'ingredients': [{'name': 'chili'}]}
        urls = detail_url(recipe.id)
        res = self.client.patch(urls,payload,format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredient.all())
        self.assertNotIn(ingredient1, recipe.ingredient.all())




