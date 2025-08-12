from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add/', views.add_operation, name='add_operation'),
    path('history/', views.history_view, name='history'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_update, name='category_update'),
    path('telegram-link/', views.generate_telegram_link, name='telegram_link'),
    path('api/categories/create/', views.api_create_category, name='api_create_category'),
    path('budget/', views.budget_view, name='budget'),
]
