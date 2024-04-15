"""
Serializer for recipes.
"""
from rest_framework import serializers

from core.models import Recipe
class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']

    def create(self, **recipe_data):
        print('hola')