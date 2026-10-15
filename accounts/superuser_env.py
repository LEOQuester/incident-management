"""Read superuser bootstrap fields from environment / .env (via django settings load_dotenv)."""

import os

import phonenumbers


def get_superuser_config() -> dict | None:
    """
    Return username, password, email, phone (E.164) from env, or None if disabled.

    Variables (set in .env locally or Railway service variables):
      DJANGO_SUPERUSER_USERNAME
      DJANGO_SUPERUSER_PASSWORD
      DJANGO_SUPERUSER_EMAIL   (optional but recommended)
      DJANGO_SUPERUSER_PHONE   (optional; stored as E.164)
    """
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
    if not username or not password:
        return None

    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip().lower() or None
    phone_raw = os.environ.get("DJANGO_SUPERUSER_PHONE", "").strip()
    phone = _normalize_phone(phone_raw) if phone_raw else None

    return {
        "username": username,
        "password": password,
        "email": email,
        "phone": phone,
    }


def _normalize_phone(raw: str) -> str:
    try:
        parsed = phonenumbers.parse(raw, None)
        if not phonenumbers.is_valid_number(parsed):
            parsed = phonenumbers.parse(raw, "LK")
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Invalid DJANGO_SUPERUSER_PHONE: {raw}") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(f"Invalid DJANGO_SUPERUSER_PHONE: {raw}")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
