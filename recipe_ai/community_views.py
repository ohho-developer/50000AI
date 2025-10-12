"""
Recipe AI 커뮤니티 뷰
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import CommunityPost, CommunityComment


def community_list(request):
    """커뮤니티 게시글 목록"""
    category = request.GET.get('category', 'all')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'recent')  # recent, popular, likes
    
    # 기본 쿼리셋
    posts = CommunityPost.objects.select_related('user').annotate(
        comment_count=Count('comments'),
        like_count=Count('likes')
    )
    
    # 카테고리 필터
    if category != 'all':
        posts = posts.filter(category=category)
    
    # 검색 필터
    if search:
        posts = posts.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # 정렬
    if sort == 'popular':
        posts = posts.order_by('-views', '-created_at')
    elif sort == 'likes':
        posts = posts.order_by('-like_count', '-created_at')
    else:  # recent
        posts = posts.order_by('-created_at')
    
    # 페이지네이션 (한 페이지에 15개)
    paginator = Paginator(posts, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category': category,
        'search': search,
        'sort': sort,
        'categories': CommunityPost._meta.get_field('category').choices,
    }
    
    return render(request, 'recipe_ai/community_list.html', context)


def community_detail(request, post_id):
    """커뮤니티 게시글 상세"""
    post = get_object_or_404(
        CommunityPost.objects.select_related('user').annotate(
            comment_count=Count('comments'),
            like_count=Count('likes')
        ),
        id=post_id
    )
    
    # 조회수 증가 (작성자 본인 제외)
    if not request.user.is_authenticated or request.user != post.user:
        post.views += 1
        post.save(update_fields=['views'])
    
    # 댓글 (대댓글 제외, 최상위 댓글만)
    comments = post.comments.filter(parent__isnull=True).select_related(
        'user'
    ).prefetch_related('replies__user').order_by('created_at')
    
    # 사용자가 좋아요를 눌렀는지 확인
    user_liked = False
    if request.user.is_authenticated:
        user_liked = post.likes.filter(id=request.user.id).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'user_liked': user_liked,
    }
    
    return render(request, 'recipe_ai/community_detail.html', context)


@login_required
def community_create(request):
    """커뮤니티 게시글 작성"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'general')
        youtube_url = request.POST.get('youtube_url', '').strip()
        
        if not title or not content:
            messages.error(request, _('제목과 내용을 모두 입력해주세요.'))
            return render(request, 'recipe_ai/community_form.html', {
                'categories': CommunityPost._meta.get_field('category').choices,
                'title': title,
                'content': content,
                'category': category,
                'youtube_url': youtube_url,
            })
        
        post = CommunityPost.objects.create(
            user=request.user,
            title=title,
            content=content,
            category=category,
            youtube_url=youtube_url if youtube_url else None
        )
        
        messages.success(request, _('게시글이 작성되었습니다.'))
        return redirect('recipe_ai:community_detail', post_id=post.id)
    
    context = {
        'categories': CommunityPost._meta.get_field('category').choices,
    }
    return render(request, 'recipe_ai/community_form.html', context)


@login_required
def community_update(request, post_id):
    """커뮤니티 게시글 수정"""
    post = get_object_or_404(CommunityPost, id=post_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'general')
        youtube_url = request.POST.get('youtube_url', '').strip()
        
        if not title or not content:
            messages.error(request, _('제목과 내용을 모두 입력해주세요.'))
            return render(request, 'recipe_ai/community_form.html', {
                'post': post,
                'categories': CommunityPost._meta.get_field('category').choices,
            })
        
        post.title = title
        post.content = content
        post.category = category
        post.youtube_url = youtube_url if youtube_url else None
        post.save()
        
        messages.success(request, _('게시글이 수정되었습니다.'))
        return redirect('recipe_ai:community_detail', post_id=post.id)
    
    context = {
        'post': post,
        'categories': CommunityPost._meta.get_field('category').choices,
    }
    return render(request, 'recipe_ai/community_form.html', context)


@login_required
@require_http_methods(["POST"])
def community_delete(request, post_id):
    """커뮤니티 게시글 삭제"""
    post = get_object_or_404(CommunityPost, id=post_id, user=request.user)
    post.delete()
    messages.success(request, _('게시글이 삭제되었습니다.'))
    return redirect('recipe_ai:community_list')


@login_required
@require_http_methods(["POST"])
def community_like(request, post_id):
    """게시글 좋아요/취소"""
    post = get_object_or_404(CommunityPost, id=post_id)
    
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'like_count': post.likes.count()
    })


@login_required
@require_http_methods(["POST"])
def comment_create(request, post_id):
    """댓글 작성"""
    post = get_object_or_404(CommunityPost, id=post_id)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        messages.error(request, _('댓글 내용을 입력해주세요.'))
        return redirect('recipe_ai:community_detail', post_id=post_id)
    
    parent = None
    if parent_id:
        parent = get_object_or_404(CommunityComment, id=parent_id)
    
    CommunityComment.objects.create(
        post=post,
        user=request.user,
        content=content,
        parent=parent
    )
    
    messages.success(request, _('댓글이 작성되었습니다.'))
    return redirect('recipe_ai:community_detail', post_id=post_id)


@login_required
@require_http_methods(["POST"])
def comment_delete(request, comment_id):
    """댓글 삭제"""
    comment = get_object_or_404(CommunityComment, id=comment_id, user=request.user)
    post_id = comment.post.id
    comment.delete()
    messages.success(request, _('댓글이 삭제되었습니다.'))
    return redirect('recipe_ai:community_detail', post_id=post_id)

