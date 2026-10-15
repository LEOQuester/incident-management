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

1. Create a **PostgreSQL** service and attach **`DATABASE_URL`** to the web service (Variables → reference from Postgres).
2. In the web service **Settings → Networking**, click **Generate domain** (public URL).
3. Set variables on the web service:
   - `DJANGO_SECRET_KEY` (long random string)
   - `DJANGO_DEBUG=False`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://YOUR-DOMAIN.up.railway.app` (your generated URL)
   - `GEMINI_API_KEY` (optional until you use AI routing)
4. Redeploy. The app auto-adds `RAILWAY_PUBLIC_DOMAIN` to `ALLOWED_HOSTS` when Railway provides it.
5. Health check: `GET /health/` should return `{"status": "ok"}`.

If you see **Application failed to respond** while Gunicorn logs look fine:

1. **Networking** → confirm a **public domain** is generated for the **web** service (not only Postgres).
2. **Variables** → web service must reference **`DATABASE_URL`** from the Postgres plugin.
3. Open **`/health/`** first; it should return `{"status": "ok"}` even before login works.
4. In service **Settings**, ensure the HTTP proxy targets the same port Gunicorn logs show (usually **`$PORT`**, often `8080`).

## Default data

`python manage.py seed_rbac` creates dashboard/report permissions, a **Member** end-user role (auto-assigned on registration), and sample staff roles (**Security**, **IT Support**, **Student Affairs**) used by Gemini routing. Mark any role as **End-user role** in the super admin UI to exclude it from AI alerts.

Superusers manage additional permissions (with optional `url_name` for sidebar links), roles, and user assignments from the in-app Super Admin pages.
