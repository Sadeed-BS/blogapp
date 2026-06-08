from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('user_home/', views.user_home, name='user_home'),
    path('admin_home/', views.admin_view, name='admin_home'),
    path('add_blog/',views.add_blog,name='add_blog'),
]
