"""Main URL Configuration

Root URL patterns for the Django application.
Routes requests to appropriate apps and views.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Dashboard page and API at /dashboard/ and /api/dashboard/
    # The dashboard urls.py contains both page patterns and API patterns
    # They are differentiated by path, not by separate includes
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("api/dashboard/", include("apps.dashboard.urls", namespace="api_dashboard")),
    # Redirect root to dashboard
    path("", RedirectView.as_view(url="/dashboard/", permanent=True)),
]
