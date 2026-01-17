from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile, UserSkill, UserCourse, UserProject, UserAchievement

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

        for name, lvl in zip(request.POST.getlist("skill_name[]"), request.POST.getlist("skill_level[]")):
            name = (name or "").strip()
            if name:
                UserSkill.objects.create(user=request.user, name=name, level=max(0, min(5, _to_int(lvl, 0))))

        for t, p, s, h in zip(
            request.POST.getlist("course_title[]"),
            request.POST.getlist("course_provider[]"),
            request.POST.getlist("course_status[]"),
            request.POST.getlist("course_hours[]"),
        ):
            t = (t or "").strip()
            if t:
                UserCourse.objects.create(
                    user=request.user,
                    title=t,
                    provider=(p or "").strip(),
                    status=(s or "in_progress"),
                    hours=max(0, _to_int(h, 0)),
                )

        for t, d, tools, link in zip(
            request.POST.getlist("project_title[]"),
            request.POST.getlist("project_desc[]"),
            request.POST.getlist("project_tools[]"),
            request.POST.getlist("project_link[]"),
        ):
            t = (t or "").strip()
            if t:
                UserProject.objects.create(
                    user=request.user,
                    title=t,
                    description=(d or "").strip(),
                    tools=(tools or "").strip(),
                    link=(link or "").strip(),
                )

        for t, dt, link in zip(
            request.POST.getlist("ach_title[]"),
            request.POST.getlist("ach_date[]"),
            request.POST.getlist("ach_link[]"),
        ):
            t = (t or "").strip()
            if t:
                UserAchievement.objects.create(
                    user=request.user,
                    title=t,
                    date=dt or None,
                    proof_link=(link or "").strip(),
                )

        messages.success(request, "Profile saved successfully!")
        return redirect("profile_builder")

    return render(request, "profile_builder.html", {
        "profile": profile,
        "skills": UserSkill.objects.filter(user=request.user),
        "courses": UserCourse.objects.filter(user=request.user),
        "projects": UserProject.objects.filter(user=request.user),
        "achievements": UserAchievement.objects.filter(user=request.user),
    })
