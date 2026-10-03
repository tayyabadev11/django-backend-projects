from datetime import timedelta

from django.conf import settings
from django.db import models

CATEGORIES = [
    ("starters", "Starters"),
    ("pizza_pasta", "Pizza and Pasta"),
    ("mains", "Mains"),
    ("desserts", "Desserts"),
    ("drinks", "Drinks"),
]


class InventoryItem(models.Model):
    name = models.CharField(max_length=80, unique=True)
    unit = models.CharField(max_length=10, default="kg", help_text="kg, l, pcs")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_level = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        help_text="A low-stock alert appears when quantity falls to this level.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_low(self):
        return self.quantity <= self.reorder_level


class MenuItem(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    image = models.CharField(
        max_length=100, blank=True,
        help_text="File name inside restaurant/static/images/ (for example margherita-pizza.svg)",
    )
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def in_stock(self):
        """True when the inventory can cover one portion of this dish."""
        return all(
            ing.inventory_item.quantity >= ing.quantity for ing in self.ingredients.all()
        )


class Ingredient(models.Model):
    """Recipe line: how much of an inventory item one portion of a dish uses."""

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="ingredients")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="used_in")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, help_text="Amount per portion")

    class Meta:
        unique_together = ("menu_item", "inventory_item")

    def __str__(self):
        return f"{self.menu_item} uses {self.quantity} {self.inventory_item.unit} {self.inventory_item}"


class Table(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    capacity = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number} (seats {self.capacity})"


class Reservation(models.Model):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    STATUSES = [(CONFIRMED, "Confirmed"), (CANCELLED, "Cancelled")]

    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name="reservations")
    customer_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=30, blank=True)
    guests = models.PositiveSmallIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def save(self, *args, **kwargs):
        if not self.end_time:
            minutes = settings.RESTAURANT["RESERVATION_MINUTES"]
            self.end_time = self.start_time + timedelta(minutes=minutes)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name}, table {self.table.number}, {self.start_time:%d %b %H:%M}"


class Order(models.Model):
    PLACED, PREPARING, SERVED, PAID = "placed", "preparing", "served", "paid"
    STATUSES = [
        (PLACED, "Placed"),
        (PREPARING, "Preparing"),
        (SERVED, "Served"),
        (PAID, "Paid"),
    ]

    customer_name = models.CharField(max_length=80, default="Guest")
    table_number = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=PLACED)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price
