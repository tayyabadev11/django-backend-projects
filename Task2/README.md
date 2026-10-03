# Event Registration System

A Django web application for browsing events, registering for them, and managing bookings. Users can sign up, register for an event, then view or cancel their registrations. Organizers get an admin panel and a dashboard with attendee lists and CSV export.

Built for the **Backend Development**.

## Task requirements

| Requirement | Implementation |
|-------------|----------------|
| Set up backend using Django to manage routes and logic | `config/` (settings, root URLs) and `events/` (views, services, URLs) |
| Create models for events and user registrations | `Event` and `Registration` in `events/models.py` |
| Build API endpoints to view event list, event details and submit registration forms | `/api/events/`, `/api/events/<id>/`, `/api/events/<id>/register/` (plus matching web pages) |
| Link registrations to users and events; let users view and cancel their registrations | `Registration` has foreign keys to `User` and `Event`; "My registrations" page and `/api/registrations/` endpoints |
| Optional: admin panel or authentication for event organizers | Signup / login / logout, Django admin (`/admin/`), organizer dashboard (`/organizer/`) |

## Features

- Browse upcoming events with search and category filters
- Event detail page with date, venue, price and a live seat meter
- User accounts: sign up, login, logout
- Registration form with ticket count and total price, and a unique confirmation code (for example `EVT-7K2QXA`)
- My registrations: upcoming bookings with cancel, plus history of past and cancelled ones
- Organizer dashboard: all events with booking counts, attendee list per event, CSV download
- Themed Django admin for adding events, editing registrations and cancelling them in bulk
- JSON API for events and registrations
- Hand-drawn style interface with colour-coded event categories and illustrated event cards

## Tech stack

Python 3, Django 4.2+, SQLite (PostgreSQL optional), HTML, CSS, a little vanilla JavaScript.

## Data model

```
User (Django auth)                     Event
  id, username, password, ...            id, title, description, category,
        |                                venue, city, start, capacity, price,
        | 1                              organizer -> User, is_published
        |                                       |
        |            Registration               | 1
        +---------<  id, name, phone,  >--------+
          many       tickets, status,    many
                     code (unique),
                     created_at, cancelled_at
```

- One user can register for many events, and one event has many registrations.
- `Registration.status` is `confirmed` or `cancelled`. Cancelling keeps the record, so history is preserved.
- Seats left = event capacity minus the tickets of confirmed registrations.

## Business rules

Implemented once in `events/services.py` and used by both the web pages and the API:

- A user cannot register twice for the same event (unless the earlier registration was cancelled)
- Registration is rejected when the event is sold out or fewer seats remain than requested
- 1 to 5 tickets per booking
- Past events cannot be booked or cancelled
- Users can only cancel their own registrations
- Unpublished events are hidden from users

## Project structure

```
EventRegistrationSystem/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── config/                          # project settings and root URLs
│   ├── settings.py
│   └── urls.py
├── templates/
│   ├── base.html                    # header, footer, messages
│   ├── events/                      # home, detail, my registrations, organizer pages
│   ├── registration/                # login and signup
│   └── admin/base_site.html         # admin theme
└── events/                          # main app
    ├── models.py                    # Event, Registration
    ├── services.py                  # registration and cancellation rules
    ├── views.py                     # web pages
    ├── api.py                       # JSON API
    ├── urls.py   admin.py   forms.py
    ├── seed_data.py                 # demo events
    ├── migrations/
    ├── management/commands/seed.py  # loads demo data
    └── static/events/
        ├── css/style.css
        └── img/                     # event illustrations (<event-slug>.svg / .jpg / .png)
```

## Getting started

### 1. Clone the repository
```bash
git clone https://github.com/tayyabadev11/django-backend-projects.git
cd django-backend-projects/Task2
```

### 2. Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create the database and load demo data
```bash
python manage.py migrate
python manage.py seed
```

### 5. Run the server
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/

### Demo accounts
`seed` creates two accounts for development use only:

| Role | Username | Password |
|------|----------|----------|
| Organizer (staff, full admin access) | `organizer` | `organizer123` |
| Regular user | `demo` | `demo12345` |

You can also create your own admin with `python manage.py createsuperuser`.

## Pages

| Page | URL | Access |
|------|-----|--------|
| Events | `/` | Everyone |
| Event details and registration | `/events/<id>/` | Everyone (login needed to register) |
| My registrations | `/my-registrations/` | Logged-in users |
| Sign up / Login | `/signup/`, `/accounts/login/` | Everyone |
| Organizer dashboard | `/organizer/` | Staff |
| Attendees and CSV export | `/organizer/<id>/` | Staff |
| Admin panel | `/admin/` | Staff |

## How to use

**As an attendee:** browse events, open one, sign up or log in, fill the registration form, and note your confirmation code. Open **My registrations** at any time to review or cancel a booking.

**As an organizer:** log in with a staff account, open **Organizer** to see bookings per event, view attendees, or download them as CSV. Use **Add new event** (or `/admin/`) to publish events.

## API reference

Authentication uses the Django session: log in first, and send the CSRF token with POST requests. Responses are JSON.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/events/` | Upcoming events. Optional `?category=tech&q=lahore` | No |
| GET | `/api/events/<id>/` | Event details | No |
| POST | `/api/events/<id>/register/` | Submit a registration | Yes |
| GET | `/api/registrations/` | The logged-in user's registrations | Yes |
| POST | `/api/registrations/<id>/cancel/` | Cancel one of their registrations | Yes |

**Event**
```json
{
  "id": 1, "title": "Code and Coffee: Django Meetup", "category": "tech",
  "venue": "National Incubation Center", "city": "Islamabad",
  "start": "2026-10-05T17:00:00+05:00", "price": 0.0, "capacity": 60,
  "seats_left": 41, "description": "...", "image": "/static/events/img/code-and-coffee-django-meetup.svg"
}
```

**Register** `POST /api/events/1/register/`
```json
{ "name": "Ali Khan", "phone": "03001234567", "tickets": 2 }
```
Returns `201` with the registration, including `code`, `status`, `tickets`, `amount` and the event.

**Status codes:** `201` created, `400` invalid input, `401` login required, `404` not found, `409` a rule was violated (already registered, sold out, past event).
```json
{ "error": "You are already registered for this event." }
```

## Event images

Each event looks for `events/static/events/img/<event-title-slug>.<ext>`, for example `sunday-morning-10k-run.jpg`. Order of preference: `jpg`, `jpeg`, `png`, `webp`, the bundled illustrated `svg`, then a category illustration. To use real photos, copy them into that folder using the same file name.

## Using PostgreSQL (optional)

SQLite is used by default. To switch, install the driver and replace `DATABASES` in `config/settings.py`:

```bash
pip install psycopg2-binary
```
```python
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "events", "USER": "postgres", "PASSWORD": "your-password",
    "HOST": "localhost", "PORT": "5432",
}}
```
Then run `python manage.py migrate` and `python manage.py seed` again.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` is not recognised | Try `py` instead of `python` |
| `No module named django` | Activate the virtual environment and run `pip install -r requirements.txt` |
| Error while running `migrate` | Delete `events/migrations/0001_initial.py` and `db.sqlite3`, then run `python manage.py makemigrations events`, `python manage.py migrate`, `python manage.py seed` |
| Home page shows no events | Demo events are created relative to the day you run `seed`, so older ones become past events. Delete `db.sqlite3`, then run `migrate` and `seed` again |
| `Address already in use` | Run on another port: `python manage.py runserver 8001` |
| Event images look missing | Hard refresh the browser (Ctrl+F5) and check `events/static/events/img/` |

## Security notes

- `DEBUG = True` and the secret key in `config/settings.py` are for development only. Change them before deploying.
- The demo passwords above are for local use. Do not use them in production.

## Possible improvements

Email confirmations, online payments, QR-code tickets, waiting lists, automated tests, Docker setup.

## Author

Built by [tayyabadev11](https://github.com/tayyabadev11) as part of the Backend Development.
