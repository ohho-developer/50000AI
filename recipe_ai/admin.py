from django.contrib import admin
from .models import RecipeSearchHistory, FavoriteRecipe, CommunityPost, CommunityComment


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


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'views', 'like_count', 'comment_count', 'has_youtube', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['views', 'created_at', 'updated_at', 'like_count', 'comment_count']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'title', 'content', 'category', 'youtube_url')
        }),
        ('통계', {
            'fields': ('views', 'like_count', 'comment_count'),
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = "좋아요 수"
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = "댓글 수"
    
    def has_youtube(self, obj):
        from django.utils.html import format_html
        if obj.youtube_url:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')
    has_youtube.short_description = "YouTube"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('likes', 'comments')


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post_title', 'content_preview', 'parent_comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__username', 'post__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('post', 'user', 'content', 'parent')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = "게시글"
    
    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content
    content_preview.short_description = "댓글 내용"
    
    def parent_comment(self, obj):
        if obj.parent:
            return f"답글 → {obj.parent.user.username}"
        return "최상위 댓글"
    parent_comment.short_description = "구분"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'post', 'parent')
