# Backend Development - Tasks

This repository contains my submissions for the **Backend Development**. Both projects are full-stack web applications built with **Django**, with a REST-style JSON API, a database layer, authentication or staff access, and a hand-drawn style responsive interface.

| Folder | Project | What it does |
|--------|---------|--------------|
| [`Task1`](Task1) | Restaurant Management System | Menu, orders, table reservations and inventory, with reporting and a staff dashboard |
| [`Task2`](Task2) | Event Registration System | Browse events, register, and view or cancel bookings, with an organizer dashboard |

## Tech stack

Python 3 - Django 4.2+ - SQLite - HTML, CSS and vanilla JavaScript

---

## Task 1 - Restaurant Management System

A restaurant app where customers browse a Pakistani menu, place orders and reserve tables, while staff manage orders, stock and sales.

**Requirements covered**
- Django backend for orders, tables and inventory
- Database models for menu items, orders, tables, reservations and inventory
- APIs for placing orders, reserving tables, updating inventory and viewing the menu
- Logic for order processing, table availability check and automatic inventory update
- Optional: daily sales reporting, low-stock alerts and an admin access panel

**Highlights**
- Orders run in a single database transaction. Ingredients are deducted from inventory automatically, and an order is rejected if stock is insufficient
- Table availability check matches party size to table capacity and prevents overlapping bookings (90-minute slots)
- Staff dashboard with sales report for any date, CSV export, low-stock alerts, order status updates and restocking
- Themed Django admin with recipes (ingredients) editable inside each menu item
- Menu with 6 categories and 22 dishes, prices in PKR, and an illustrated image for each dish

**Run it**
```bash
cd Task1
python -m venv venv
venv\Scripts\activate            # macOS / Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed --demo     # menu, inventory, tables and sample orders
python manage.py createsuperuser # staff account for /dashboard/ and /admin/
python manage.py runserver
```

| Page | URL |
|------|-----|
| Customer site | http://127.0.0.1:8000/ |
| Staff dashboard (login required) | http://127.0.0.1:8000/dashboard/ |
| Admin panel | http://127.0.0.1:8000/admin/ |

**API overview**

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/api/menu/` | Public |
| POST | `/api/orders/` | Public |
| GET | `/api/tables/available/?start=YYYY-MM-DDTHH:MM&guests=N` | Public |
| POST | `/api/reservations/` | Public |
| GET | `/api/inventory/` | Staff |
| POST | `/api/inventory/<id>/restock/` | Staff |
| GET | `/api/reports/daily/?date=YYYY-MM-DD` and `/api/reports/daily.csv` | Staff |
| GET | `/api/orders/list/`, POST `/api/orders/<id>/status/` | Staff |

---

## Task 2 - Event Registration System

An event platform where users sign up, register for events, and manage their registrations, while organizers see attendees.

**Requirements covered**
- Django backend to manage routes and logic
- Models for events and user registrations
- API endpoints to view the event list, event details and submit registration forms
- Registrations linked to users and events, with users able to view and cancel their own
- Optional: admin panel and authentication for event organizers

**Highlights**
- Business rules in one place (`events/services.py`): no duplicate registration, capacity limits, 1 to 5 tickets per booking, past events locked, users can only cancel their own bookings
- Unique confirmation code for every booking
- "My registrations" page with upcoming bookings, cancel option and history
- Organizer dashboard with attendee lists and CSV download, plus a themed Django admin
- 14 demo events across 7 colour-coded categories, each with an illustration

**Run it**
```bash
cd Task2
python -m venv venv
venv\Scripts\activate            # macOS / Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed            # demo events, organizer and demo user
python manage.py runserver
```

Demo accounts created by `seed` (development only):

| Role | Username | Password |
|------|----------|----------|
| Organizer (staff) | `organizer` | `organizer123` |
| Regular user | `demo` | `demo12345` |

| Page | URL |
|------|-----|
| Events | http://127.0.0.1:8000/ |
| My registrations | http://127.0.0.1:8000/my-registrations/ |
| Organizer dashboard | http://127.0.0.1:8000/organizer/ |
| Admin panel | http://127.0.0.1:8000/admin/ |

**API overview**

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/api/events/` | Public |
| GET | `/api/events/<id>/` | Public |
| POST | `/api/events/<id>/register/` | Logged-in user |
| GET | `/api/registrations/` | Logged-in user |
| POST | `/api/registrations/<id>/cancel/` | Logged-in user |

Each project folder has its own `README.md` with the full documentation: project structure, API examples, troubleshooting and more.

---

## Getting the code

```bash
git clone https://github.com/tayyabadev11/django-backend-projects.git
cd django-backend-projects
```

## Notes

- `DEBUG = True` and the secret keys in each `config/settings.py` are for development only.
- Demo passwords are for local use. Do not use them in production.
- Possible improvements: automated tests, Docker setup, PostgreSQL, payments, email notifications.

## Author

Built by [tayyabadev11](https://github.com/tayyabadev11) as part of the Backend Development.
