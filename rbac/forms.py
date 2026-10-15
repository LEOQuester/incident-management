from django import forms

from rbac.models import Role


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
