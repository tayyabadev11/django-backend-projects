"""Business rules: ordering, inventory deduction, table availability, reports."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from .models import InventoryItem, MenuItem, Order, OrderItem, Reservation, Table


class OrderError(Exception):
    pass


class ReservationError(Exception):
    pass


# ---------------------------------------------------------------- orders

def place_order(customer_name, table_number, lines):
    """Create an order and deduct ingredients from inventory.

    Everything happens inside one database transaction. If any ingredient
    is short, nothing is saved and the whole order is rejected.
    """
    merged = defaultdict(int)
    for item_id, qty in lines:
        try:
            item_id, qty = int(item_id), int(qty)
        except (TypeError, ValueError):
            raise OrderError("One of the order lines is invalid.")
        if qty < 1 or qty > 20:
            raise OrderError("Quantity must be between 1 and 20.")
        merged[item_id] += qty
    if not merged:
        raise OrderError("Your cart is empty.")

    with transaction.atomic():
        items = {
            m.id: m
            for m in MenuItem.objects.filter(id__in=merged, is_available=True)
            .prefetch_related("ingredients")
        }
        if len(items) != len(merged):
            raise OrderError("One of the dishes is no longer available.")

        # Total ingredients needed for the whole order
        needed = defaultdict(Decimal)
        for item_id, qty in merged.items():
            for ing in items[item_id].ingredients.all():
                needed[ing.inventory_item_id] += ing.quantity * qty

        stock = {
            s.id: s
            for s in InventoryItem.objects.select_for_update().filter(id__in=needed.keys())
        }
        short = {i for i, qty in needed.items() if stock[i].quantity < qty}
        if short:
            names = [
                items[item_id].name
                for item_id in merged
                if any(ing.inventory_item_id in short for ing in items[item_id].ingredients.all())
            ]
            raise OrderError(
                "Not enough stock to prepare: " + ", ".join(names) + ". Nothing was ordered."
            )

        order = Order.objects.create(
            customer_name=(customer_name or "Guest").strip()[:80] or "Guest",
            table_number=table_number or None,
        )
        total = Decimal("0")
        for item_id, qty in merged.items():
            item = items[item_id]
            OrderItem.objects.create(
                order=order, menu_item=item, quantity=qty, unit_price=item.price
            )
            total += item.price * qty

        for inv_id, qty in needed.items():
            stock[inv_id].quantity -= qty
            stock[inv_id].save(update_fields=["quantity"])

        order.total = total
        order.save(update_fields=["total"])
    return order


# ---------------------------------------------------------- reservations

def _minutes():
    return settings.RESTAURANT["RESERVATION_MINUTES"]


def validate_slot(start):
    if start <= timezone.now():
        raise ReservationError("Please choose a time in the future.")
    hour = timezone.localtime(start).hour
    cfg = settings.RESTAURANT
    if not (cfg["OPEN_HOUR"] <= hour < cfg["CLOSE_HOUR"]):
        raise ReservationError(
            f"We take bookings between {cfg['OPEN_HOUR']}:00 and {cfg['CLOSE_HOUR']}:00."
        )


def available_tables(start, guests):
    """Tables that seat the party and have no booking overlapping the 90 minute window."""
    end = start + timedelta(minutes=_minutes())
    busy = Reservation.objects.filter(
        status=Reservation.CONFIRMED, start_time__lt=end, end_time__gt=start
    ).values_list("table_id", flat=True)
    return (
        Table.objects.filter(capacity__gte=guests)
        .exclude(id__in=busy)
        .order_by("capacity", "number")
    )


def reserve_table(customer_name, phone, guests, start, table_id=None):
    try:
        guests = int(guests)
    except (TypeError, ValueError):
        raise ReservationError("Number of guests must be a whole number.")
    if guests < 1:
        raise ReservationError("At least one guest is required.")
    customer_name = (customer_name or "").strip()
    if not customer_name:
        raise ReservationError("Please enter a name for the booking.")
    validate_slot(start)

    with transaction.atomic():
        tables = available_tables(start, guests)
        if table_id:
            tables = tables.filter(pk=table_id)
        table = tables.first()  # smallest table that fits
        if table is None:
            raise ReservationError(
                "No table is free for that party size and time. Try another time."
            )
        return Reservation.objects.create(
            table=table,
            customer_name=customer_name[:80],
            phone=(phone or "").strip()[:30],
            guests=guests,
            start_time=start,
        )


# --------------------------------------------------- inventory and reports

def low_stock_items():
    return InventoryItem.objects.filter(quantity__lte=F("reorder_level"))


def sales_report(day):
    orders = Order.objects.filter(created_at__date=day)
    totals = orders.aggregate(count=Count("id"), revenue=Sum("total"))
    count = totals["count"] or 0
    revenue = totals["revenue"] or Decimal("0")
    line_value = ExpressionWrapper(
        F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    top = (
        OrderItem.objects.filter(order__created_at__date=day)
        .values("menu_item__name")
        .annotate(sold=Sum("quantity"), revenue=Sum(line_value))
        .order_by("-sold", "menu_item__name")[:5]
    )
    return {
        "date": day.isoformat(),
        "orders": count,
        "revenue": revenue,
        "average": (revenue / count) if count else Decimal("0"),
        "top_items": [
            {"name": t["menu_item__name"], "quantity": t["sold"], "revenue": t["revenue"]}
            for t in top
        ],
    }
