from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import services
from .models import Ingredient, InventoryItem, MenuItem, Order, Reservation, Table


class OrderTests(TestCase):
    def setUp(self):
        self.flour = InventoryItem.objects.create(name="Flour", unit="kg", quantity=Decimal("1.0"), reorder_level=Decimal("0.2"))
        self.cheese = InventoryItem.objects.create(name="Cheese", unit="kg", quantity=Decimal("10"), reorder_level=1)
        self.pizza = MenuItem.objects.create(name="Pizza", price=1000, category="pizza_pasta")
        self.toast = MenuItem.objects.create(name="Toast", price=200, category="starters")
        Ingredient.objects.create(menu_item=self.pizza, inventory_item=self.flour, quantity=Decimal("0.4"))
        Ingredient.objects.create(menu_item=self.pizza, inventory_item=self.cheese, quantity=Decimal("0.2"))
        Ingredient.objects.create(menu_item=self.toast, inventory_item=self.flour, quantity=Decimal("0.1"))

    def test_order_deducts_inventory_and_totals(self):
        order = services.place_order("Ali", 3, [(self.pizza.id, 2), (self.toast.id, 1)])
        self.flour.refresh_from_db()
        self.cheese.refresh_from_db()
        self.assertEqual(order.total, Decimal("2200"))
        self.assertEqual(self.flour.quantity, Decimal("0.100"))
        self.assertEqual(self.cheese.quantity, Decimal("9.600"))

    def test_short_stock_rejects_whole_order(self):
        # 3 pizzas need 1.2 kg flour but only 1.0 kg exists
        with self.assertRaises(services.OrderError):
            services.place_order("Ali", None, [(self.toast.id, 1), (self.pizza.id, 3)])
        self.flour.refresh_from_db()
        self.assertEqual(self.flour.quantity, Decimal("1.000"))
        self.assertEqual(Order.objects.count(), 0)

    def test_empty_and_bad_quantity(self):
        with self.assertRaises(services.OrderError):
            services.place_order("Ali", None, [])
        with self.assertRaises(services.OrderError):
            services.place_order("Ali", None, [(self.pizza.id, 0)])

    def test_menu_marks_sold_out(self):
        self.flour.quantity = Decimal("0.05")
        self.flour.save()
        data = self.client.get(reverse("api-menu")).json()
        flat = {i["name"]: i["in_stock"] for c in data["categories"] for i in c["items"]}
        self.assertFalse(flat["Pizza"])
        self.assertFalse(flat["Toast"])

    def test_low_stock_list(self):
        services.place_order("Ali", None, [(self.pizza.id, 2)])  # flour 1.0 -> 0.2
        self.assertIn(self.flour, services.low_stock_items())
        self.assertNotIn(self.cheese, services.low_stock_items())


class ReservationTests(TestCase):
    def setUp(self):
        self.t4 = Table.objects.create(number=1, capacity=4)
        self.t2 = Table.objects.create(number=2, capacity=2)
        day = timezone.localtime(timezone.now() + timedelta(days=2))
        self.start = day.replace(hour=19, minute=0, second=0, microsecond=0)

    def test_smallest_fitting_table_is_chosen(self):
        r = services.reserve_table("Sara", "0300", 2, self.start)
        self.assertEqual(r.table, self.t2)
        self.assertEqual(r.end_time - r.start_time, timedelta(minutes=90))

    def test_overlap_blocks_and_back_to_back_is_allowed(self):
        services.reserve_table("A", "", 4, self.start)
        with self.assertRaises(services.ReservationError):
            services.reserve_table("B", "", 4, self.start + timedelta(minutes=60))
        services.reserve_table("C", "", 4, self.start + timedelta(minutes=90))

    def test_party_too_large(self):
        with self.assertRaises(services.ReservationError):
            services.reserve_table("D", "", 6, self.start)

    def test_past_and_closed_hours_rejected(self):
        with self.assertRaises(services.ReservationError):
            services.reserve_table("E", "", 2, timezone.now() - timedelta(hours=1))
        with self.assertRaises(services.ReservationError):
            services.reserve_table("E", "", 2, self.start.replace(hour=3))

    def test_cancelled_booking_frees_table(self):
        r = services.reserve_table("A", "", 4, self.start)
        Reservation.objects.filter(pk=r.pk).update(status=Reservation.CANCELLED)
        self.assertIn(self.t4, services.available_tables(self.start, 3))


class StaffApiTests(TestCase):
    def setUp(self):
        self.item = InventoryItem.objects.create(name="Mint", unit="kg", quantity=1, reorder_level=2)
        self.dish = MenuItem.objects.create(name="Lemonade", price=250, category="drinks")
        Ingredient.objects.create(menu_item=self.dish, inventory_item=self.item, quantity=Decimal("0.1"))
        self.staff = User.objects.create_user("chef", password="pw12345!", is_staff=True)
        self.guest = User.objects.create_user("guest", password="pw12345!")

    def test_staff_endpoints_require_staff(self):
        urls = [reverse("api-inventory"), reverse("api-sales"), reverse("api-sales-csv")]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.login(username="guest", password="pw12345!")
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(reverse("api-orders")).status_code, 403)

    def test_dashboard_redirects_anonymous(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_customer_can_order_over_api(self):
        res = self.client.post(reverse("api-orders"), {"customer_name": "Zed", "items": [{"id": self.dish.id, "quantity": 2}]},
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["total"], 500.0)

    def test_api_rejects_short_stock(self):
        res = self.client.post(reverse("api-orders"), {"items": [{"id": self.dish.id, "quantity": 11}]},
                               content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_staff_flow_status_restock_report_csv(self):
        order = services.place_order("Zed", 2, [(self.dish.id, 2)])
        self.client.login(username="chef", password="pw12345!")

        res = self.client.post(reverse("api-order-status", args=[order.id]), {"status": "served"}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "served")

        res = self.client.post(reverse("api-restock", args=[self.item.id]), {"amount": 5}, content_type="application/json")
        self.assertEqual(res.json()["quantity"], 5.8)

        today = timezone.localdate().isoformat()
        report = self.client.get(reverse("api-sales"), {"date": today}).json()
        self.assertEqual(report["orders"], 1)
        self.assertEqual(report["revenue"], 500.0)
        self.assertEqual(report["top_items"][0]["name"], "Lemonade")

        csv_res = self.client.get(reverse("api-sales-csv"), {"date": today})
        self.assertEqual(csv_res["Content-Type"], "text/csv")
        self.assertIn("Lemonade", csv_res.content.decode())

    def test_csrf_is_enforced(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        res = strict.post(reverse("api-orders"), {"items": []}, content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_non_staff_cannot_log_into_dashboard(self):
        res = self.client.post(reverse("dashboard-login"), {"username": "guest", "password": "pw12345!"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "does not have staff access")
