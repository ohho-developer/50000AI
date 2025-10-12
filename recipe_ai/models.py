from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class RecipeSearchHistory(models.Model):
    """사용자 검색 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_searches')
    query = models.TextField(verbose_name=_('검색 키워드'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('검색 시간'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('레시피 검색 기록')
        verbose_name_plural = _('레시피 검색 기록')
    
    def __str__(self):
        return f"{self.user.username} - {self.query[:30]}"


class FavoriteRecipe(models.Model):
    """즐겨찾기한 레시피 (AI 분석 데이터 포함)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    
    # 기본 영상 정보
    video_id = models.CharField(max_length=20, verbose_name=_('YouTube 비디오 ID'))
    title = models.CharField(max_length=200, verbose_name=_('레시피 제목'))
    channel_name = models.CharField(max_length=100, verbose_name=_('채널명'))
    thumbnail_url = models.URLField(verbose_name=_('썸네일 URL'))
    description = models.TextField(blank=True, verbose_name=_('영상 설명'))
    
    # 통계 정보
    view_count = models.IntegerField(default=0, verbose_name=_('조회수'))
    comment_count = models.IntegerField(default=0, verbose_name=_('댓글수'))
    
    # AI 분석 데이터
    comment_summary = models.TextField(blank=True, verbose_name=_('AI 댓글 요약'))
    sentiment_rating = models.IntegerField(default=0, verbose_name=_('긍부정 평가 (1-5)'))
    difficulty_rating = models.IntegerField(default=0, verbose_name=_('난이도 평가 (1-5)'))
    positive_keywords = models.JSONField(default=list, blank=True, verbose_name=_('긍정 키워드'))
    negative_keywords = models.JSONField(default=list, blank=True, verbose_name=_('부정 키워드'))
    
    # 레시피 요약 (선택적)
    recipe_ingredients = models.TextField(blank=True, verbose_name=_('주요 재료'))
    recipe_steps = models.TextField(blank=True, verbose_name=_('요리 순서'))
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('즐겨찾기 추가 시간'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('마지막 업데이트'))
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'video_id']
        verbose_name = _('즐겨찾기 레시피')
        verbose_name_plural = _('즐겨찾기 레시피')
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class CommunityPost(models.Model):
    """AI 레시피 추천 커뮤니티 게시글"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_posts')
    title = models.CharField(max_length=200, verbose_name=_('제목'))
    content = models.TextField(verbose_name=_('내용'))
    
    # 카테고리
    category = models.CharField(max_length=50, choices=[
        ('recipe', _('레시피 공유')),
        ('question', _('질문')),
        ('review', _('요리 후기')),
        ('tip', _('요리 팁')),
        ('general', _('자유게시판')),
    ], default='general', verbose_name=_('카테고리'))
    
    # 통계
    views = models.IntegerField(default=0, verbose_name=_('조회수'))
    likes = models.ManyToManyField(User, related_name='recipe_liked_posts', blank=True, verbose_name=_('좋아요'))
    
    # YouTube 영상 링크 (선택사항)
    youtube_url = models.URLField(null=True, blank=True, verbose_name=_('YouTube 링크'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('작성일'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('수정일'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('커뮤니티 게시글')
        verbose_name_plural = _('커뮤니티 게시글')
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-views']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_likes_count(self):
        return self.likes.count()
    
    def get_comments_count(self):
        return self.comments.count()


class CommunityComment(models.Model):
    """AI 레시피 추천 커뮤니티 댓글"""
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments', verbose_name=_('게시글'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_comments', verbose_name=_('작성자'))
    content = models.TextField(verbose_name=_('댓글 내용'))
    
    # 대댓글 (선택사항)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name=_('상위 댓글'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('작성일'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('수정일'))
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('커뮤니티 댓글')
        verbose_name_plural = _('커뮤니티 댓글')
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}의 댓글 - {self.post.title}"
