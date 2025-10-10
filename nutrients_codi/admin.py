from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Profile, Food, FoodLog, CommunityPost, CommunityComment

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'age_display', 'height', 'weight', 'bmi_display', 'daily_calories', 'created_at']
    list_filter = ['gender', 'goal', 'activity_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'bmi_display', 'age_display']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'gender', 'birth_date', 'height', 'weight')
        }),
        ('목표 설정', {
            'fields': ('goal', 'activity_level')
        }),
        ('권장 섭취량', {
            'fields': ('daily_calories', 'daily_protein', 'daily_carbs', 'daily_fat'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def age_display(self, obj):
        if obj.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
            return f"{age}세"
        return "-"
    age_display.short_description = "나이"
    
    def bmi_display(self, obj):
        if obj.height and obj.weight:
            bmi = obj.weight / ((obj.height / 100) ** 2)
            if bmi < 18.5:
                color = "blue"
                status = "저체중"
            elif bmi < 23:
                color = "green"
                status = "정상"
            elif bmi < 25:
                color = "orange"
                status = "과체중"
            else:
                color = "red"
                status = "비만"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color, round(bmi, 1), status
            )
        return "-"
    bmi_display.short_description = "BMI"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'calories', 'protein', 'carbs', 'fat', 'has_embedding', 'created_at']
    list_filter = ['category', 'subcategory', 'source', 'created_at']
    search_fields = ['name', 'food_code', 'category', 'subcategory']
    readonly_fields = ['created_at', 'updated_at', 'embedding_preview']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'food_code', 'category', 'subcategory', 'source')
        }),
        ('기본 영양소', {
            'fields': ('calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium'),
            'classes': ('collapse',)
        }),
        ('미네랄', {
            'fields': ('potassium', 'calcium', 'iron', 'magnesium', 'phosphorus', 'zinc', 'copper', 'manganese', 'selenium'),
            'classes': ('collapse',)
        }),
        ('비타민', {
            'fields': ('vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6', 'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'folate', 'choline'),
            'classes': ('collapse',)
        }),
        ('지방산', {
            'fields': ('cholesterol', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat', 'omega3', 'omega6', 'trans_fat'),
            'classes': ('collapse',)
        }),
        ('기타', {
            'fields': ('caffeine', 'alcohol', 'water', 'ash'),
            'classes': ('collapse',)
        }),
        ('AI 임베딩', {
            'fields': ('embedding', 'embedding_preview'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_embedding(self, obj):
        # VectorField는 None 체크만 가능 (배열 truth value 에러 방지)
        if obj.embedding is not None:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_embedding.short_description = "임베딩"
    
    def embedding_preview(self, obj):
        # VectorField는 None 체크만 가능
        if obj.embedding is not None:
            try:
                # VectorField는 이미 리스트/배열로 반환됨 (JSON 파싱 불필요)
                embedding_data = list(obj.embedding)
                if len(embedding_data) > 0:
                    preview = embedding_data[:5]  # 처음 5개 값만 표시
                    return format_html(
                        '<div style="font-family: monospace; background: #f5f5f5; padding: 5px; border-radius: 3px;">'
                        '차원: {}<br/>'
                        '미리보기: [{}...]'
                        '</div>',
                        len(embedding_data),
                        ', '.join([f'{x:.4f}' for x in preview])
                    )
            except:
                pass
        return "임베딩 없음"
    embedding_preview.short_description = "임베딩 미리보기"

@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'food', 'quantity', 'meal_type', 'consumed_date', 'total_calories']
    list_filter = ['meal_type', 'consumed_date']
    search_fields = ['user__username', 'food__name', 'original_text']
    readonly_fields = ['consumed_at', 'consumed_date', 'total_calories', 'total_protein', 'total_carbs', 'total_fat']
    date_hierarchy = 'consumed_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'food', 'quantity', 'meal_type', 'consumed_date')
        }),
        ('AI 분석 정보', {
            'fields': ('original_text', 'ai_analysis'),
            'classes': ('collapse',)
        }),
        ('총 영양소 (수량 × 단위 영양소)', {
            'fields': ('total_calories', 'total_protein', 'total_carbs', 'total_fat'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('consumed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'food')

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'views', 'like_count', 'comment_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['views', 'created_at', 'updated_at', 'like_count', 'comment_count']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'title', 'content', 'category')
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


# Admin 사이트 설정
admin.site.site_header = "칼로리코디 관리자"
admin.site.site_title = "칼로리코디"
admin.site.index_title = "관리자 대시보드"
