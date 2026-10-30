from django import forms

from rbac.features import FEATURE_BY_CODENAME
from rbac.models import Permission, Role

END_USER_PERMISSION_CODENAMES = frozenset(
    {"view_profile", "view_dashboard", "report_incident"}
)


def infer_is_end_user_role(role: Role, permission_codenames: set[str]) -> bool:
    """Staff/unit roles and any operational permission are never end-user roles."""
    if role.authority_id:
        return False
    if not permission_codenames:
        return False
    return permission_codenames.issubset(END_USER_PERMISSION_CODENAMES)


def display_name_for_codename(codename: str) -> str:
    return codename.replace("_", " ").replace("-", " ").strip().title()


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ("name", "description", "authority", "permissions")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "authority": forms.Select(attrs={"class": "form-control"}),
            "permissions": forms.CheckboxSelectMultiple(
                attrs={"class": "permission-checkbox-list"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = Permission.objects.all().order_by(
            "sort_order", "name"
        )
        self.fields["permissions"].label_from_instance = (
            lambda perm: f"{perm.name} ({perm.codename})"
        )
        self.fields["permissions"].help_text = (
            "Users with this role receive the checked permissions. "
            "Menu links and features for each code are configured in application code."
        )

    def save(self, commit=True):
        role = super().save(commit=False)
        perms = self.cleaned_data.get("permissions")
        codenames = (
            set(perms.values_list("codename", flat=True))
            if perms is not None
            else set(role.permissions.values_list("codename", flat=True))
        )
        role.is_end_user_role = infer_is_end_user_role(role, codenames)
        if commit:
            role.save()
            self.save_m2m()
        return role


class PermissionCreateForm(forms.Form):
    codename = forms.SlugField(
        label="Permission code",
        max_length=100,
        help_text=(
            "Custom codes only. Built-in permissions (e.g. manage_cases) are synced from "
            "application code when you open the Permissions list or run seed_rbac."
        ),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "approve_incidents",
                "autocomplete": "off",
            }
        ),
    )

    def clean_codename(self):
        codename = self.cleaned_data["codename"]
        existing = Permission.objects.filter(codename=codename).first()
        if existing:
            if existing.is_builtin or codename in FEATURE_BY_CODENAME:
                raise forms.ValidationError(
                    "That code is already a built-in permission synced from application code."
                )
            raise forms.ValidationError("A permission with this code already exists.")
        if codename in FEATURE_BY_CODENAME:
            raise forms.ValidationError(
                "That code is reserved for a built-in permission. "
                "Open the Permissions list to sync built-ins from application code."
            )
        return codename
