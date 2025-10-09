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
    """즐겨찾기한 레시피 (AI 분석 데이터 포함)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    
    # 기본 영상 정보
    video_id = models.CharField(max_length=20, verbose_name='YouTube 비디오 ID')
    title = models.CharField(max_length=200, verbose_name='레시피 제목')
    channel_name = models.CharField(max_length=100, verbose_name='채널명')
    thumbnail_url = models.URLField(verbose_name='썸네일 URL')
    description = models.TextField(blank=True, verbose_name='영상 설명')
    
    # 통계 정보
    view_count = models.IntegerField(default=0, verbose_name='조회수')
    comment_count = models.IntegerField(default=0, verbose_name='댓글수')
    
    # AI 분석 데이터
    comment_summary = models.TextField(blank=True, verbose_name='AI 댓글 요약')
    sentiment_rating = models.IntegerField(default=0, verbose_name='긍부정 평가 (1-5)')
    difficulty_rating = models.IntegerField(default=0, verbose_name='난이도 평가 (1-5)')
    positive_keywords = models.JSONField(default=list, blank=True, verbose_name='긍정 키워드')
    negative_keywords = models.JSONField(default=list, blank=True, verbose_name='부정 키워드')
    
    # 레시피 요약 (선택적)
    recipe_ingredients = models.TextField(blank=True, verbose_name='주요 재료')
    recipe_steps = models.TextField(blank=True, verbose_name='요리 순서')
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='즐겨찾기 추가 시간')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='마지막 업데이트')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'video_id']
        verbose_name = '즐겨찾기 레시피'
        verbose_name_plural = '즐겨찾기 레시피'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
