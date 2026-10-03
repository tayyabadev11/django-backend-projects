from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from events import services
from events.models import Event, Registration
from events.seed_data import EVENTS

class Command(BaseCommand):
    help = "Load demo events, an organizer account and a demo user"
    def handle(self, *a, **o):
        org, made = User.objects.get_or_create(username="organizer", defaults=dict(is_staff=True, is_superuser=True, first_name="Event", last_name="Organizer"))
        if made: org.set_password("organizer123"); org.save()
        demo, made = User.objects.get_or_create(username="demo", defaults=dict(first_name="Demo", last_name="User"))
        if made: demo.set_password("demo12345"); demo.save()
        base = timezone.localtime().replace(minute=0, second=0, microsecond=0)
        for d in EVENTS:
            start = (base + timedelta(days=d["days"])).replace(hour=d["hour"])
            e, new = Event.objects.get_or_create(title=d["title"], defaults=dict(category=d["category"], description=d["description"],
                venue=d["venue"], city=d["city"], start=start, capacity=d["capacity"], price=d["price"], organizer=org))
            if new:
                for i in range(d["sold"]):
                    g, made = User.objects.get_or_create(username=f"guest{i+1}")
                    if made: g.set_unusable_password(); g.save()
                    Registration.objects.create(user=g, event=e, name=f"Guest {i+1}", tickets=1)
        for t in ("Code and Coffee: Django Meetup", "Startup Pitch Night"):
            e = Event.objects.filter(title=t).first()
            if e and not Registration.objects.filter(user=demo, event=e).exists():
                services.register(demo, e, "Demo User", "03001234567", 1)
        self.stdout.write("Seeded.  Organizer: organizer / organizer123   Demo user: demo / demo12345  (development only)")
