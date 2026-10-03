import csv
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from . import services
from .forms import RegistrationForm
from .models import CATEGORIES, Event, Registration

def home(request):
    upcoming = Event.objects.filter(is_published=True, start__gte=timezone.now())
    cat, q = request.GET.get("category", ""), request.GET.get("q", "").strip()
    events = upcoming
    if cat: events = events.filter(category=cat)
    if q: events = events.filter(Q(title__icontains=q) | Q(city__icontains=q) | Q(venue__icontains=q))
    return render(request, "events/home.html", {"events": list(events), "featured": list(upcoming[:3]),
        "categories": CATEGORIES, "cat": cat, "q": q})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    user = request.user
    mine = Registration.objects.filter(user=user, event=event, status="confirmed").first() if user.is_authenticated else None
    if request.method == "POST":
        if not user.is_authenticated: return redirect_to_login(request.get_full_path())
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try: reg = services.register(user, event, **form.cleaned_data)
            except services.RegError as e: messages.error(request, str(e))
            else:
                messages.success(request, f"You are registered. Your confirmation code is {reg.code}.")
                return redirect("my_registrations")
    else:
        name = (user.get_full_name() or user.username) if user.is_authenticated else ""
        form = RegistrationForm(initial={"name": name, "tickets": 1})
    return render(request, "events/detail.html", {"event": event, "mine": mine, "form": form})

@login_required
def my_registrations(request):
    regs = list(request.user.registrations.select_related("event"))
    upcoming = [r for r in regs if r.status == "confirmed" and not r.event.is_past]
    return render(request, "events/mine.html", {"upcoming": upcoming, "history": [r for r in regs if r not in upcoming]})

@login_required
@require_POST
def cancel_registration(request, pk):
    reg = get_object_or_404(Registration, pk=pk, user=request.user)
    try: services.cancel(reg, request.user)
    except services.RegError as e: messages.error(request, str(e))
    else: messages.success(request, f"Registration {reg.code} cancelled.")
    return redirect("my_registrations")

def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Welcome! Your account is ready.")
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})

@staff_member_required
def organizer(request):
    return render(request, "events/organizer.html", {"events": Event.objects.all()})

@staff_member_required
def organizer_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    regs = event.registrations.select_related("user")
    if request.GET.get("csv"):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="attendees-{event.pk}.csv"'
        w = csv.writer(resp); w.writerow(["Code", "Name", "Username", "Phone", "Tickets", "Status", "Registered at"])
        for r in regs: w.writerow([r.code, r.name, r.user.username, r.phone, r.tickets, r.status,
                                   timezone.localtime(r.created_at).strftime("%Y-%m-%d %H:%M")])
        return resp
    return render(request, "events/organizer_event.html", {"event": event, "regs": regs})
