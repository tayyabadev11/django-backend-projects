from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "The Red Spoon Administration"
admin.site.site_title = "The Red Spoon Admin"
admin.site.index_title = "Manage the restaurant"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("restaurant.urls")),
]
