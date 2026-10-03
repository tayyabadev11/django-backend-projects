from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
admin.site.site_header = "Event Registration System"
admin.site.site_title = "Event Registration System"
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("events.urls")),
]
