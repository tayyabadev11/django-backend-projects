import csv
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import services
from .models import CATEGORIES, InventoryItem, MenuItem, Order, Reservation


# ------------------------------------------------------------- helpers

def _is_staff(user):
    return user.is_authenticated and user.is_active and user.is_staff


def staff_api(view):
    """JSON endpoints that only logged-in staff may use."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not _is_staff(request.user):
            return JsonResponse({"error": "Staff login required."}, status=403)
        return view(request, *args, **kwargs)
    return wrapper


def _body(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _money(value):
    return float(value)


def _local(dt, fmt="%a %d %b, %H:%M"):
    return timezone.localtime(dt).strftime(fmt)


def _parse_start(value):
    try:
        start = datetime.fromisoformat(str(value))
    except ValueError:
        raise services.ReservationError("Please choose a valid date and time.")
    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    return start


def _parse_day(value):
    if not value:
        return timezone.localdate()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# --------------------------------------------------------------- pages

def home(request):
    return render(request, "restaurant/index.html")


class StaffAuthForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError("This account does not have staff access.", code="no_staff")


class StaffLoginView(LoginView):
    template_name = "restaurant/login.html"
    authentication_form = StaffAuthForm
    redirect_authenticated_user = True


@user_passes_test(_is_staff, login_url="dashboard-login")
def dashboard(request):
    return render(request, "restaurant/dashboard.html")


# ------------------------------------------------- public API: menu

@require_GET
def api_menu(request):
    items = (
        MenuItem.objects.filter(is_available=True)
        .order_by("id")
        .prefetch_related("ingredients__inventory_item")
    )
    grouped = {key: [] for key, _ in CATEGORIES}
    for m in items:
        grouped[m.category].append({
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "price": _money(m.price),
            "image": static("images/" + m.image) if m.image else "",
            "in_stock": m.in_stock(),
        })
    return JsonResponse({
        "categories": [
            {"key": key, "label": label, "items": grouped[key]}
            for key, label in CATEGORIES if grouped[key]
        ]
    })


# ------------------------------------------------------ orders API

def _order_json(order):
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "table_number": order.table_number,
        "status": order.status,
        "total": _money(order.total),
        "time": _local(order.created_at, "%d %b, %H:%M"),
        "items": ", ".join(f"{i.quantity} x {i.menu_item.name}" for i in order.items.all()),
    }


@require_http_methods(["GET", "POST"])
def orders_collection(request):
    if request.method == "POST":
        return _create_order(request)
    return _list_orders(request)


def _create_order(request):
    data = _body(request)
    if data is None:
        return _error("Invalid request body.")
    lines = [(row.get("id"), row.get("quantity")) for row in data.get("items", []) if isinstance(row, dict)]
    table = data.get("table_number")
    try:
        table = int(table) if table not in (None, "") else None
        order = services.place_order(data.get("customer_name"), table, lines)
    except (TypeError, ValueError):
        return _error("Table number must be a whole number.")
    except services.OrderError as exc:
        return _error(str(exc))
    return JsonResponse({"id": order.id, "total": _money(order.total), "status": order.status}, status=201)


@staff_api
def _list_orders(request):
    qs = Order.objects.prefetch_related("items__menu_item")
    status = request.GET.get("status")
    if status in dict(Order.STATUSES):
        qs = qs.filter(status=status)
    return JsonResponse({
        "statuses": [{"key": k, "label": v} for k, v in Order.STATUSES],
        "orders": [_order_json(o) for o in qs[:60]],
    })


@staff_api
@require_POST
def order_status(request, pk):
    data = _body(request) or {}
    status = data.get("status")
    if status not in dict(Order.STATUSES):
        return _error("Unknown status.")
    updated = Order.objects.filter(pk=pk).update(status=status)
    if not updated:
        return _error("Order not found.", 404)
    return JsonResponse({"id": pk, "status": status})


# --------------------------------------------------- inventory API

def _inventory_json(item):
    return {
        "id": item.id,
        "name": item.name,
        "unit": item.unit,
        "quantity": _money(item.quantity),
        "reorder_level": _money(item.reorder_level),
        "is_low": item.is_low,
    }


@staff_api
@require_GET
def inventory_list(request):
    items = InventoryItem.objects.all()
    return JsonResponse({
        "items": [_inventory_json(i) for i in items],
        "low_stock": [_inventory_json(i) for i in items if i.is_low],
    })


@staff_api
@require_POST
def inventory_restock(request, pk):
    data = _body(request) or {}
    try:
        amount = Decimal(str(data.get("amount")))
    except InvalidOperation:
        return _error("Enter a valid amount.")
    if not amount.is_finite() or amount <= 0 or amount > 100000:
        return _error("Amount must be greater than zero.")
    with transaction.atomic():
        try:
            item = InventoryItem.objects.select_for_update().get(pk=pk)
        except InventoryItem.DoesNotExist:
            return _error("Inventory item not found.", 404)
        item.quantity += amount
        item.save(update_fields=["quantity"])
    return JsonResponse(_inventory_json(item))


# ------------------------------------------------------ reports API

def _report_json(report):
    return {
        "date": report["date"],
        "orders": report["orders"],
        "revenue": _money(report["revenue"]),
        "average": round(_money(report["average"]), 2),
        "top_items": [
            {"name": t["name"], "quantity": t["quantity"], "revenue": _money(t["revenue"])}
            for t in report["top_items"]
        ],
    }


@staff_api
@require_GET
def sales_report_json(request):
    day = _parse_day(request.GET.get("date"))
    if day is None:
        return _error("Date must look like 2026-10-01.")
    return JsonResponse(_report_json(services.sales_report(day)))


@staff_api
@require_GET
def sales_report_csv(request):
    day = _parse_day(request.GET.get("date"))
    if day is None:
        return _error("Date must look like 2026-10-01.")
    report = services.sales_report(day)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="red-spoon-sales-{day.isoformat()}.csv"'
    writer = csv.writer(response)
    writer.writerow(["The Red Spoon daily sales report", report["date"]])
    writer.writerow(["Orders", report["orders"]])
    writer.writerow(["Revenue (Rs.)", f"{report['revenue']:.2f}"])
    writer.writerow(["Average order (Rs.)", f"{report['average']:.2f}"])
    writer.writerow([])
    writer.writerow(["Top selling items", "Quantity", "Revenue (Rs.)"])
    for t in report["top_items"]:
        writer.writerow([t["name"], t["quantity"], f"{t['revenue']:.2f}"])
    return response


# ------------------------------------------------ reservations API

def _reservation_json(r):
    return {
        "id": r.id,
        "customer_name": r.customer_name,
        "phone": r.phone,
        "guests": r.guests,
        "table": r.table.number,
        "start": _local(r.start_time),
        "end": _local(r.end_time, "%H:%M"),
        "status": r.status,
    }


@require_GET
def reservation_availability(request):
    try:
        guests = int(request.GET.get("guests", ""))
        if guests < 1:
            raise ValueError
        start = _parse_start(request.GET.get("start"))
        services.validate_slot(start)
    except ValueError:
        return _error("Enter the number of guests.")
    except services.ReservationError as exc:
        return _error(str(exc))
    tables = services.available_tables(start, guests)
    return JsonResponse({
        "tables": [{"id": t.id, "number": t.number, "capacity": t.capacity} for t in tables]
    })


@require_http_methods(["GET", "POST"])
def reservations_collection(request):
    if request.method == "POST":
        return _create_reservation(request)
    return _list_reservations(request)


def _create_reservation(request):
    data = _body(request)
    if data is None:
        return _error("Invalid request body.")
    try:
        start = _parse_start(data.get("start"))
        reservation = services.reserve_table(
            data.get("customer_name"), data.get("phone"), data.get("guests"),
            start, data.get("table_id") or None,
        )
    except services.ReservationError as exc:
        return _error(str(exc))
    return JsonResponse(_reservation_json(reservation), status=201)


@staff_api
def _list_reservations(request):
    today = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    qs = Reservation.objects.select_related("table").filter(start_time__gte=today)[:100]
    return JsonResponse({"reservations": [_reservation_json(r) for r in qs]})


@staff_api
@require_POST
def reservation_cancel(request, pk):
    updated = Reservation.objects.filter(pk=pk).update(status=Reservation.CANCELLED)
    if not updated:
        return _error("Reservation not found.", 404)
    return JsonResponse({"id": pk, "status": Reservation.CANCELLED})
