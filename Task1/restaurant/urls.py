from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/login/", views.StaffLoginView.as_view(), name="dashboard-login"),
    path("dashboard/logout/", LogoutView.as_view(), name="dashboard-logout"),

    # public API
    path("api/menu/", views.api_menu, name="api-menu"),
    path("api/orders/", views.orders_collection, name="api-orders"),
    path("api/reservations/", views.reservations_collection, name="api-reservations"),
    path("api/reservations/availability/", views.reservation_availability, name="api-availability"),

    # staff API
    path("api/orders/<int:pk>/status/", views.order_status, name="api-order-status"),
    path("api/inventory/", views.inventory_list, name="api-inventory"),
    path("api/inventory/<int:pk>/restock/", views.inventory_restock, name="api-restock"),
    path("api/reports/sales/", views.sales_report_json, name="api-sales"),
    path("api/reports/sales.csv", views.sales_report_csv, name="api-sales-csv"),
    path("api/reservations/<int:pk>/cancel/", views.reservation_cancel, name="api-reservation-cancel"),
]
