# The Red Spoon Restaurant Management System

A restaurant system built with Django for the Backend Development.
Customers browse the menu, place orders and reserve tables. Staff manage orders, stock and sales
from a login protected panel.

## Features

**Customer site** (`/`)
- Menu with category filter, dish illustrations and live "sold out" marks based on stock
- Cart and order placement
- Table reservation with a free-table check

**Staff panel** (`/dashboard/`, staff login required)
- Daily sales report (orders, revenue, average order, top selling dishes) with CSV download
- Order list with status changes: placed, preparing, served, paid
- Inventory cards with a low-stock warning banner and one-click restock
- Upcoming reservations with cancel

**Admin panel** (`/admin/`)
- Menu, recipes (ingredients per dish), inventory, orders, tables and reservations

## Backend logic

| Rule | How it works |
| --- | --- |
| Order processing | `services.place_order` runs inside `transaction.atomic()`. |
| Stock check | Ingredients for the whole order are added up and compared with inventory. If anything is short, nothing is saved and the order is rejected. |
| Inventory update | When an order succeeds, each dish's recipe (`Ingredient` model) is subtracted from inventory automatically. |
| Table availability | A table is free if it seats the party and no confirmed booking overlaps the 90 minute window. Back to back bookings are allowed. The smallest fitting table is chosen. |
| Low stock | An item is low when `quantity <= reorder_level`. |

## Models

`MenuItem`, `Ingredient` (recipe line), `InventoryItem`, `Order`, `OrderItem`, `Table`, `Reservation`

## Setup

Requires Python 3.10 or newer.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up the database
python manage.py makemigrations restaurant
python manage.py migrate

# 4. Load tables, inventory, menu and recipes
python manage.py seed            # add --demo to also create sample orders

# 5. Create a staff account
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Open http://127.0.0.1:8000 for the customer site, http://127.0.0.1:8000/dashboard/ for the staff
panel and http://127.0.0.1:8000/admin/ for the admin panel. Log in with the superuser you created.

Dish photos live in `restaurant/static/images/`. Each dish points to a file there through its
`image` field, so you can swap in your own photos (use the same file name, or change the name in
the admin panel). The included illustrations can be redrawn with `python tools/make_images.py`.

`python manage.py seed --reset-stock` puts inventory back to the starting amounts.

## API

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /api/menu/` | public | Menu grouped by category, with stock status |
| `POST /api/orders/` | public | Place an order `{customer_name, table_number, items:[{id, quantity}]}` |
| `GET /api/reservations/availability/?start=&guests=` | public | Free tables for a time and party size |
| `POST /api/reservations/` | public | Reserve a table `{customer_name, phone, guests, start, table_id?}` |
| `GET /api/orders/` | staff | Recent orders, optional `?status=` |
| `POST /api/orders/<id>/status/` | staff | Change order status |
| `GET /api/inventory/` | staff | Stock levels and low-stock list |
| `POST /api/inventory/<id>/restock/` | staff | Add stock `{amount}` |
| `GET /api/reports/sales/?date=YYYY-MM-DD` | staff | Daily sales report |
| `GET /api/reports/sales.csv?date=YYYY-MM-DD` | staff | Same report as a CSV file |
| `GET /api/reservations/` | staff | Upcoming reservations |
| `POST /api/reservations/<id>/cancel/` | staff | Cancel a reservation |

All POST requests are CSRF protected. Staff endpoints return 403 for anyone who is not staff.

## Tests

```bash
python manage.py test
```

Covers order totals, automatic stock deduction, full rollback on short stock, reservation overlap
and capacity rules, staff-only access, status changes, restock, sales report, CSV and CSRF.

## Project structure

```
config/                 Django settings and root URLs
restaurant/
  models.py             Data models
  services.py           Ordering, availability and report logic
  views.py              Pages and JSON API
  admin.py              Admin configuration
  management/commands/  seed command
  templates/            Customer site, staff panel, login, admin theme
  static/               CSS, JavaScript, dish images
  migrations/           Database migrations
  tests.py              Automated tests
tools/make_images.py    Redraws the dish illustrations
```
