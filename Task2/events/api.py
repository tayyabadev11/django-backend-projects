import json
from functools import wraps
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from . import services
from .models import Event, Registration

def _event(e):
    return {"id": e.id, "title": e.title, "description": e.description, "category": e.category, "venue": e.venue,
            "city": e.city, "start": e.start.isoformat(), "price": float(e.price), "capacity": e.capacity,
            "seats_left": e.seats_left, "image": e.image_url}

def _reg(r):
    return {"id": r.id, "code": r.code, "status": r.status, "tickets": r.tickets, "name": r.name,
            "amount": float(r.amount), "registered_at": r.created_at.isoformat(), "event": _event(r.event)}

def _err(msg, code=400): return JsonResponse({"error": msg}, status=code)

def login_required_api(f):
    @wraps(f)
    def w(request, *a, **k):
        if not request.user.is_authenticated: return _err("Login required", 401)
        return f(request, *a, **k)
    return w

@require_GET
def events(request):
    qs = Event.objects.filter(is_published=True, start__gte=timezone.now())
    cat, q = request.GET.get("category"), request.GET.get("q")
    if cat: qs = qs.filter(category=cat)
    if q: qs = qs.filter(Q(title__icontains=q) | Q(city__icontains=q))
    return JsonResponse([_event(e) for e in qs], safe=False)

@require_GET
def event_detail(request, pk):
    try: e = Event.objects.get(pk=pk, is_published=True)
    except Event.DoesNotExist: return _err("Event not found", 404)
    return JsonResponse(_event(e))

@require_POST
@login_required_api
def register(request, pk):
    try: e = Event.objects.get(pk=pk, is_published=True)
    except Event.DoesNotExist: return _err("Event not found", 404)
    try:
        d = json.loads(request.body or "{}")
        name, phone, tickets = str(d["name"]).strip(), str(d.get("phone", "")), int(d.get("tickets", 1))
        if not name: raise ValueError
    except (KeyError, ValueError, TypeError): return _err("Provide 'name' and (optionally) 'phone' and 'tickets'")
    try: r = services.register(request.user, e, name, phone, tickets)
    except services.RegError as ex: return _err(str(ex), 409)
    return JsonResponse(_reg(r), status=201)

@require_GET
@login_required_api
def my_registrations(request):
    return JsonResponse([_reg(r) for r in request.user.registrations.select_related("event")], safe=False)

@require_POST
@login_required_api
def cancel(request, pk):
    try: r = Registration.objects.select_related("event").get(pk=pk, user=request.user)
    except Registration.DoesNotExist: return _err("Registration not found", 404)
    try: services.cancel(r, request.user)
    except services.RegError as ex: return _err(str(ex), 409)
    return JsonResponse(_reg(r))
