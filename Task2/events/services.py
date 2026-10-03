from django.db import transaction
from django.utils import timezone
from .models import Event, Registration

MAX_TICKETS = 5

class RegError(Exception):
    """A user-facing reason why a registration or cancellation failed."""

@transaction.atomic
def register(user, event, name, phone, tickets):
    """Register `user` for `event`: checks availability, capacity and duplicates."""
    event = Event.objects.select_for_update().get(pk=event.pk)
    if not event.is_published: raise RegError("This event is not available.")
    if event.is_past: raise RegError("This event has already taken place.")
    if not 1 <= tickets <= MAX_TICKETS: raise RegError(f"You can book between 1 and {MAX_TICKETS} tickets.")
    if Registration.objects.filter(user=user, event=event, status="confirmed").exists():
        raise RegError("You are already registered for this event.")
    if event.is_full: raise RegError("Sorry, this event is sold out.")
    if tickets > event.seats_left: raise RegError(f"Only {event.seats_left} seat(s) left.")
    return Registration.objects.create(user=user, event=event, name=name, phone=phone, tickets=tickets)

@transaction.atomic
def cancel(registration, user):
    """Cancel a registration; only its owner can do so, and only before the event starts."""
    if registration.user_id != user.id: raise RegError("This is not your registration.")
    if registration.status == "cancelled": raise RegError("Already cancelled.")
    if registration.event.is_past: raise RegError("Past events cannot be cancelled.")
    registration.status = "cancelled"
    registration.cancelled_at = timezone.now()
    registration.save()
    return registration
