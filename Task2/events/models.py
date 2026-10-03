import secrets, string
from pathlib import Path
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.templatetags.static import static
from django.utils import timezone
from django.utils.text import slugify

CATEGORIES = [("tech","Tech"),("music","Music"),("art","Art"),("sports","Sports"),
              ("food","Food"),("business","Business"),("workshop","Workshop")]
THEME = {"tech":("#2f6fb0","#dbe8f6"),"music":("#8e3fa8","#eadcf3"),"art":("#e8590c","#fde5d0"),
         "sports":("#2e8b57","#d9efdf"),"food":("#c98a00","#fbefc6"),"business":("#1f7a8c","#d6ecef"),
         "workshop":("#c2185b","#f9d9e5")}
IMG_DIR = Path(__file__).resolve().parent / "static" / "events" / "img"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES)
    venue = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    start = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="organized_events")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["start"]
    def __str__(self): return self.title
    @property
    def booked(self):
        return self.registrations.filter(status="confirmed").aggregate(n=Sum("tickets"))["n"] or 0
    @property
    def seats_left(self): return max(self.capacity - self.booked, 0)
    @property
    def is_full(self): return self.seats_left == 0
    @property
    def is_past(self): return self.start < timezone.now()
    @property
    def percent_full(self): return min(100, int(100 * self.booked / self.capacity)) if self.capacity else 100
    @property
    def color(self): return THEME.get(self.category, THEME["tech"])[0]
    @property
    def tint(self): return THEME.get(self.category, THEME["tech"])[1]
    @property
    def image_url(self):
        s = slugify(self.title)
        for ext in ("jpg", "jpeg", "png", "webp", "svg"):
            if (IMG_DIR / f"{s}.{ext}").exists(): return static(f"events/img/{s}.{ext}")
        return static(f"events/img/cat-{self.category}.svg")

def _code(): return "EVT-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

class Registration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    tickets = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=10, default="confirmed",
        choices=[("confirmed","Confirmed"),("cancelled","Cancelled")])
    code = models.CharField(max_length=12, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.code} - {self.name} - {self.event}"
    @property
    def amount(self): return self.tickets * self.event.price
    def save(self, *a, **k):
        while not self.code:
            c = _code()
            if not Registration.objects.filter(code=c).exists(): self.code = c
        super().save(*a, **k)
