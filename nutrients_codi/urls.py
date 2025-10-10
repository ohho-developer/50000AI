from django.urls import path
from . import views
from . import community_views

app_name = 'nutrients_codi'

urlpatterns = [
    # 기존 기능
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile_setup, name='profile_setup'),
    path('analyze/', views.analyze_food, name='analyze_food'),
    path('delete-log/<int:log_id>/', views.delete_food_log, name='delete_food_log'),
    path('daily/<int:year>/<int:month>/<int:day>/', views.daily_detail, name='daily_detail'),
    path('edit-log/<int:log_id>/', views.edit_food_log, name='edit_food_log'),
    
    # 커뮤니티 기능
    path('community/', community_views.community_list, name='community_list'),
    path('community/<int:post_id>/', community_views.community_detail, name='community_detail'),
    path('community/create/', community_views.community_create, name='community_create'),
    path('community/<int:post_id>/update/', community_views.community_update, name='community_update'),
    path('community/<int:post_id>/delete/', community_views.community_delete, name='community_delete'),
    path('community/<int:post_id>/like/', community_views.community_like, name='community_like'),
    path('community/<int:post_id>/comment/', community_views.comment_create, name='comment_create'),
    path('community/comment/<int:comment_id>/delete/', community_views.comment_delete, name='comment_delete'),
]
