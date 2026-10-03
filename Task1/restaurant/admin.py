from django.contrib import admin

from .models import (
    Ingredient, InventoryItem, MenuItem, Order, OrderItem, Reservation, Table,
)


class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1
    verbose_name = "recipe ingredient"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_available")
    list_filter = ("category", "is_available")
    list_editable = ("price", "is_available")
    search_fields = ("name",)
    inlines = [IngredientInline]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "unit", "reorder_level", "low_stock")
    list_editable = ("quantity", "reorder_level")
    search_fields = ("name",)

    @admin.display(boolean=True, description="Low stock")
    def low_stock(self, obj):
        return obj.is_low


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("menu_item", "quantity", "unit_price")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "table_number", "status", "total", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = ("customer_name",)
    readonly_fields = ("total", "created_at")
    inlines = [OrderItemInline]


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "capacity")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "table", "guests", "start_time", "end_time", "status")
    list_filter = ("status", "table")
    list_editable = ("status",)
    search_fields = ("customer_name", "phone")
    readonly_fields = ("end_time",)
