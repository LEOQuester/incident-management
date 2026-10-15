import re

import phonenumbers
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from accounts.models import User


class MultiIdentifierBackend(ModelBackend):
    """Authenticate using username, email, or international phone number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        identifier = username.strip()
        user = self._resolve_user(identifier)
        if user is None:
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _resolve_user(self, identifier: str) -> User | None:
        if "@" in identifier:
            return User.objects.filter(email__iexact=identifier).first()

        phone_user = self._user_by_phone(identifier)
        if phone_user:
            return phone_user

        return User.objects.filter(username__iexact=identifier).first()

    def _user_by_phone(self, raw: str) -> User | None:
        digits = re.sub(r"\D", "", raw)
        if not digits:
            return None
        try:
            parsed = phonenumbers.parse("+" + digits.lstrip("+"), None)
            if not phonenumbers.is_valid_number(parsed):
                parsed = phonenumbers.parse(raw, "LK")
        except phonenumbers.NumberParseException:
            try:
                parsed = phonenumbers.parse(raw, "LK")
            except phonenumbers.NumberParseException:
                return None

        if not phonenumbers.is_valid_number(parsed):
            return None

        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        return User.objects.filter(phone=e164).first()
