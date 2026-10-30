from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.utils.safestring import mark_safe
import phonenumbers

from accounts.models import User
from accounts.validators import normalize_cpm_number, normalize_mc_number
from rbac.models import Role


def role_choice_label(role: Role) -> str:
    if role.authority_id:
        return f"{role.name} — {role.authority.name}"
    return role.name


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
    department = forms.CharField(max_length=150, required=False)
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
    mc_number = forms.CharField(
        label="MC number",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. mc112202"}
        ),
    )
    cpm_number = forms.CharField(
        label="CPM number",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. cpm25666"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "department",
            "first_name",
            "last_name",
            "email",
            "phone",
            "mc_number",
            "cpm_number",
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
        self.fields["mc_number"].required = True
        self.fields["cpm_number"].required = True
        self.fields["department"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Department or faculty",
                "autocomplete": "organization-title",
            }
        )
        password_help = self.fields["password1"].help_text
        self.password_requirements = mark_safe(password_help) if password_help else ""
        self.fields["password1"].help_text = ""
        for field in ("password1", "password2"):
            self.fields[field].widget.attrs.update(
                {"class": "form-control", "placeholder": self.fields[field].label}
            )
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            return None
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email.lower()

    def clean_mc_number(self):
        raw = self.cleaned_data.get("mc_number", "")
        try:
            mc = normalize_mc_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        if User.objects.filter(mc_number=mc).exists():
            raise forms.ValidationError("This MC number is already registered.")
        return mc

    def clean_cpm_number(self):
        raw = self.cleaned_data.get("cpm_number", "")
        try:
            cpm = normalize_cpm_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        if User.objects.filter(cpm_number=cpm).exists():
            raise forms.ValidationError("This CPM number is already registered.")
        return cpm

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
        user.mc_number = self.cleaned_data.get("mc_number")
        user.cpm_number = self.cleaned_data.get("cpm_number")
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
            "department",
            "first_name",
            "last_name",
            "email",
            "phone",
            "mc_number",
            "cpm_number",
            "is_active",
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
            "mc_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Optional, e.g. mc112202"}
            ),
            "cpm_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Optional, e.g. cpm25666"}
            ),
            "roles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        compact = "form-control form-control-compact"
        for name, field in self.fields.items():
            if name == "roles":
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
                continue
            if hasattr(field.widget, "attrs"):
                field.widget.attrs["class"] = compact
        self.fields["roles"].label = "Roles"
        self.fields["roles"].help_text = (
            "Menus and case access come from assigned roles. "
            "Unit roles show the authority after the role name."
        )
        roles_field = self.fields["roles"]
        roles_field.queryset = Role.objects.select_related("authority").order_by(
            "authority__name",
            "name",
        )
        roles_field.label_from_instance = role_choice_label
        if not self.instance.pk:
            self.fields["password"].help_text = "Required for new users."
            self.fields["password"].required = True

    def clean_mc_number(self):
        raw = (self.cleaned_data.get("mc_number") or "").strip()
        if not raw:
            return None
        try:
            mc = normalize_mc_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        qs = User.objects.filter(mc_number=mc)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This MC number is already in use.")
        return mc

    def clean_cpm_number(self):
        raw = (self.cleaned_data.get("cpm_number") or "").strip()
        if not raw:
            return None
        try:
            cpm = normalize_cpm_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        qs = User.objects.filter(cpm_number=cpm)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This CPM number is already in use.")
        return cpm

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

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        if not self.instance.pk and not password:
            raise forms.ValidationError("Set a password for new users.")
        return password or None

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password, user)
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
            scoped_ids = set(
                user.roles.filter(authority__isnull=False).values_list(
                    "authority_id", flat=True
                )
            )
            from incidents.models import Authority

            Authority.objects.filter(primary_contact=user).exclude(
                pk__in=scoped_ids
            ).update(primary_contact=None)
        return user


PROFILE_AVATAR_MAX_BYTES = 2 * 1024 * 1024
PROFILE_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        label="Phone number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control phone-input",
                "type": "tel",
                "autocomplete": "tel",
                "placeholder": "+94 …",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "department",
            "mc_number",
            "cpm_number",
            "avatar",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "given-name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "family-name"}
            ),
            "department": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "organization-title"}
            ),
            "mc_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. mc112202",
                    "autocomplete": "off",
                }
            ),
            "cpm_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. cpm25666",
                    "autocomplete": "off",
                }
            ),
            "avatar": forms.FileInput(
                attrs={
                    "class": "profile-avatar-file visually-hidden",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["mc_number"].label = "MC number"
        self.fields["cpm_number"].label = "CPM number"
        if self.instance.pk and self.instance.phone:
            self.fields["phone"].initial = phonenumbers.format_number(
                self.instance.phone, phonenumbers.PhoneNumberFormat.E164
            )

    def clean_mc_number(self):
        raw = (self.cleaned_data.get("mc_number") or "").strip()
        if not raw:
            return None
        try:
            mc = normalize_mc_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        qs = User.objects.filter(mc_number=mc)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This MC number is already in use.")
        return mc

    def clean_cpm_number(self):
        raw = (self.cleaned_data.get("cpm_number") or "").strip()
        if not raw:
            return None
        try:
            cpm = normalize_cpm_number(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        qs = User.objects.filter(cpm_number=cpm)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This CPM number is already in use.")
        return cpm

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            return None
        email = email.lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return None
        try:
            parsed = phonenumbers.parse(raw, None)
            if not phonenumbers.is_valid_number(parsed):
                parsed = phonenumbers.parse(raw, "LK")
        except phonenumbers.NumberParseException as exc:
            raise forms.ValidationError("Enter a valid international phone number.") from exc
        if not phonenumbers.is_valid_number(parsed):
            raise forms.ValidationError("Enter a valid international phone number.")
        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        qs = User.objects.filter(phone=e164)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This phone number is already in use.")
        return e164

    def clean_avatar(self):
        upload = self.cleaned_data.get("avatar")
        if not upload:
            return upload
        if upload.size > PROFILE_AVATAR_MAX_BYTES:
            raise forms.ValidationError("Image must be 2 MB or smaller.")
        content_type = getattr(upload, "content_type", "") or ""
        if content_type and content_type not in PROFILE_AVATAR_TYPES:
            raise forms.ValidationError("Use a JPEG, PNG, or WebP image.")
        return upload

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone = self.cleaned_data.get("phone")
        if self.data.get("avatar-clear") and not self.files.get("avatar"):
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
        if commit:
            user.save()
        return user
