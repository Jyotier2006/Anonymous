from django.contrib import admin
from .models import (
    Profile,
    UserSkill,
    UserCourse,
    UserProject,
    UserAchievement,
)

admin.site.register(Profile)
admin.site.register(UserSkill)
admin.site.register(UserCourse)
admin.site.register(UserProject)
admin.site.register(UserAchievement)
from .models import LearningTopic, TopicProgress
admin.site.register(LearningTopic)
admin.site.register(TopicProgress)

