from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

CATS = [("tech", "Tech"), ("music", "Music"), ("art", "Art"), ("sports", "Sports"), ("food", "Food"), ("business", "Business"), ("workshop", "Workshop")]

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Event", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=200)),
            ("description", models.TextField()),
            ("category", models.CharField(choices=CATS, max_length=20)),
            ("venue", models.CharField(max_length=200)),
            ("city", models.CharField(max_length=100)),
            ("start", models.DateTimeField()),
            ("capacity", models.PositiveIntegerField(default=50)),
            ("price", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
            ("is_published", models.BooleanField(default=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("organizer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organized_events", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["start"]}),
        migrations.CreateModel(name="Registration", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=100)),
            ("phone", models.CharField(blank=True, max_length=20)),
            ("tickets", models.PositiveSmallIntegerField(default=1)),
            ("status", models.CharField(choices=[("confirmed", "Confirmed"), ("cancelled", "Cancelled")], default="confirmed", max_length=10)),
            ("code", models.CharField(blank=True, max_length=12, unique=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("cancelled_at", models.DateTimeField(blank=True, null=True)),
            ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registrations", to="events.event")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registrations", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-created_at"]}),
    ]
