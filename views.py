from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

import requests
import os
from groq import Groq
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
def ai_advisor_page(request):
    # just render the page
    return render(request, "ai_advisor.html", {
        "target_role": getattr(Profile.objects.filter(user=request.user).first(), "target_role", "") or "Health Data Assistant"
    })
COURSE_LIBRARY = {
    "sql": [
        {"title": "SQL for Healthcare Reporting (Joins → KPIs)", "provider": "YouTube", "est_hours": 6},
        {"title": "SQL Window Functions for Analytics", "provider": "YouTube", "est_hours": 5},
        {"title": "SQL for Data Analysis (Basics to Intermediate)", "provider": "Coursera", "est_hours": 12},
    ],
    "excel": [
        {"title": "Excel Pivot Tables + Dashboards (Healthcare KPIs)", "provider": "YouTube", "est_hours": 4},
        {"title": "Excel for Data Cleaning (Real datasets)", "provider": "YouTube", "est_hours": 3},
    ],
    "data cleaning": [
        {"title": "Data Cleaning Fundamentals (Missing Values, Outliers)", "provider": "YouTube", "est_hours": 4},
        {"title": "Healthcare Data Quality Checks", "provider": "YouTube", "est_hours": 3},
    ],
    "data privacy (hipaa-like)": [
        {"title": "Healthcare Data Privacy Basics (HIPAA-style)", "provider": "YouTube", "est_hours": 2},
        {"title": "Patient Data Handling & Compliance Basics", "provider": "YouTube", "est_hours": 2},
    ],
    "documentation": [
        {"title": "Documentation for Analysts (Reports + SOPs)", "provider": "YouTube", "est_hours": 2},
    ],
    "dashboarding": [
        {"title": "Build Dashboards in Excel (Healthcare KPIs)", "provider": "YouTube", "est_hours": 4},
    ],
    "healthcare basics": [
        {"title": "Healthcare Data 101 (EHR, ICD, Lab, Claims)", "provider": "YouTube", "est_hours": 2},
    ],
    "medical terminology": [
        {"title": "Medical Terminology for Data Roles", "provider": "YouTube", "est_hours": 3},
    ],
}
def recommend_new_courses(user, gaps, limit=6):
    """
    Returns a list of courses (dicts) based on top gaps,
    excluding courses user already added.
    """
    existing_titles = set(
        (c.title or "").strip().lower()
        for c in UserCourse.objects.filter(user=user)
    )

    recs = []
    for g in (gaps or [])[:5]:  # top 5 gaps
        skill_key = (g.get("skill") or "").strip().lower()
        for course in COURSE_LIBRARY.get(skill_key, []):
            title_lc = course["title"].strip().lower()
            if title_lc in existing_titles:
                continue
            recs.append({
                "title": course["title"],
                "provider": course["provider"],
                "hours": course["est_hours"],
                "skill": g.get("skill"),
                "why": f"Missing +{g.get('missing')} levels in {g.get('skill')}",
            })
            if len(recs) >= limit:
                return recs

    # fallback: if no gaps or no library match
    if not recs:
        fallback = [
            {"title": "SQL for Data Analysis (Basics)", "provider": "YouTube", "hours": 6, "skill": "SQL", "why": "Strong base skill"},
            {"title": "Excel Dashboards (Healthcare KPIs)", "provider": "YouTube", "hours": 4, "skill": "Excel", "why": "Portfolio-friendly"},
        ]
        for c in fallback:
            if c["title"].lower() not in existing_titles:
                recs.append(c)

    return recs[:limit]

@require_POST
@login_required
def ai_advisor_chat(request):
    msg = (request.POST.get("message") or "").strip()
    if not msg:
        return JsonResponse({"ok": False, "error": "Empty message."})

    # Build a healthcare-focused context from DB
    profile, _ = Profile.objects.get_or_create(user=request.user)

    skills = list(UserSkill.objects.filter(user=request.user).values("name", "level"))
    courses = list(UserCourse.objects.filter(user=request.user).values("title", "status", "hours"))
    projects = list(UserProject.objects.filter(user=request.user).values("title", "tools"))
    ach = list(UserAchievement.objects.filter(user=request.user).values("title"))

    system = f"""
You are a healthcare career mentor for the MediBridge app.
Give practical, short, step-by-step advice.
Focus only on healthcare domain roles like: Health Data Assistant, Clinical Data QA Associate, etc.
When recommending, use the user's saved skills/courses/projects.
Always output:
1) Best next 3 actions
2) 2 course suggestions (healthcare relevant)
3) 1 project idea (healthcare dataset / KPI / quality / privacy)
"""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    completion = client.chat.completions.create(
        model="groq/compound-mini",   
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"""
USER PROFILE:
target_role: {profile.target_role or "Health Data Assistant"}
headline: {profile.headline or ""}
bio: {profile.bio or ""}

SKILLS: {skills}
COURSES: {courses}
PROJECTS: {projects}
ACHIEVEMENTS: {ach}

USER QUESTION: {msg}
"""}
        ],
        temperature=0.4,
    )

    answer = completion.choices[0].message.content
    return JsonResponse({"ok": True, "answer": answer})

from .models import (
    Profile,
    UserSkill, UserCourse, UserProject, UserAchievement,
    LearningTopic, TopicProgress
)

# -----------------------------
# Auth
# -----------------------------

def logout_view(request):
    logout(request)
    return redirect("login")

import requests

HEALTHCARE_TOPIC_LIBRARY = [
    {
        "title": "Healthcare Data Basics: Patients, Visits, Encounters",
        "difficulty": "beginner",
        "est_minutes": 35,
        "skill_tag": "Healthcare Basics",
        "description": "Understand how patient, visit, encounter, and provider data is structured in hospitals.",
        "resource_link": "",
    },
    {
        "title": "Medical Terminology for Healthcare Analytics",
        "difficulty": "beginner",
        "est_minutes": 40,
        "skill_tag": "Medical Terminology",
        "description": "Learn common clinical terms used in diagnoses, lab tests, and prescriptions.",
        "resource_link": "",
    },
    {
        "title": "Healthcare Privacy & Compliance (HIPAA-like concepts)",
        "difficulty": "beginner",
        "est_minutes": 45,
        "skill_tag": "Healthcare Data Privacy",
        "description": "Learn PHI, de-identification, access control, audit logs, and safe data sharing practices.",
        "resource_link": "",
    },
    {
        "title": "SQL Practice: Appointments + No-show Analysis",
        "difficulty": "intermediate",
        "est_minutes": 60,
        "skill_tag": "SQL (Health Data)",
        "description": "Write queries to calculate no-show rate by department/time and identify patterns.",
        "resource_link": "",
    },
    {
        "title": "Excel Dashboard: Hospital KPIs (Admissions, ALOS, Bed Occupancy)",
        "difficulty": "intermediate",
        "est_minutes": 60,
        "skill_tag": "Excel",
        "description": "Create pivot tables + KPI cards + charts for operational hospital reporting.",
        "resource_link": "",
    },
    {
        "title": "Clinical Data Quality & Cleaning",
        "difficulty": "intermediate",
        "est_minutes": 50,
        "skill_tag": "Clinical Data Quality",
        "description": "Handle missing values, duplicates, invalid codes, and consistency checks in healthcare tables.",
        "resource_link": "",
    },
]

def github_fetch(username: str):
    username = (username or "").strip()
    if not username:
        return None

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "MediBridge"
    }

    try:
        prof = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
        if prof.status_code == 404:
            return {"ok": False, "error": "GitHub username not found."}
        if prof.status_code == 403:
            return {"ok": False, "error": "GitHub rate limit (403). Try after few minutes."}
        prof.raise_for_status()
        p = prof.json()

        repos_r = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"sort": "updated", "per_page": 5},
            headers=headers,
            timeout=10
        )
        if repos_r.status_code == 403:
            return {"ok": False, "error": "GitHub rate limit (403). Try after few minutes."}
        repos_r.raise_for_status()
        repos = repos_r.json() if isinstance(repos_r.json(), list) else []

        latest = repos[0] if repos else None

        # simple language count
        lang_map = {}
        for r in repos:
            lang = r.get("language")
            if lang:
                lang_map[lang] = lang_map.get(lang, 0) + 1

        top_langs = [{"name": k, "count": v} for k, v in sorted(lang_map.items(), key=lambda x: -x[1])]

        return {
            "ok": True,
            "profile": {
                "login": p.get("login"),
                "name": p.get("name"),
                "followers": p.get("followers"),
                "public_repos": p.get("public_repos"),
                "html_url": p.get("html_url"),
                "avatar_url": p.get("avatar_url"),
            },
            "latest_repo": {
                "name": (latest or {}).get("name"),
                "description": (latest or {}).get("description"),
                "html_url": (latest or {}).get("html_url"),
                "updated_at": (latest or {}).get("updated_at"),
            } if latest else None,
            "top_languages": top_langs[:5],
        }

    except requests.RequestException as e:
        return {"ok": False, "error": f"GitHub error: {e}"}

def signup_view(request):
    if request.method == "POST":
        username = (request.POST.get("username", "") or "").strip()
        email = (request.POST.get("email", "") or "").strip()
        password1 = request.POST.get("password1", "") or ""
        password2 = request.POST.get("password2", "") or ""

        role = request.POST.get("role")  # student / educator
        goal = (request.POST.get("goal", "") or "").strip()
        institution = (request.POST.get("institution", "") or "").strip()
        terms = request.POST.get("terms")

        # Healthcare only
        sector = "healthcare"

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

        user = User.objects.create_user(username=username, email=email, password=password1)

        Profile.objects.create(
            user=user,
            role=role,
            domain=sector,
            headline=f"{role.title()} | {institution}".strip(" |"),
            bio=goal
        )

        login(request, user)
        messages.success(request, "Account created successfully!")

        if role == "educator":
            return redirect("educator_dashboard")
        return redirect("student_dashboard")

    return render(request, "signup.html")


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


# -----------------------------
# GitHub API helper (ONE source of truth)
# -----------------------------

def fetch_github_data(username: str):
    username = (username or "").strip()
    if not username:
        return None

    base = "https://api.github.com"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "MediBridge-Django-App"
    }

    try:
        # profile
        r = requests.get(f"{base}/users/{username}", headers=headers, timeout=8)
        if r.status_code == 404:
            return {"ok": False, "error": "GitHub user not found (404). Check username spelling."}
        if r.status_code == 403:
            return {"ok": False, "error": "GitHub rate limit (403). Try again after a few minutes."}
        r.raise_for_status()
        prof = r.json()

        # repos (recent)
        rr = requests.get(
            f"{base}/users/{username}/repos",
            params={"sort": "updated", "per_page": 5},
            headers=headers,
            timeout=8
        )
        if rr.status_code == 403:
            return {"ok": False, "error": "GitHub rate limit (403) while fetching repos."}
        rr.raise_for_status()
        repos = rr.json() if isinstance(rr.json(), list) else []

        latest_repo = repos[0] if repos else None

        # languages
        lang_count = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                lang_count[lang] = lang_count.get(lang, 0) + 1

        top_languages = [{"name": k, "count": v} for k, v in sorted(lang_count.items(), key=lambda x: -x[1])][:5]

        return {
            "ok": True,
            "profile": {
                "login": prof.get("login"),
                "name": prof.get("name"),
                "followers": prof.get("followers", 0),
                "public_repos": prof.get("public_repos", 0),
                "html_url": prof.get("html_url"),
                "avatar_url": prof.get("avatar_url"),
            },
            "repo_count": prof.get("public_repos", 0),
            "latest_repo": {
                "name": (latest_repo or {}).get("name"),
                "description": (latest_repo or {}).get("description"),
                "html_url": (latest_repo or {}).get("html_url"),
                "updated_at": (latest_repo or {}).get("updated_at"),
                "language": (latest_repo or {}).get("language"),
            } if latest_repo else None,
            "top_languages": top_languages,
        }

    except requests.Timeout:
        return {"ok": False, "error": "GitHub request timed out. Check internet and try again."}
    except requests.RequestException as e:
        return {"ok": False, "error": f"GitHub fetch failed: {str(e)}"}


# -----------------------------
# Healthcare Role Framework (demo-ready)
# -----------------------------

HEALTHCARE_ROLES = {
    "Health Data Assistant": {
        "summary": "Entry role focusing on cleaning, reporting, and basic analytics for healthcare datasets.",
        "skills": {
            "Excel": {"level": 4, "weight": 3},
            "SQL (Health Data)": {"level": 3, "weight": 4},
            "Clinical Data Quality": {"level": 3, "weight": 3},
            "Healthcare Basics": {"level": 2, "weight": 2},
            "Medical Terminology": {"level": 2, "weight": 2},
            "Healthcare Data Privacy": {"level": 2, "weight": 4},
            "Dashboarding": {"level": 2, "weight": 2},
            "Documentation": {"level": 3, "weight": 2},
        },
        "projects": [
            "Hospital KPI dashboard (Admissions, ALOS, Bed Occupancy)",
            "Patient appointment no-show analysis",
            "Lab test turnaround time reporting"
        ],
        "courses": [
            "SQL for Healthcare Data Analysis",
            "Excel (Pivot tables + dashboards)",
            "Healthcare Data Privacy basics"
        ],
    },
    "Clinical Data QA Associate": {
        "summary": "Focus on validating clinical datasets, ensuring accuracy, and maintaining documentation.",
        "skills": {
            "Attention to Detail": {"level": 4, "weight": 4},
            "Documentation": {"level": 4, "weight": 4},
            "Healthcare Data Privacy": {"level": 3, "weight": 4},
            "Excel": {"level": 3, "weight": 3},
            "SQL (Health Data)": {"level": 2, "weight": 2},
            "Healthcare Basics": {"level": 3, "weight": 3},
            "Medical Terminology": {"level": 3, "weight": 3},
        },
        "projects": [
            "Clinical dataset validation checklist",
            "Data quality report with issues and fixes"
        ],
        "courses": [
            "Clinical Data Quality fundamentals",
            "Documentation best practices"
        ],
    }
}

DEFAULT_ROLE = "Health Data Assistant"


def _compute_readiness(user_skills: dict, role_req: dict):
    total_weight = 0
    score_weighted = 0
    gaps = []

    for req_name, req in role_req.items():
        req_level = int(req.get("level", 0) or 0)
        weight = int(req.get("weight", 1) or 1)
        if req_level <= 0:
            continue

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


def _next_actions(profile, readiness, gaps, user_courses_count, user_projects_count):
    actions = []

    if gaps:
        top = gaps[0]
        actions.append({
            "title": f"Improve {top['skill']} (+{top['missing']} levels)",
            "desc": "This is your highest-impact gap for your target role.",
            "tag": "Highest priority"
        })

    if user_projects_count < 1:
        actions.append({
            "title": "Add 1 healthcare project",
            "desc": "Projects increase readiness and make your profile credible for employers.",
            "tag": "Portfolio"
        })

    if user_courses_count < 1:
        actions.append({
            "title": "Start 1 course this week",
            "desc": "Even a YouTube playlist counts—track it as a course to show progression.",
            "tag": "Learning"
        })

    if not (profile.headline or "").strip():
        actions.append({
            "title": "Write a strong headline",
            "desc": "Example: Health Data | SQL | Excel | Reporting",
            "tag": "Quick win"
        })

    if readiness >= 75:
        actions.append({
            "title": "Prepare a role-ready resume",
            "desc": "You’re close. Add proof links and refine projects.",
            "tag": "Finish"
        })

    return actions[:5]


def _build_recommendations(role_data, gaps):
    recs = []
    top_gaps = gaps[:4]

    for g in top_gaps:
        recs.append({
            "title": f"Learn: {g['skill']}",
            "type": "course",
            "why": f"Required for your role. Missing +{g['missing']} levels."
        })

    for c in (role_data.get("courses") or [])[:2]:
        recs.append({"title": c, "type": "course", "why": "Suggested by role framework."})

    for p in (role_data.get("projects") or [])[:2]:
        recs.append({"title": p, "type": "project", "why": "Suggested project to build proof."})

    return recs[:8]


def _build_roadmap_7(gaps):
    plan = []
    focus = gaps[:3]
    days = ["Day 1","Day 2","Day 3","Day 4","Day 5","Day 6","Day 7"]

    if not focus:
        return []

    for i, d in enumerate(days):
        g = focus[i % len(focus)]
        plan.append({
            "day": d,
            "task": f"Spend 45–60 mins on {g['skill']} (target +{g['missing']} levels). Do 1 small practice task."
        })
    return plan


# -----------------------------
# Dashboards
# -----------------------------

@login_required
def student_dashboard(request):
    # ensures CSRF cookie exists (helps some CSRF setups)
    get_token(request)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.domain = "healthcare"
    profile.save(update_fields=["domain"])

    # defaults
    readiness = 0
    gaps = []
    next_actions = []
    recommendations = []
    roadmap_7 = []
    roles_list = list(HEALTHCARE_ROLES.keys())

    # role
    target_role = (profile.target_role or "").strip() or DEFAULT_ROLE
    if target_role not in HEALTHCARE_ROLES:
        target_role = DEFAULT_ROLE
    role_data = HEALTHCARE_ROLES.get(target_role)

    skills_qs = UserSkill.objects.filter(user=request.user)
    courses_qs = UserCourse.objects.filter(user=request.user)
    projects_qs = UserProject.objects.filter(user=request.user)
    achievements_qs = UserAchievement.objects.filter(user=request.user)

    user_skills = {}
    for s in skills_qs:
        k = (s.name or "").strip().lower()
        if k:
            user_skills[k] = int(s.level or 0)

    readiness, gaps = _compute_readiness(user_skills, role_data.get("skills", {}))
    new_course_recs = recommend_new_courses(request.user, gaps, limit=6)

    next_actions = _next_actions(profile, readiness, gaps, courses_qs.count(), projects_qs.count())
    recommendations = _build_recommendations(role_data, gaps)
    roadmap_7 = _build_roadmap_7(gaps)

    stage_label = "Starting"
    stage_index = 0
    if readiness >= 75:
        stage_label = "Near-ready"
        stage_index = 2
    elif readiness >= 45:
        stage_label = "Building"
        stage_index = 1

    pathway = [
        {"title": "Foundation", "desc": "Learn basics + build 1 mini healthcare dataset project."},
        {"title": "Job-ready", "desc": "Close top gaps + finish 2 evidence projects + 1 course."},
        {"title": "Specialist", "desc": "Pick a niche: EHR analytics / privacy / quality / interoperability."},
    ]

    topics_qs = LearningTopic.objects.filter(domain="healthcare").order_by("-created_at")
    progress_map = {p.topic_id: p.status for p in TopicProgress.objects.filter(student=request.user)}

    topics_ui = []
    for t in topics_qs:
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

    topics_total = topics_qs.count()
    topics_completed = sum(1 for s in progress_map.values() if s == "completed")
    topics_inprog = sum(1 for s in progress_map.values() if s == "in_progress")
    learning_progress = 0 if topics_total == 0 else round((topics_completed / topics_total) * 100)

    # GitHub data for dashboard (optional)
    github_data = None
    if hasattr(profile, "github_username") and (profile.github_username or "").strip():
        github_data = fetch_github_data(profile.github_username)

    context = {
        "profile": profile,
        "new_course_recs": new_course_recs,
        "skills_count": skills_qs.count(),
        "courses_count": courses_qs.count(),
        "projects_count": projects_qs.count(),
        "ach_count": achievements_qs.count(),

        "target_role": target_role,
        "roles_list": roles_list,
        "role_data": role_data,

        "readiness": readiness,
        "gaps": gaps,
        "next_actions": next_actions,
        "recommendations": recommendations,
        "roadmap_7": roadmap_7,

        "topics": topics_ui,
        "learning_progress": learning_progress,
        "topics_total": topics_total,
        "topics_completed": topics_completed,
        "topics_inprog": topics_inprog,

        "stage_label": stage_label,
        "stage_index": stage_index,
        "pathway": pathway,

        "github_data": github_data,
    }
    return render(request, "student_dashboard.html", context)

@login_required
def educator_dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    if not profile or profile.role != "educator":
        return redirect("student_dashboard")

    if request.method == "POST":
        # If educator clicked "Add from library"
        if request.POST.get("use_library") == "1":
            idx = request.POST.get("lib_index")
            try:
                idx = int(idx)
            except:
                idx = -1

            if 0 <= idx < len(HEALTHCARE_TOPIC_LIBRARY):
                t = HEALTHCARE_TOPIC_LIBRARY[idx]
                LearningTopic.objects.create(
                    created_by=request.user,
                    domain="healthcare",
                    title=t["title"],
                    description=t["description"],
                    difficulty=t["difficulty"],
                    est_minutes=int(t["est_minutes"]),
                    skill_tag=t["skill_tag"],
                    resource_link=t.get("resource_link", ""),
                )
                messages.success(request, "Topic added from Healthcare Library!")
                return redirect("educator_dashboard")

        # Manual create (your original)
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
    return render(request, "educator_dashboard.html", {
        "topics": topics,
        "library": HEALTHCARE_TOPIC_LIBRARY,
    })

# -----------------------------
# Topic Progress
# -----------------------------

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


# -----------------------------
# Profile Builder
# -----------------------------

def _to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement
from django.db.models import Q
from django.views.decorators.http import require_POST

@login_required
def skills_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.domain = "healthcare"
    profile.save(update_fields=["domain"])

    # Search / filter
    q = (request.GET.get("q") or "").strip()
    min_level = (request.GET.get("min_level") or "").strip()

    skills_qs = UserSkill.objects.filter(user=request.user)

    if q:
        skills_qs = skills_qs.filter(name__icontains=q)

    if min_level.isdigit():
        skills_qs = skills_qs.filter(level__gte=int(min_level))

    skills_qs = skills_qs.order_by("-level", "name")

    # Role framework
    target_role = (profile.target_role or "").strip() or DEFAULT_ROLE
    if target_role not in HEALTHCARE_ROLES:
        target_role = DEFAULT_ROLE
    role_data = HEALTHCARE_ROLES[target_role]
    role_skills = role_data.get("skills", {})

    # Build user skills map
    user_map = {(s.name or "").strip().lower(): int(s.level or 0) for s in UserSkill.objects.filter(user=request.user)}

    readiness, gaps = _compute_readiness(user_map, role_skills)

    # Build gap rows for this page (required vs current)
    gap_rows = []
    for skill_name, req in role_skills.items():
        req_level = int(req.get("level", 0) or 0)
        cur = int(user_map.get(skill_name.lower(), 0))
        gap_rows.append({
            "name": skill_name,
            "required": req_level,
            "current": cur,
            "missing": max(0, req_level - cur),
            "weight": int(req.get("weight", 1) or 1),
        })
    gap_rows.sort(key=lambda x: (-x["missing"], -x["weight"], x["name"]))

    # Suggested skills to add quickly (healthcare-only)
    suggested = [
        "Excel", "SQL", "Capalary", "Dashboarding",
        "Healthcare Basics", "Medical Terminology",
        "Muscle Theory", "Documentation",
        "Attention to Detail"
    ]
    suggested = [s for s in suggested if s.lower() not in user_map]

    # POST handling (add/update)
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        level = request.POST.get("level") or "1"

        if not name:
            messages.error(request, "Skill name is required.")
            return redirect("skills_page")

        try:
            level_int = int(level)
            level_int = max(1, min(5, level_int))
        except:
            level_int = 1

        obj, created = UserSkill.objects.update_or_create(
            user=request.user,
            name=name,
            defaults={"level": level_int}
        )

        if created:
            messages.success(request, f"Skill added: {name} (Level {level_int}).")
        else:
            messages.success(request, f"Skill updated: {name} (Level {level_int}).")

        return redirect("skills_page")

    return render(request, "skills_page.html", {
        "profile": profile,
        "skills": skills_qs,
        "q": q,
        "min_level": min_level,
        "target_role": target_role,
        "readiness": readiness,
        "gap_rows": gap_rows,
        "suggested": suggested,
    })

from django.views.decorators.http import require_POST

@login_required
def courses_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.domain = "healthcare"
    profile.save(update_fields=["domain"])

    # Filters
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()  # in_progress/completed
    provider = (request.GET.get("provider") or "").strip()
    min_hours = (request.GET.get("min_hours") or "").strip()

    courses_qs = UserCourse.objects.filter(user=request.user)

    if q:
        courses_qs = courses_qs.filter(title__icontains=q)
    if status in ["in_progress", "completed"]:
        courses_qs = courses_qs.filter(status=status)
    if provider:
        courses_qs = courses_qs.filter(provider__icontains=provider)
    if min_hours.isdigit():
        courses_qs = courses_qs.filter(hours__gte=int(min_hours))

    courses_qs = courses_qs.order_by("-id")

    # Stats
    total = UserCourse.objects.filter(user=request.user).count()
    completed = UserCourse.objects.filter(user=request.user, status="completed").count()
    in_prog = UserCourse.objects.filter(user=request.user, status="in_progress").count()
    total_hours = sum(c.hours or 0 for c in UserCourse.objects.filter(user=request.user))
    completion_pct = 0 if total == 0 else round((completed / total) * 100)

    # Role-based recommendations (use your existing role framework)
    target_role = (profile.target_role or "").strip() or DEFAULT_ROLE
    if target_role not in HEALTHCARE_ROLES:
        target_role = DEFAULT_ROLE
    role_data = HEALTHCARE_ROLES[target_role]

    # Build user skill map and compute gaps to suggest courses
    user_skills = {(s.name or "").strip().lower(): int(s.level or 0) for s in UserSkill.objects.filter(user=request.user)}
    _, gaps = _compute_readiness(user_skills, role_data.get("skills", {}))

    recommended = []
    # Top gap-based course suggestions (simple mapping)
    for g in gaps[:3]:
        skill = g["skill"].lower()
        if "sql" in skill:
            recommended.append("SQL for Healthcare Data Analysis")
        elif "excel" in skill:
            recommended.append("Excel Dashboards for Hospital KPIs")
        elif "privacy" in skill:
            recommended.append("Healthcare Data Privacy & Compliance Basics")
        elif "dashboard" in skill:
            recommended.append("Power BI / Dashboarding for Healthcare (Basics)")
        elif "terminology" in skill:
            recommended.append("Medical Terminology for Data Professionals")
        else:
            recommended.append(f"{g['skill']} Fundamentals (Healthcare context)")

    # Add role framework courses too (fallback)
    for c in (role_data.get("courses") or [])[:3]:
        if c not in recommended:
            recommended.append(c)

    # Suggested quick-add courses (healthcare)
    suggested = [
        {"title": "SQL for Data Analysis", "provider": "YouTube / Coursera", "status": "in_progress", "hours": 0},
        {"title": "Excel Pivot Tables + Dashboards", "provider": "YouTube", "status": "in_progress", "hours": 0},
        {"title": "Healthcare Data Privacy basics", "provider": "YouTube", "status": "in_progress", "hours": 0},
        {"title": "Hospital KPI Reporting (Admissions, ALOS, Bed Occupancy)", "provider": "YouTube", "status": "in_progress", "hours": 0},
    ]

    existing_titles = set((c.title or "").strip().lower() for c in UserCourse.objects.filter(user=request.user))
    suggested = [s for s in suggested if s["title"].lower() not in existing_titles]

    # Add/update on POST
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        provider_in = (request.POST.get("provider") or "").strip()
        status_in = (request.POST.get("status") or "in_progress").strip()
        hours_in = request.POST.get("hours") or "0"

        if not title:
            messages.error(request, "Course title is required.")
            return redirect("courses_page")

        if status_in not in ["in_progress", "completed"]:
            status_in = "in_progress"

        try:
            hours_int = max(0, int(hours_in))
        except:
            hours_int = 0

        # If you want “update if same title already exists”
        obj = UserCourse.objects.filter(user=request.user, title__iexact=title).first()
        if obj:
            obj.provider = provider_in
            obj.status = status_in
            obj.hours = hours_int
            obj.save()
            messages.success(request, f"Course updated: {title}")
        else:
            UserCourse.objects.create(
                user=request.user,
                title=title,
                provider=provider_in,
                status=status_in,
                hours=hours_int
            )
            messages.success(request, f"Course added: {title}")

        return redirect("courses_page")

    return render(request, "courses_page.html", {
        "profile": profile,
        "courses": courses_qs,
        "q": q,
        "status": status,
        "provider": provider,
        "min_hours": min_hours,

        "target_role": target_role,
        "completion_pct": completion_pct,
        "total_courses": total,
        "completed_courses": completed,
        "in_progress_courses": in_prog,
        "total_hours": total_hours,

        "recommended": recommended[:6],
        "suggested": suggested[:8],
    })

from django.views.decorators.http import require_POST
from django.db.models import Q

@login_required
def projects_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.domain = "healthcare"
    profile.save(update_fields=["domain"])

    # GET filters
    q = (request.GET.get("q") or "").strip()
    tool = (request.GET.get("tool") or "").strip()
    has_link = (request.GET.get("has_link") or "").strip()  # "1" only
    recent = (request.GET.get("recent") or "").strip()      # "1" only

    projects_qs = UserProject.objects.filter(user=request.user)

    if q:
        projects_qs = projects_qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(tools__icontains=q)
        )

    if tool:
        projects_qs = projects_qs.filter(tools__icontains=tool)

    if has_link == "1":
        projects_qs = projects_qs.exclude(link="").exclude(link__isnull=True)

    projects_qs = projects_qs.order_by("-created_at")

    if recent == "1":
        projects_qs = projects_qs[:8]

    # Stats
    total = UserProject.objects.filter(user=request.user).count()
    with_link = UserProject.objects.filter(user=request.user).exclude(link="").exclude(link__isnull=True).count()
    score = 0
    if total > 0:
        score = min(100, (with_link * 30) + (total * 15))  # simple demo scoring

    # Optional GitHub data (for auto-link suggestion)
    github_data = None
    gh = (getattr(profile, "github_username", "") or "").strip()
    if gh:
        github_data = fetch_github_data(gh)

    # Suggested healthcare projects (1-click add)
    suggested = [
        {
            "title": "Hospital KPI Dashboard",
            "tools": "Excel, SQL, Dashboarding",
            "description": "Build a dashboard for Admissions, Bed Occupancy, ALOS, Discharge rate. Explain insights and decisions.",
        },
        {
            "title": "Patient No-Show Analysis",
            "tools": "SQL, Excel",
            "description": "Analyze appointment no-show patterns by day/time/department. Suggest reduction strategies.",
        },
        {
            "title": "Lab Turnaround Time Reporting",
            "tools": "SQL, Excel, Reporting",
            "description": "Track lab test turnaround time trends. Identify bottlenecks and propose improvement plan.",
        },
        {
            "title": "Healthcare Data Privacy Checklist",
            "tools": "Documentation, Privacy",
            "description": "Create a privacy-first data handling checklist for healthcare datasets (role-based access, masking, audit trail).",
        },
    ]

    existing_titles = set((p.title or "").strip().lower() for p in UserProject.objects.filter(user=request.user))
    suggested = [s for s in suggested if s["title"].lower() not in existing_titles]

    # POST add/update
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        tools_in = (request.POST.get("tools") or "").strip()
        link_in = (request.POST.get("link") or "").strip()

        if not title:
            messages.error(request, "Project title is required.")
            return redirect("projects_page")

        # If user clicked "Use latest GitHub repo link"
        if request.POST.get("use_latest_github") == "1" and github_data and github_data.get("ok"):
            latest = (github_data.get("latest_repo") or {})
            if latest.get("html_url"):
                link_in = latest["html_url"]

        # Update if same title exists
        obj = UserProject.objects.filter(user=request.user, title__iexact=title).first()
        if obj:
            obj.description = description
            obj.tools = tools_in
            obj.link = link_in
            obj.save()
            messages.success(request, f"Project updated: {title}")
        else:
            UserProject.objects.create(
                user=request.user,
                title=title,
                description=description,
                tools=tools_in,
                link=link_in
            )
            messages.success(request, f"Project added: {title}")

        return redirect("projects_page")

    return render(request, "projects_page.html", {
        "profile": profile,
        "projects": projects_qs,

        "q": q,
        "tool": tool,
        "has_link": has_link,
        "recent": recent,

        "total_projects": total,
        "with_link": with_link,
        "portfolio_score": score,

        "suggested": suggested[:8],
        "github_data": github_data,
    })

from django.db.models import Q
from django.views.decorators.http import require_POST

@login_required
def achievements_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.domain = "healthcare"
    profile.save(update_fields=["domain"])

    # Filters
    q = (request.GET.get("q") or "").strip()
    has_proof = (request.GET.get("has_proof") or "").strip()  # "1"
    recent = (request.GET.get("recent") or "").strip()        # "1"

    ach_qs = UserAchievement.objects.filter(user=request.user)

    if q:
        ach_qs = ach_qs.filter(Q(title__icontains=q))

    if has_proof == "1":
        ach_qs = ach_qs.exclude(proof_link="").exclude(proof_link__isnull=True)

    ach_qs = ach_qs.order_by("-date", "-id")

    if recent == "1":
        ach_qs = ach_qs[:10]

    # Stats
    total = UserAchievement.objects.filter(user=request.user).count()
    with_proof = UserAchievement.objects.filter(user=request.user).exclude(proof_link="").exclude(proof_link__isnull=True).count()
    score = 0
    if total > 0:
        score = min(100, (with_proof * 35) + (total * 15))  # simple score for demo

    # Suggested achievements (1-click add)
    suggested = [
        {"title": "Completed: Healthcare Data Privacy Basics", "date": "", "proof_link": ""},
        {"title": "Certificate: SQL for Healthcare Analytics", "date": "", "proof_link": ""},
        {"title": "Workshop: Excel Dashboards for Hospital KPIs", "date": "", "proof_link": ""},
        {"title": "Volunteer: Community Health Data Camp", "date": "", "proof_link": ""},
        {"title": "Hackathon: Healthcare Data Challenge Participation", "date": "", "proof_link": ""},
    ]
    existing = set((a.title or "").strip().lower() for a in UserAchievement.objects.filter(user=request.user))
    suggested = [s for s in suggested if s["title"].lower() not in existing]

    # POST add/update
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        date_str = (request.POST.get("date") or "").strip()
        proof = (request.POST.get("proof_link") or "").strip()

        if not title:
            messages.error(request, "Achievement title is required.")
            return redirect("achievements_page")

        # update if same title exists
        obj = UserAchievement.objects.filter(user=request.user, title__iexact=title).first()
        if obj:
            obj.proof_link = proof
            # date can be blank
            if date_str:
                obj.date = date_str  # Django accepts YYYY-MM-DD
            else:
                obj.date = None
            obj.save()
            messages.success(request, f"Achievement updated: {title}")
        else:
            UserAchievement.objects.create(
                user=request.user,
                title=title,
                date=date_str or None,
                proof_link=proof
            )
            messages.success(request, f"Achievement added: {title}")

        return redirect("achievements_page")

    return render(request, "achievements_page.html", {
        "profile": profile,
        "achievements": ach_qs,

        "q": q,
        "has_proof": has_proof,
        "recent": recent,

        "total_ach": total,
        "with_proof": with_proof,
        "ach_score": score,

        "suggested": suggested[:10],
    })


@require_POST
@login_required
def delete_achievement(request, ach_id):
    UserAchievement.objects.filter(id=ach_id, user=request.user).delete()
    messages.success(request, "Achievement deleted.")
    return redirect("achievements_page")
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required
def ai_advisor_page(request):
    return render(request, "ai_advisor.html")


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def ai_advisor_chat(request):
    msg = (request.POST.get("message") or "").strip().lower()

    profile, _ = Profile.objects.get_or_create(user=request.user)
    target_role = (profile.target_role or "").strip() or DEFAULT_ROLE
    if target_role not in HEALTHCARE_ROLES:
        target_role = DEFAULT_ROLE
    role_data = HEALTHCARE_ROLES[target_role]

    # --- user data ---
    skills_qs = UserSkill.objects.filter(user=request.user)
    courses_qs = UserCourse.objects.filter(user=request.user)
    projects_count = UserProject.objects.filter(user=request.user).count()

    # map skills
    user_skills = {
        (s.name or "").strip().lower(): int(s.level or 0)
        for s in skills_qs
        if (s.name or "").strip()
    }

    readiness, gaps = _compute_readiness(user_skills, role_data.get("skills", {}))

    # course history
    existing_courses = set((c.title or "").strip().lower() for c in courses_qs)
    completed_courses = set((c.title or "").strip().lower() for c in courses_qs.filter(status="completed"))

    # helper: recommend new courses based on gaps + course history
    def suggest_new_courses():
        suggestions = []

        # gap-based suggestions
        for g in gaps[:5]:
            s = g["skill"].lower()

            if "sql" in s:
                suggestions += [
                    "SQL for Healthcare Data Analysis (Intermediate)",
                    "SQL Window Functions for Healthcare Reporting",
                ]
            elif "excel" in s:
                suggestions += [
                    "Excel Dashboards for Hospital KPI Reporting",
                    "Excel Power Query for Healthcare Data Cleaning",
                ]
            elif "privacy" in s or "hipaa" in s:
                suggestions += [
                    "Healthcare Data Privacy & Compliance (HIPAA-like) Basics",
                    "De-identification & PHI Handling for Analytics",
                ]
            elif "terminology" in s:
                suggestions += [
                    "Medical Terminology for Healthcare Analytics",
                    "ICD-10 & CPT Basics for Data Professionals",
                ]
            elif "quality" in s or "clean" in s:
                suggestions += [
                    "Clinical Data Quality & Validation Fundamentals",
                    "Data Cleaning for Healthcare: Missing Values & Codes",
                ]
            elif "dashboard" in s:
                suggestions += [
                    "Power BI for Healthcare Dashboards (Beginner)",
                    "KPI Storytelling for Hospital Operations",
                ]
            else:
                suggestions.append(f"{g['skill']} Fundamentals (Healthcare Context)")

        # role-based extras
        suggestions += (role_data.get("courses") or [])

        # If user already completed beginner courses, recommend intermediate
        if any("sql" in c for c in completed_courses):
            suggestions.append("Advanced SQL: Performance + Indexing for Reporting")
        if any("excel" in c for c in completed_courses):
            suggestions.append("Advanced Excel: Modeling + Scenario Analysis for Healthcare")

        # remove duplicates + already existing
        cleaned = []
        seen = set()
        for s in suggestions:
            key = s.strip().lower()
            if not key or key in seen or key in existing_courses:
                continue
            seen.add(key)
            cleaned.append(s)

        return cleaned[:8]

    def format_list(items):
        return "\n".join([f"• {x}" for x in items]) if items else "No new recommendations right now."

    # --- intents ---
    if "recommend" in msg or "suggest" in msg or "course" in msg or "learn" in msg:
        new_courses = suggest_new_courses()
        reply = (
            f"Based on your profile + past courses, here are **new healthcare courses** you should add next:\n"
            f"{format_list(new_courses)}\n\n"
            f"Target role: **{target_role}**\n"
            f"Readiness: **{readiness}%**"
        )
        if projects_count < 1:
            reply += "\n\nTip: Add **1 healthcare project** to make your profile stronger."
        return JsonResponse({"ok": True, "reply": reply})

    if "readiness" in msg or "score" in msg:
        reply = f"Your readiness for **{target_role}** is **{readiness}%**."
        if gaps:
            reply += "\nTop gaps:\n" + "\n".join([f"• {g['skill']} (+{g['missing']} levels)" for g in gaps[:3]])
        return JsonResponse({"ok": True, "reply": reply})

    if "gap" in msg or "missing" in msg:
        if not gaps:
            return JsonResponse({"ok": True, "reply": "You have no major gaps. Add more projects + proof links to strengthen your portfolio."})
        reply = "Your biggest gaps are:\n" + "\n".join([f"• {g['skill']} (+{g['missing']} levels)" for g in gaps[:5]])
        return JsonResponse({"ok": True, "reply": reply})

    # default
    reply = (
        "Hi! I’m your **Healthcare AI Course Advisor** 🤖\n\n"
        "Ask me:\n"
        "• suggest courses\n"
        "• what should I learn next\n"
        "• readiness\n"
        "• gaps\n"
    )
    return JsonResponse({"ok": True, "reply": reply})

@require_POST
@login_required
def delete_project(request, project_id):
    UserProject.objects.filter(id=project_id, user=request.user).delete()
    messages.success(request, "Project deleted.")
    return redirect("projects_page")

@require_POST
@login_required
def delete_course(request, course_id):
    UserCourse.objects.filter(id=course_id, user=request.user).delete()
    messages.success(request, "Course removed.")
    return redirect("courses_page")

@require_POST
@login_required
def delete_skill(request, skill_id):
    UserSkill.objects.filter(id=skill_id, user=request.user).delete()
    messages.success(request, "Skill removed.")
    return redirect("skills_page")
from django.db import transaction
@login_required
def profile_builder(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        names = request.POST.getlist("skill_name[]")
        levels = request.POST.getlist("skill_level[]")

        # clean & pair safely
        pairs = []
        for n, lv in zip(names, levels):
            n = (n or "").strip()
            if not n:
                continue
            try:
                lv = int(lv)
            except:
                lv = 1
            lv = max(1, min(5, lv))  # clamp to 1..5
            pairs.append((n, lv))

        # replace old skills with new skills
        with transaction.atomic():
            UserSkill.objects.filter(user=request.user).delete()
            UserSkill.objects.bulk_create([
                UserSkill(user=request.user, name=n, level=lv)
                for n, lv in pairs
            ])

        messages.success(request, "Skills updated!")
        return redirect("skills_page")

    skills = UserSkill.objects.filter(user=request.user).order_by("-level", "name")
    return render(request, "skills.html", {"profile": profile, "skills": skills})
    if request.method == "POST":
        profile.github_username = (request.POST.get("github_username") or "").strip()
        profile.headline = (request.POST.get("headline") or "").strip()
        profile.bio = (request.POST.get("bio") or "").strip()
        profile.target_role = (request.POST.get("target_role") or "").strip()
        profile.domain = "healthcare"
        profile.save()

        messages.success(request, "Profile saved successfully!")
        return redirect("profile_builder")

    github_data = None
    gh = (profile.github_username or "").strip()
    github_data = fetch_github_data(gh) if gh else None
    if gh:
        github_data = fetch_github_data(gh)  # <-- make sure this exact function exists

    skills = UserSkill.objects.filter(user=request.user).order_by("-level", "name")
    courses = UserCourse.objects.filter(user=request.user).order_by("-id")
    projects = UserProject.objects.filter(user=request.user).order_by("-created_at")
    achievements = UserAchievement.objects.filter(user=request.user).order_by("-id")

    return render(request, "profile_builder.html", {
        "profile": profile,
        "skills": skills,
        "courses": courses,
        "projects": projects,
        "achievements": achievements,
        "github_data": github_data,
    })


def home_view(request):
    return render(request, "dashboard.html")
