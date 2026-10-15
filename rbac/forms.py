import phonenumbers
from django import forms

from rbac.models import Permission, Role


class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = (
            "codename",
            "name",
            "description",
            "url_name",
            "menu_label",
            "menu_icon",
            "menu_order",
        )
        widgets = {
            "codename": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "url_name": forms.TextInput(attrs={"class": "form-control"}),
            "menu_label": forms.TextInput(attrs={"class": "form-control"}),
            "menu_icon": forms.TextInput(attrs={"class": "form-control"}),
            "menu_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ("name", "description", "is_end_user_role", "permissions")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_end_user_role": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "permissions": forms.CheckboxSelectMultiple(),
        }
