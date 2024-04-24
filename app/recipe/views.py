"""Views for the recipe APIs."""

from rest_framework import (viewsets, mixins,)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (Recipe, Tag, Ingredients,)
from recipe import serializers

class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes=[TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')

class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes=[TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')
    def get_serializer_class(self):
        """Return the reializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

class TagViewSet(BaseRecipeAttrViewSet):
    """Manage Tag in the database"""
    serializer_class = serializers.TagSerializer
    queryset= Tag.objects.all()


    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')
class IngredientsViewSet(BaseRecipeAttrViewSet):
    """Manage Ingredients in the Database"""
    serializer_class=serializers.IngredientsSerializer
    queryset=Ingredients.objects.all()



