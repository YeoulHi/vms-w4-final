"""Main URL Configuration

Root URL patterns for the Django application.
Routes requests to appropriate apps and views.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
            next_page="/dashboard/"
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    # Dashboard page and API at /dashboard/ and /api/dashboard/
    # The dashboard urls.py contains both page patterns and API patterns
    # They are differentiated by path, not by separate includes
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("api/dashboard/", include("apps.dashboard.urls", namespace="api_dashboard")),
    # Root path - redirect authenticated users to dashboard, others to login
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
]
