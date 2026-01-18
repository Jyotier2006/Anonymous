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
    path("skills/", views.skills_page, name="skills_page"),
    path("skills/delete/<int:skill_id>/", views.delete_skill, name="delete_skill"),
    path("courses/", views.courses_page, name="courses_page"),
    path("courses/delete/<int:course_id>/", views.delete_course, name="delete_course"),
    path("projects/", views.projects_page, name="projects_page"),
    path("projects/delete/<int:project_id>/", views.delete_project, name="delete_project"),
    path("achievements/", views.achievements_page, name="achievements_page"),
    path("achievements/delete/<int:ach_id>/", views.delete_achievement, name="delete_achievement"),
    path("advisor/", views.ai_advisor_page, name="ai_advisor_page"),
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("advisor/", views.ai_advisor_page, name="ai_advisor"),
    path("advisor/chat/", views.ai_advisor_chat, name="ai_advisor_chat"),

]
