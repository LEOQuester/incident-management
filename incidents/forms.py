from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from incidents.models import Incident


class ReportIncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("description",)
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control incident-description",
                    "rows": 6,
                    "placeholder": "Describe what happened, where, and when…",
                    "maxlength": settings.INCIDENT_DESCRIPTION_MAX_LENGTH,
                }
            ),
        }

    def clean_description(self):
        text = (self.cleaned_data.get("description") or "").strip()
        if len(text) < 10:
            raise ValidationError("Please provide at least 10 characters.")
        max_len = settings.INCIDENT_DESCRIPTION_MAX_LENGTH
        if len(text) > max_len:
            raise ValidationError(f"Description cannot exceed {max_len} characters.")
        return text


def validate_incident_photos(files):
    max_count = settings.INCIDENT_MAX_PHOTOS
    max_bytes = settings.INCIDENT_PHOTO_MAX_BYTES
    allowed = settings.INCIDENT_ALLOWED_IMAGE_TYPES

    if len(files) > max_count:
        raise ValidationError(f"You can upload at most {max_count} images.")

    for uploaded in files:
        content_type = getattr(uploaded, "content_type", "") or ""
        if content_type not in allowed:
            raise ValidationError(
                f"Unsupported image type: {content_type or uploaded.name}."
            )
        if uploaded.size > max_bytes:
            raise ValidationError(
                f"Each image must be smaller than {max_bytes // (1024 * 1024)} MB."
            )
