# FMSC Incident Management (USJ)

Django web application for the Faculty of Management Studies and Commerce, University of Sri Jayewardenepura. Provides universal login/registration and role-based access control, ready for Railway deployment.

## Features

- **Universal authentication**: sign in with email, E.164 phone number, or username; register with validated international phone numbers (intl-tel-input + `phonenumbers`).
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
2. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS` for your Railway domain.
3. Deploy this repository; the start command runs migrations, seeds default permissions, and collects static files.

## Default data

`python manage.py seed_rbac` creates the `view_dashboard` permission and a **Member** role (assigned automatically on self-registration).

Superusers manage additional permissions (with optional `url_name` for sidebar links), roles, and user assignments from the in-app Super Admin pages.
