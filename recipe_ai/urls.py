from django.urls import path
from . import views

app_name = 'recipe_ai'

urlpatterns = [
    path('', views.index, name='index'),  # 메인 입력 화면
    path('recommend/', views.recommend_menus, name='recommend'),  # 메뉴 추천 결과
    path('recommend/more/', views.recommend_more_menus, name='recommend_more'),  # 추가 메뉴 추천 (AJAX)
    path('recipes/<str:menu_name>/', views.recipe_list, name='recipe_list'),  # 레시피 목록
    path('api/recipe-videos/', views.get_recipe_videos, name='get_recipe_videos'),  # 레시피 영상 ID 목록 (AJAX)
    path('api/recipe-detail/', views.get_recipe_detail, name='get_recipe_detail'),  # 개별 레시피 상세 (AJAX)
    path('recipe/<str:video_id>/', views.recipe_detail, name='recipe_detail'),  # 레시피 상세
]

