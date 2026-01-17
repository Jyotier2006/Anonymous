from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .models import Profile
from .models import LearningTopic, TopicProgress
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .models import Profile
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect("login")

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        role = request.POST.get("role")  # student / educator
        goal = request.POST.get("goal", "").strip()
        institution = request.POST.get("institution", "").strip()
        terms = request.POST.get("terms")

        # If you are only doing healthcare now:
        sector = "healthcare"

        # validations
        if not terms:
            messages.error(request, "Please accept the Terms & Privacy Policy.")
            return redirect("signup")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        if role not in ["student", "educator"]:
            messages.error(request, "Please select Student or Educator.")
            return redirect("signup")

        # create user ONCE
        user = User.objects.create_user(username=username, email=email, password=password1)

        # create profile ONCE with role
        Profile.objects.create(
            user=user,
            role=role,
            domain=sector,
            headline=f"{role.title()} | {institution}".strip(" |"),
            bio=goal
        )

        login(request, user)
        messages.success(request, "Account created successfully!")

        # redirect by role after signup too
        if role == "educator":
            return redirect("educator_dashboard")
        return redirect("student_dashboard")

    return render(request, "signup.html")

from django.contrib.auth import authenticate, login as auth_login
from .models import Profile

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            profile = Profile.objects.filter(user=user).first()
            if profile and profile.role == "educator":
                return redirect("educator_dashboard")
            return redirect("student_dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "login.html")
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement

# --- Healthcare Role Framework (demo-ready) ---
HEALTHCARE_ROLES = {
    "Health Data Assistant": {
        "summary": "Entry role focusing on cleaning, reporting, and basic analytics for healthcare datasets.",
        "skills": {
            "Excel": {"level": 4, "weight": 3},
            "SQL": {"level": 3, "weight": 4},
            "Data Cleaning": {"level": 3, "weight": 3},
            "Healthcare Basics": {"level": 2, "weight": 2},
            "Medical Terminology": {"level": 2, "weight": 2},
            "Data Privacy (HIPAA-like)": {"level": 2, "weight": 4},
            "Dashboarding": {"level": 2, "weight": 2},
            "Documentation": {"level": 3, "weight": 2},
        },
        "projects": [
            "Hospital KPI dashboard (Admissions, ALOS, Bed Occupancy)",
            "Patient appointment no-show analysis",
            "Lab test turnaround time reporting"
        ],
        "courses": [
            "SQL for Data Analysis",
            "Excel (Pivot tables + dashboards)",
            "Healthcare Data Privacy basics"
        ],
    },
    "Clinical Data QA Associate": {
        "summary": "Focus on validating clinical datasets, ensuring accuracy, and maintaining documentation.",
        "skills": {
            "Attention to Detail": {"level": 4, "weight": 4},
            "Documentation": {"level": 4, "weight": 4},
            "Data Privacy (HIPAA-like)": {"level": 3, "weight": 4},
            "Excel": {"level": 3, "weight": 3},
            "SQL": {"level": 2, "weight": 2},
            "Healthcare Basics": {"level": 3, "weight": 3},
            "Medical Terminology": {"level": 3, "weight": 3},
        },
        "projects": [
            "Clinical dataset validation checklist",
            "Data quality report with issues and fixes"
        ],
        "courses": [
            "Data Quality fundamentals",
            "Documentation best practices"
        ],
    }
}

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))
topics = LearningTopic.objects.filter(domain="healthcare").order_by("-created_at")




def _compute_readiness(user_skills: dict, role_req: dict):
    """
    user_skills: {skill_name_lower: level_int}
    role_req: dict from HEALTHCARE_ROLES[...]['skills']
    """
    total_weight = 0
    score_weighted = 0
    gaps = []
    for req_name, req in role_req.items():
        req_level = int(req["level"])
        weight = int(req["weight"])
        total_weight += weight
        user_level = int(user_skills.get(req_name.lower(), 0))
        contribution = min(user_level, req_level) / req_level
        score_weighted += contribution * weight
        missing = req_level - user_level
        if missing > 0:
            gaps.append({
                "skill": req_name,
                "required": req_level,
                "current": user_level,
                "missing": missing,
                "priority": missing * weight,
                "weight": weight
            })

    readiness = 0 if total_weight == 0 else round((score_weighted / total_weight) * 100)
    gaps.sort(key=lambda x: (-x["priority"], -x["missing"], x["skill"]))
    return readiness, gaps

def _next_actions(profile, readiness, gaps, user_courses, user_projects):
    actions = []

    # 1) Gaps-based action
    if gaps:
        top = gaps[0]
        actions.append({
            "title": f"Improve {top['skill']} (+{top['missing']} levels)",
            "desc": "This is your highest-impact gap for your target role.",
            "tag": "Highest priority"
        })

    # 2) Projects-based action
    if user_projects < 1:
        actions.append({
            "title": "Add 1 healthcare project",
            "desc": "Projects increase readiness and make your profile credible for employers.",
            "tag": "Portfolio"
        })

    # 3) Courses-based action
    if user_courses < 1:
        actions.append({
            "title": "Start 1 course this week",
            "desc": "Even a YouTube playlist counts—track it as a course to show progression.",
            "tag": "Learning"
        })

    # 4) Profile completeness
    if not (profile.headline or "").strip():
        actions.append({
            "title": "Write a strong headline",
            "desc": "Example: Health Data | SQL | Excel | Reporting",
            "tag": "Quick win"
        })

    # 5) readiness note
    if readiness >= 75:
        actions.append({
            "title": "Prepare a role-ready resume",
            "desc": "You’re close. Add proof links and refine projects.",
            "tag": "Finish"
        })

    return actions[:5]

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement, LearningTopic, TopicProgress

@login_required
def student_dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()

    # 1) Load profile data
    skills_qs = UserSkill.objects.filter(user=request.user)
    courses_qs = UserCourse.objects.filter(user=request.user)
    projects_qs = UserProject.objects.filter(user=request.user)
    achievements_qs = UserAchievement.objects.filter(user=request.user)

    # 2) Load learning topics (educator-created) + student's progress
    topics = LearningTopic.objects.filter(domain="healthcare").order_by("-created_at")

    progress_map = {
        p.topic_id: p.status
        for p in TopicProgress.objects.filter(student=request.user)
    }

    topics_ui = []
    for t in topics:
        topics_ui.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "difficulty": t.difficulty,
            "est_minutes": t.est_minutes,
            "skill_tag": t.skill_tag,
            "resource_link": t.resource_link,
            "status": progress_map.get(t.id, "not_started"),
        })

    completed = sum(1 for s in progress_map.values() if s == "completed")
    inprog = sum(1 for s in progress_map.values() if s == "in_progress")
    total_topics = topics.count()
    learning_progress = 0 if total_topics == 0 else round((completed / total_topics) * 100)

    # (Optional) quick readiness score based on skills (simple demo)
    skills_count = skills_qs.count()
    readiness = 0
    if skills_count:
        readiness = round(sum(int(s.level) for s in skills_qs) / (skills_count * 5) * 100)

    context = {
        "profile": profile,
        "skills": skills_qs,
        "courses": courses_qs,
        "projects": projects_qs,
        "achievements": achievements_qs,

        "readiness": readiness,
        "skills_count": skills_count,

        "topics": topics_ui,
        "learning_progress": learning_progress,
        "topics_total": total_topics,
        "topics_completed": completed,
        "topics_inprog": inprog,
    }

    return render(request, "student_dashboard.html", context)

@login_required
def educator_dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    if not profile or profile.role != "educator":
        return redirect("student_dashboard")

    if request.method == "POST":
        LearningTopic.objects.create(
            created_by=request.user,
            domain="healthcare",
            title=(request.POST.get("title") or "").strip(),
            description=(request.POST.get("description") or "").strip(),
            difficulty=request.POST.get("difficulty") or "beginner",
            est_minutes=int(request.POST.get("est_minutes") or 30),
            skill_tag=(request.POST.get("skill_tag") or "").strip(),
            resource_link=(request.POST.get("resource_link") or "").strip(),
        )
        messages.success(request, "Topic created successfully!")
        return redirect("educator_dashboard")

    topics = LearningTopic.objects.filter(domain="healthcare").order_by("-created_at")
    return render(request, "educator_dashboard.html", {"topics": topics})

import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement
from django.contrib import messages
@require_POST
@login_required
def update_topic_status(request):
    topic_id = request.POST.get("topic_id")
    status = request.POST.get("status")
    if status not in ["not_started", "in_progress", "completed"]:
        status = "not_started"

    topic = LearningTopic.objects.filter(id=topic_id, domain="healthcare").first()
    if not topic:
        messages.error(request, "Topic not found.")
        return redirect("student_dashboard")

    obj, _ = TopicProgress.objects.get_or_create(student=request.user, topic=topic)
    obj.status = status
    obj.save()
    return redirect("student_dashboard")

def _to_int(x, default=0):
    try:
        return int(x)
    except:
        return default

@login_required
def profile_builder(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.headline = (request.POST.get("headline") or "").strip()
        profile.bio = (request.POST.get("bio") or "").strip()
        profile.target_role = (request.POST.get("target_role") or "").strip()
        profile.domain = "healthcare"
        profile.save()

        UserSkill.objects.filter(user=request.user).delete()
        UserCourse.objects.filter(user=request.user).delete()
        UserProject.objects.filter(user=request.user).delete()
        UserAchievement.objects.filter(user=request.user).delete()

        # Skills
        for name, lvl in zip(request.POST.getlist("skill_name[]"), request.POST.getlist("skill_level[]")):
            name = (name or "").strip()
            if name:
                UserSkill.objects.create(user=request.user, name=name, level=max(0, min(5, _to_int(lvl, 0))))

        # Courses
        for t, p, s, h in zip(
            request.POST.getlist("course_title[]"),
            request.POST.getlist("course_provider[]"),
            request.POST.getlist("course_status[]"),
            request.POST.getlist("course_hours[]")
        ):
            t = (t or "").strip()
            if t:
                UserCourse.objects.create(
                    user=request.user,
                    title=t,
                    provider=(p or "").strip(),
                    status=(s or "in_progress"),
                    hours=max(0, _to_int(h, 0))
                )

        # Projects
        for t, d, tools, link in zip(
            request.POST.getlist("project_title[]"),
            request.POST.getlist("project_desc[]"),
            request.POST.getlist("project_tools[]"),
            request.POST.getlist("project_link[]")
        ):
            t = (t or "").strip()
            if t:
                UserProject.objects.create(
                    user=request.user,
                    title=t,
                    description=(d or "").strip(),
                    tools=(tools or "").strip(),
                    link=(link or "").strip()
                )

        # Achievements
        for t, dt, link in zip(
            request.POST.getlist("ach_title[]"),
            request.POST.getlist("ach_date[]"),
            request.POST.getlist("ach_link[]")
        ):
            t = (t or "").strip()
            if t:
                UserAchievement.objects.create(
                    user=request.user,
                    title=t,
                    date=dt or None,
                    proof_link=(link or "").strip()
                )

        messages.success(request, "Profile saved successfully!")
        return redirect("profile_builder")

    skills = UserSkill.objects.filter(user=request.user).order_by("-level", "name")
    courses = UserCourse.objects.filter(user=request.user).order_by("-id")
    projects = UserProject.objects.filter(user=request.user).order_by("-created_at")
    achievements = UserAchievement.objects.filter(user=request.user).order_by("-id")

    return render(request, "profile_builder.html", {
        "profile": profile,
        "skills": skills,
        "courses": courses,
        "projects": projects,
        "achievements": achievements
    })

@require_POST
@login_required
def update_topic_status(request):
    topic_id = request.POST.get("topic_id")
    status = request.POST.get("status")
    if status not in ["not_started", "in_progress", "completed"]:
        status = "not_started"

    topic = LearningTopic.objects.filter(id=topic_id, domain="healthcare").first()
    if not topic:
        messages.error(request, "Topic not found.")
        return redirect("student_dashboard")

    obj, _ = TopicProgress.objects.get_or_create(student=request.user, topic=topic)
    obj.status = status
    obj.save()
    return redirect("student_dashboard")

def home_view(request):
    return render(request, "dashboard.html")