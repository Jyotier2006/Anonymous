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
        # contribution is capped at required level
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

@login_required
def student_dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Choose target role
    target_role = (profile.target_role or "").strip()
    if target_role not in HEALTHCARE_ROLES:
        target_role = "Health Data Assistant"

    role_data = HEALTHCARE_ROLES[target_role]
    role_req = role_data["skills"]

    # Fetch user data
    user_skills_map = {s.name.lower(): int(s.level) for s in skills_qs}


    user_skills_map = {s.name.lower(): int(s.level) for s in skills_qs}

    readiness, gaps = _compute_readiness(user_skills_map, role_req)

    # Simple recommendation engine (based on top gaps)
    top_gaps = gaps[:5]
    recommendations = []
    for g in top_gaps:
        # map gap -> suggestion bucket
        if "sql" in g["skill"].lower():
            recommendations.append({"type": "course", "title": "SQL for Data Analysis", "why": "Directly closes your SQL gap."})
            recommendations.append({"type": "project", "title": "Patient appointment analytics (SQL queries + report)", "why": "Shows real SQL usage."})
        elif "excel" in g["skill"].lower():
            recommendations.append({"type": "course", "title": "Excel Pivot + Dashboarding", "why": "Improves reporting speed and accuracy."})
            recommendations.append({"type": "project", "title": "Hospital KPI dashboard (Excel)", "why": "Strong portfolio project for entry roles."})
        elif "privacy" in g["skill"].lower():
            recommendations.append({"type": "course", "title": "Healthcare Data Privacy basics", "why": "High weight skill, improves trust and compliance."})
        elif "terminology" in g["skill"].lower():
            recommendations.append({"type": "course", "title": "Medical Terminology essentials", "why": "Helps you understand healthcare datasets."})
        else:
            recommendations.append({"type": "practice", "title": f"Practice {g['skill']} with mini tasks", "why": "Small daily practice boosts level quickly."})

    # Remove duplicate titles
    seen = set()
    recommendations_unique = []
    for r in recommendations:
        key = (r["type"], r["title"])
        if key not in seen:
            seen.add(key)
            recommendations_unique.append(r)

    next_actions = _next_actions(profile, readiness, gaps, courses_qs.count(), projects_qs.count())

    # Roadmap (7-day plan)
    roadmap_7 = []
    if gaps:
        focus = gaps[0]["skill"]
        roadmap_7 = [
            {"day": "Day 1", "task": f"Set goal + baseline test for {focus} (20–30 min)"},
            {"day": "Day 2", "task": f"Watch 1 lesson + take notes (30 min)"},
            {"day": "Day 3", "task": f"Do 5 practice questions/tasks (30–45 min)"},
            {"day": "Day 4", "task": f"Apply {focus} in a mini dataset task (45 min)"},
            {"day": "Day 5", "task": "Update your profile with progress + evidence"},
            {"day": "Day 6", "task": "Build 1 small portfolio artifact (report/dashboard/query)"},
            {"day": "Day 7", "task": "Review gaps again + plan next week"},
        ]

    context = {
        "profile": profile,
        "target_role": target_role,
        "role_data": role_data,
        "roles_list": list(HEALTHCARE_ROLES.keys()),
        "readiness": readiness,
        "gaps": gaps[:12],
        "skills_count": skills_qs.count(),
        "courses_count": courses_qs.count(),
        "projects_count": projects_qs.count(),
        "ach_count": ach_qs.count(),
        "recommendations": recommendations_unique[:10],
        "next_actions": next_actions,
        "roadmap_7": roadmap_7,
    }
    return render(request, "student_dashboard.html", context)
