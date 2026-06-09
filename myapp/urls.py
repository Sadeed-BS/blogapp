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
    path('my_blogs/',views.my_blogs,name='my_blogs'),
    path('edit_blog/<int:id>/',views.edit_blog,name='edit_blog'),
    path('delete_blog/<int:id>/',views.delete_blog,name='delete_blog'),
    path('view_users/',views.view_users,name='view_users'),
    path('view_blogs_admin/',views.view_blogs_admin,name='view_blogs_admin'),
    path('delete_blog_admin/<int:id>/',views.delete_blog_admin,name='delete_blog_admin'),
    path('blogs/', views.blog_feed, name='blog_feed'),
]
