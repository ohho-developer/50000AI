from django.contrib import admin
from .models import RecipeSearchHistory, FavoriteRecipe


@admin.register(RecipeSearchHistory)
class RecipeSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'query']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'channel_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'title', 'channel_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
