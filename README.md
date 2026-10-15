# FMSC Incident Management (USJ)

Django web application for the Faculty of Management Studies and Commerce, University of Sri Jayewardenepura. Provides universal login/registration and role-based access control, ready for Railway deployment.

## Features

- **Universal authentication**: sign in with email, E.164 phone number, or username; register with validated international phone numbers (intl-tel-input + `phonenumbers`), plus mandatory **MC** (`mc112202`) and **CPM** (`cpm25666`) numbers on self-registration (optional when a superuser creates the account).
- **Incident reporting**: members submit a description (up to 2000 characters) and up to five optional photos (drag-and-drop UI).
- **Gemini routing**: incident text is sent to Google Gemini with staff role catalog; the model returns JSON role names; active users in those roles receive in-app notifications.
- **RBAC**: custom permissions and roles; users may hold multiple roles; roles hold many permissions.
- **Superuser admin UI**: CRUD permissions, roles (with permission assignment), and users (with role assignment).
- **Dynamic sidebar**: menu items appear from the logged-in user’s permission set; superuser sees an additional admin section.
- **FMSC styling**: Open Sans / Poppins typography and USJ theme colors (navy `#192f59`, green `#3db166`).

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_rbac
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/accounts/login/`.

## Railway

1. Create a PostgreSQL service and attach `DATABASE_URL` to the web service.
2. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, and `GEMINI_API_KEY` for your Railway domain.
3. Deploy this repository; the start command runs migrations, seeds default permissions, and collects static files.

## Default data

`python manage.py seed_rbac` creates dashboard/report permissions, a **Member** end-user role (auto-assigned on registration), and sample staff roles (**Security**, **IT Support**, **Student Affairs**) used by Gemini routing. Mark any role as **End-user role** in the super admin UI to exclude it from AI alerts.

Superusers manage additional permissions (with optional `url_name` for sidebar links), roles, and user assignments from the in-app Super Admin pages.
