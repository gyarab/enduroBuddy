from django.shortcuts import redirect, render
from django.urls import reverse


def public_home(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard_home"))
    return render(request, "public/home.html", {"current_public_page": "home"})


def public_about(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard_home"))
    return render(request, "public/about.html", {"current_public_page": "about"})


def public_terms(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard_home"))
    return render(request, "public/terms.html", {"current_public_page": "terms"})


def public_privacy(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard_home"))
    return render(request, "public/privacy.html", {"current_public_page": "privacy"})
