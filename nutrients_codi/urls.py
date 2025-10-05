from django.urls import path
from . import views

app_name = 'nutrients_codi'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile_setup, name='profile_setup'),
    path('analyze/', views.analyze_food, name='analyze_food'),
    path('delete-log/<int:log_id>/', views.delete_food_log, name='delete_food_log'),
    path('daily/<int:year>/<int:month>/<int:day>/', views.daily_detail, name='daily_detail'),
    path('edit-log/<int:log_id>/', views.edit_food_log, name='edit_food_log'),
]
