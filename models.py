from django.db import models
from django.contrib.auth.models import User

DOMAIN_CHOICES = [("healthcare", "Healthcare")]
ROLE_CHOICES = [("student", "Student"), ("educator", "Educator")]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    domain = models.CharField(max_length=50, default="healthcare")
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    target_role = models.CharField(max_length=120, blank=True)
    github_username = models.CharField(max_length=39, blank=True, default="")
    def __str__(self):
        return f"{self.user.username} Profile"


class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=0)  # 0-5
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.level})"


class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=140)
    provider = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=30, default="in_progress")  # planned/in_progress/completed
    hours = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    tools = models.CharField(max_length=160, blank=True)  # Holistic Skill Intelligence System, Excel, Python...
    link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    date = models.DateField(null=True, blank=True)
    proof_link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class LearningTopic(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topics_created")
    domain = models.CharField(max_length=50, default="healthcare")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, default="beginner")  # beginner/intermediate/advanced
    est_minutes = models.IntegerField(default=30)
    skill_tag = models.CharField(max_length=100, blank=True)  # e.g. SQL, Excel, Privacy
    resource_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.domain})"


class TopicProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topic_progress")
    topic = models.ForeignKey(LearningTopic, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=20, default="not_started")  # not_started/in_progress/completed
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "topic")

    def __str__(self):
        return f"{self.student.username} - {self.topic.title} ({self.status})"
