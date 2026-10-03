import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from restaurant import services
from restaurant.models import Ingredient, InventoryItem, MenuItem, Order, Table

D = Decimal

TABLES = [(1, 2), (2, 2), (3, 2), (4, 4), (5, 4), (6, 4), (7, 6), (8, 8)]

# name: (unit, stock, reorder level)
INVENTORY = {
    "Flour": ("kg", 40, 5), "Mozzarella": ("kg", 15, 3), "Tomato Sauce": ("kg", 12, 2),
    "Fresh Tomato": ("kg", 15, 3), "Basil": ("kg", 1.5, 0.3), "Chicken": ("kg", 30, 5),
    "Beef": ("kg", 20, 4), "Pasta": ("kg", 20, 3), "Cream": ("l", 10, 2),
    "Lettuce": ("kg", 8, 1.5), "Burger Buns": ("pcs", 80, 15), "Cheese Slices": ("pcs", 100, 20),
    "Fish Fillet": ("kg", 12, 2), "Potatoes": ("kg", 25, 5), "Chocolate": ("kg", 5, 1),
    "Mascarpone": ("kg", 4, 1), "Coffee": ("kg", 3, 0.5), "Milk": ("l", 25, 5),
    "Sugar": ("kg", 15, 3), "Lemon": ("kg", 8, 1.5), "Mint": ("kg", 0.4, 0.5),
    "Eggs": ("pcs", 120, 20), "Bread Loaf": ("pcs", 30, 5), "Butter": ("kg", 8, 1.5),
    "Pepperoni": ("kg", 5, 1), "Olive Oil": ("l", 10, 2), "Cream Cheese": ("kg", 5, 1),
    "Strawberry": ("kg", 4, 0.8), "Soda": ("l", 20, 4), "BBQ Sauce": ("l", 6, 1),
    "Parmesan": ("kg", 3, 0.5),
}

# name: (category, price, image, description, {ingredient: amount per portion})
MENU = {
    "Bruschetta al Pomodoro": ("starters", 450, "bruschetta.svg",
        "Grilled bread rubbed with garlic, topped with tomato, basil and olive oil.",
        {"Bread Loaf": .5, "Fresh Tomato": .1, "Basil": .01, "Olive Oil": .02}),
    "Garlic Bread": ("starters", 350, "garlic-bread.svg",
        "Baguette slices baked with garlic butter and parsley.",
        {"Bread Loaf": .5, "Butter": .03}),
    "Tomato Basil Soup": ("starters", 400, "tomato-soup.svg",
        "Slow cooked tomato soup finished with cream, basil and croutons.",
        {"Fresh Tomato": .25, "Cream": .03, "Basil": .01, "Bread Loaf": .1}),
    "Crispy Chicken Wings": ("starters", 650, "chicken-wings.svg",
        "Six wings tossed in smoky BBQ glaze with a cool dip and celery.",
        {"Chicken": .4, "BBQ Sauce": .05}),
    "Caesar Salad": ("starters", 550, "caesar-salad.svg",
        "Crisp lettuce, grilled chicken, parmesan and croutons with house dressing.",
        {"Lettuce": .15, "Chicken": .12, "Parmesan": .02, "Bread Loaf": .1}),

    "Margherita Pizza": ("pizza_pasta", 1100, "margherita-pizza.svg",
        "Stone baked crust with tomato sauce, fresh mozzarella and basil.",
        {"Flour": .25, "Tomato Sauce": .1, "Mozzarella": .15, "Basil": .01}),
    "Pepperoni Pizza": ("pizza_pasta", 1350, "pepperoni-pizza.svg",
        "Tomato sauce, mozzarella and generous slices of spicy pepperoni.",
        {"Flour": .25, "Tomato Sauce": .1, "Mozzarella": .15, "Pepperoni": .08}),
    "BBQ Chicken Pizza": ("pizza_pasta", 1400, "bbq-chicken-pizza.svg",
        "Smoky BBQ sauce, grilled chicken, red onion and mozzarella.",
        {"Flour": .25, "Mozzarella": .15, "Chicken": .15, "BBQ Sauce": .05}),
    "Spaghetti Bolognese": ("pizza_pasta", 1000, "spaghetti-bolognese.svg",
        "Spaghetti in a slow cooked beef and tomato ragu with parmesan.",
        {"Pasta": .2, "Beef": .15, "Tomato Sauce": .1, "Parmesan": .02}),
    "Fettuccine Alfredo": ("pizza_pasta", 1050, "fettuccine-alfredo.svg",
        "Ribbon pasta in a creamy parmesan sauce with grilled chicken.",
        {"Pasta": .2, "Cream": .15, "Parmesan": .03, "Chicken": .1, "Butter": .02}),
    "Penne Arrabbiata": ("pizza_pasta", 900, "penne-arrabbiata.svg",
        "Penne in a spicy tomato and chilli sauce finished with basil.",
        {"Pasta": .2, "Tomato Sauce": .15, "Olive Oil": .02, "Basil": .01}),

    "Grilled Chicken Breast": ("mains", 1200, "grilled-chicken.svg",
        "Marinated chicken breast grilled over charcoal, with potatoes and greens.",
        {"Chicken": .3, "Potatoes": .2, "Butter": .02, "Lemon": .03}),
    "Beef Steak with Pepper Sauce": ("mains", 2200, "beef-steak.svg",
        "Grilled beef steak with a creamy pepper sauce, butter and roast potatoes.",
        {"Beef": .3, "Potatoes": .2, "Cream": .05, "Butter": .02}),
    "Classic Beef Burger": ("mains", 850, "beef-burger.svg",
        "Beef patty, cheese, lettuce and tomato in a toasted bun, with fries.",
        {"Burger Buns": 1, "Beef": .15, "Cheese Slices": 1, "Lettuce": .03, "Fresh Tomato": .04, "Potatoes": .15}),
    "Crispy Chicken Burger": ("mains", 800, "chicken-burger.svg",
        "Crunchy fried chicken fillet with lettuce and house sauce, with fries.",
        {"Burger Buns": 1, "Chicken": .15, "Lettuce": .03, "Eggs": 1, "Flour": .05, "Potatoes": .15}),
    "Grilled Fish with Lemon": ("mains", 1600, "grilled-fish.svg",
        "Fish fillet grilled with olive oil and lemon, served with potatoes.",
        {"Fish Fillet": .25, "Lemon": .05, "Olive Oil": .02, "Potatoes": .2}),
    "Club Sandwich": ("mains", 750, "club-sandwich.svg",
        "Toasted triple decker with chicken, egg, cheese, lettuce and tomato.",
        {"Bread Loaf": .4, "Chicken": .1, "Eggs": 1, "Lettuce": .03, "Fresh Tomato": .04, "Cheese Slices": 1}),

    "Chocolate Lava Cake": ("desserts", 600, "lava-cake.svg",
        "Warm chocolate cake with a molten centre and fresh strawberries.",
        {"Chocolate": .08, "Flour": .03, "Eggs": 1, "Butter": .04, "Sugar": .03, "Strawberry": .02}),
    "Tiramisu": ("desserts", 650, "tiramisu.svg",
        "Coffee soaked sponge layered with mascarpone cream and cocoa.",
        {"Mascarpone": .1, "Coffee": .02, "Eggs": 1, "Sugar": .03, "Chocolate": .01}),
    "Strawberry Cheesecake": ("desserts", 650, "cheesecake.svg",
        "Baked cheesecake on a biscuit base with strawberry glaze.",
        {"Cream Cheese": .12, "Strawberry": .05, "Sugar": .03, "Butter": .03, "Flour": .03}),

    "Fresh Lemonade": ("drinks", 250, "lemonade.svg",
        "Freshly squeezed lemon, mint and ice.",
        {"Lemon": .1, "Sugar": .03, "Mint": .01}),
    "Mint Margarita": ("drinks", 300, "mint-margarita.svg",
        "Cooler of lemon, crushed mint and soda over ice. No alcohol.",
        {"Lemon": .08, "Mint": .02, "Sugar": .03, "Soda": .2}),
    "Iced Coffee": ("drinks", 350, "iced-coffee.svg",
        "Cold brewed coffee with milk and ice.",
        {"Coffee": .02, "Milk": .2, "Sugar": .02}),
}


class Command(BaseCommand):
    help = "Load tables, inventory, menu and recipes. Safe to run more than once."

    def add_arguments(self, parser):
        parser.add_argument("--reset-stock", action="store_true",
                            help="Set inventory quantities back to the starting values.")
        parser.add_argument("--demo", action="store_true",
                            help="Also place some sample orders so the sales report has data.")

    @transaction.atomic
    def handle(self, *args, **opts):
        for number, capacity in TABLES:
            Table.objects.update_or_create(number=number, defaults={"capacity": capacity})

        inventory = {}
        for name, (unit, stock, reorder) in INVENTORY.items():
            item, created = InventoryItem.objects.get_or_create(
                name=name,
                defaults={"unit": unit, "quantity": D(str(stock)), "reorder_level": D(str(reorder))},
            )
            if not created and opts["reset_stock"]:
                item.quantity = D(str(stock))
                item.save(update_fields=["quantity"])
            inventory[name] = item

        for name, (category, price, image, description, recipe) in MENU.items():
            item, _ = MenuItem.objects.update_or_create(
                name=name,
                defaults={"category": category, "price": D(price), "image": image,
                          "description": description, "is_available": True},
            )
            for ing_name, amount in recipe.items():
                Ingredient.objects.update_or_create(
                    menu_item=item, inventory_item=inventory[ing_name],
                    defaults={"quantity": D(str(amount))},
                )

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(TABLES)} tables, {len(INVENTORY)} inventory items and {len(MENU)} dishes."
        ))

        if opts["demo"]:
            self._demo_orders()

    def _demo_orders(self):
        rng = random.Random(7)
        dishes = list(MenuItem.objects.all())
        statuses = [Order.PREPARING, Order.SERVED, Order.PAID, Order.PAID]
        names = ["Ayesha", "Bilal", "Hamza", "Sana", "Usman", "Maha", "Fahad", "Zara"]
        placed = 0
        for _ in range(12):
            picks = rng.sample(dishes, rng.randint(1, 3))
            try:
                order = services.place_order(
                    rng.choice(names), rng.randint(1, 8),
                    [(d.id, rng.randint(1, 3)) for d in picks],
                )
            except services.OrderError:
                continue
            order.status = rng.choice(statuses)
            order.save(update_fields=["status"])
            placed += 1
        self.stdout.write(self.style.SUCCESS(f"Placed {placed} sample orders."))
