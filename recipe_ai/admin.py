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
    list_display = ['user', 'title', 'channel_name', 'view_count', 'comment_count', 'sentiment_rating', 'difficulty_rating', 'created_at']
    list_filter = ['created_at', 'sentiment_rating', 'difficulty_rating']
    search_fields = ['user__username', 'title', 'channel_name', 'video_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'video_id', 'title', 'channel_name', 'thumbnail_url', 'description')
        }),
        ('통계', {
            'fields': ('view_count', 'comment_count')
        }),
        ('AI 분석', {
            'fields': ('comment_summary', 'sentiment_rating', 'difficulty_rating', 'positive_keywords', 'negative_keywords')
        }),
        ('레시피 정보', {
            'fields': ('recipe_ingredients', 'recipe_steps'),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at')
        }),
    )
