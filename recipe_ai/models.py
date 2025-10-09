from django.db import models
from django.contrib.auth.models import User


class RecipeSearchHistory(models.Model):
    """사용자 검색 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_searches')
    query = models.TextField(verbose_name='검색 키워드')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='검색 시간')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '레시피 검색 기록'
        verbose_name_plural = '레시피 검색 기록'
    
    def __str__(self):
        return f"{self.user.username} - {self.query[:30]}"


class FavoriteRecipe(models.Model):
    """즐겨찾기한 레시피"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    video_id = models.CharField(max_length=20, verbose_name='YouTube 비디오 ID')
    title = models.CharField(max_length=200, verbose_name='레시피 제목')
    channel_name = models.CharField(max_length=100, verbose_name='채널명')
    thumbnail_url = models.URLField(verbose_name='썸네일 URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='즐겨찾기 추가 시간')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'video_id']
        verbose_name = '즐겨찾기 레시피'
        verbose_name_plural = '즐겨찾기 레시피'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
