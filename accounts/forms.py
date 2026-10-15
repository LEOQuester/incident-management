import phonenumbers
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

from accounts.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email, phone, or username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email, phone (+94…), or username",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email (optional)"}
        ),
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control phone-input",
                "placeholder": "Phone number",
                "type": "tel",
            }
        ),
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First name"}
        ),
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last name"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("password1", "password2"):
            self.fields[field].widget.attrs.update(
                {"class": "form-control", "placeholder": self.fields[field].label}
            )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            return None
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email.lower()

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "").strip()
        if not raw:
            return None
        try:
            parsed = phonenumbers.parse(raw, None)
            if not phonenumbers.is_valid_number(parsed):
                parsed = phonenumbers.parse(raw, "LK")
        except phonenumbers.NumberParseException as exc:
            raise forms.ValidationError("Enter a valid phone number.") from exc

        if not phonenumbers.is_valid_number(parsed):
            raise forms.ValidationError("Enter a valid phone number.")

        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        if User.objects.filter(phone=e164).exists():
            raise forms.ValidationError("An account with this phone number exists.")
        return e164

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        phone = cleaned.get("phone")
        if not email and not phone:
            raise forms.ValidationError(
                "Provide at least an email or a phone number in addition to username."
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.phone = self.cleaned_data.get("phone")
        if commit:
            user.save()
        return user


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Leave blank to keep the current password.",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_active",
            "is_staff",
            "is_superuser",
            "roles",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control phone-input", "type": "tel"}
            ),
            "roles": forms.CheckboxSelectMultiple(),
        }

    def clean_phone(self):
        raw = self.cleaned_data.get("phone")
        if not raw:
            return None
        if isinstance(raw, str):
            try:
                parsed = phonenumbers.parse(raw, None)
                if not phonenumbers.is_valid_number(parsed):
                    parsed = phonenumbers.parse(raw, "LK")
            except phonenumbers.NumberParseException as exc:
                raise forms.ValidationError("Enter a valid phone number.") from exc
            if not phonenumbers.is_valid_number(parsed):
                raise forms.ValidationError("Enter a valid phone number.")
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        return phonenumbers.format_number(
            raw, phonenumbers.PhoneNumberFormat.E164
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            return email.lower()
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password, user)
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user
