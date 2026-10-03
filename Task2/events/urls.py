from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.home, name="home"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("my-registrations/", views.my_registrations, name="my_registrations"),
    path("my-registrations/<int:pk>/cancel/", views.cancel_registration, name="cancel_registration"),
    path("signup/", views.signup, name="signup"),
    path("organizer/", views.organizer, name="organizer"),
    path("organizer/<int:pk>/", views.organizer_event, name="organizer_event"),
    # JSON API
    path("api/events/", api.events),
    path("api/events/<int:pk>/", api.event_detail),
    path("api/events/<int:pk>/register/", api.register),
    path("api/registrations/", api.my_registrations),
    path("api/registrations/<int:pk>/cancel/", api.cancel),
]
