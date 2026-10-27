from django import forms

from rbac.models import Permission, Role


def display_name_for_codename(codename: str) -> str:
    return codename.replace("_", " ").replace("-", " ").strip().title()


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ("name", "description", "is_end_user_role", "permissions")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_end_user_role": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "permissions": forms.CheckboxSelectMultiple(
                attrs={"class": "permission-checkbox-list"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = Permission.objects.all().order_by(
            "sort_order", "name"
        )
        self.fields["permissions"].label_from_instance = lambda perm: perm.name
        self.fields["permissions"].help_text = (
            "Users with this role receive the checked permissions. "
            "Menu links and features for each code are configured in application code."
        )


class PermissionCreateForm(forms.Form):
    codename = forms.SlugField(
        label="Permission code",
        max_length=100,
        help_text="Use lowercase letters, numbers, and underscores (e.g. approve_incidents).",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "approve_incidents",
                "autocomplete": "off",
            }
        ),
    )
