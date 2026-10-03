from django.contrib import admin
from django.utils import timezone
from .models import Event, Registration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "city", "start", "capacity", "seats", "price", "is_published")
    list_filter = ("category", "city", "is_published")
    search_fields = ("title", "venue", "city")
    @admin.display(description="Seats left")
    def seats(self, o): return o.seats_left
    def save_model(self, request, obj, form, change):
        if not obj.organizer: obj.organizer = request.user
        super().save_model(request, obj, form, change)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "event", "user", "tickets", "status", "created_at")
    list_filter = ("status", "event")
    search_fields = ("code", "name", "user__username")
    actions = ["cancel_selected"]
    @admin.action(description="Cancel selected registrations")
    def cancel_selected(self, request, qs): qs.update(status="cancelled", cancelled_at=timezone.now())
