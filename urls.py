from django.contrib import admin
from django.urls import path
from app1 import views
from app1.profile_views import profile_builder
urlpatterns = [
    path('admin/', admin.site.urls),
    path("profile/", profile_builder, name="profile_builder"),
    path("logout/", views.logout_view, name="logout"),
    path('', views.signup_view, name='signup'),
    path('register/', views.signup_view, name='register'),
    path('login/', views.login_view, name='login'),
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("educator/", views.educator_dashboard, name="educator_dashboard"),
    path("topic/status/", views.update_topic_status, name="update_topic_status"),
    path('dashboard/', views.home_view, name='dashboard'),
]
