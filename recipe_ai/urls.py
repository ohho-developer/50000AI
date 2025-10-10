from django.urls import path
from . import views
from . import community_views

app_name = 'recipe_ai'

urlpatterns = [
    # 기존 기능
    path('', views.index, name='index'),  # 메인 입력 화면
    path('recommend/', views.recommend_menus, name='recommend'),  # 메뉴 추천 결과
    path('recommend/more/', views.recommend_more_menus, name='recommend_more'),  # 추가 메뉴 추천 (AJAX)
    path('recipes/<str:menu_name>/', views.recipe_list, name='recipe_list'),  # 레시피 목록
    path('api/recipe-videos/', views.get_recipe_videos, name='get_recipe_videos'),  # 레시피 영상 ID 목록 (AJAX)
    path('api/recipe-detail/', views.get_recipe_detail, name='get_recipe_detail'),  # 개별 레시피 상세 (AJAX)
    path('recipe/<str:video_id>/', views.recipe_detail, name='recipe_detail'),  # 레시피 상세
    
    # 즐겨찾기
    path('favorites/', views.favorite_list, name='favorite_list'),  # 즐겨찾기 목록
    path('api/favorite/add/', views.add_favorite, name='add_favorite'),  # 즐겨찾기 추가 (AJAX)
    path('api/favorite/remove/', views.remove_favorite, name='remove_favorite'),  # 즐겨찾기 삭제 (AJAX)
    path('api/favorite/check/', views.check_favorite, name='check_favorite'),  # 즐겨찾기 확인 (AJAX)
    
    # 커뮤니티
    path('community/', community_views.community_list, name='community_list'),
    path('community/<int:post_id>/', community_views.community_detail, name='community_detail'),
    path('community/create/', community_views.community_create, name='community_create'),
    path('community/<int:post_id>/update/', community_views.community_update, name='community_update'),
    path('community/<int:post_id>/delete/', community_views.community_delete, name='community_delete'),
    path('community/<int:post_id>/like/', community_views.community_like, name='community_like'),
    path('community/<int:post_id>/comment/', community_views.comment_create, name='comment_create'),
    path('community/comment/<int:comment_id>/delete/', community_views.comment_delete, name='comment_delete'),
]

