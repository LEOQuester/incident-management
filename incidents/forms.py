from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from incidents.models import Incident, Authority, Category


class ReportIncidentForm(forms.ModelForm):
    declaration = forms.BooleanField(label="I confirm that the information is accurate to the best of my knowledge.")
    class Meta:
        model = Incident
        fields = ("title", "case_type", "priority", "category", "location", "description")
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        for name in ("title", "category", "location"):
            self.fields[name].required = True
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-control")

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


class CaseUpdateForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea, required=False, max_length=5000)
    internal = forms.BooleanField(required=False, label="Internal note (staff only)")

    class Meta:
        model = Incident
        fields = ("category", "priority", "authority", "status", "resolution_note")

    def __init__(self, *args, manager=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.fields["authority"].queryset = Authority.objects.filter(is_active=True)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        allowed = {"under_review", "not_started", "assigned", "in_progress", "waiting", "solved", "closed", "rejected", "reopened"}
        if not manager:
            allowed = {"in_progress", "waiting", "solved"}
            for field in ("category", "priority", "authority"):
                self.fields.pop(field)
        self.fields["status"].choices = [(k, v) for k, v in Incident.Status.choices if k in allowed]
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        if status == "solved" and not (cleaned.get("resolution_note") or "").strip():
            self.add_error("resolution_note", "A resolution note is required when marking a case solved.")
        authority = cleaned.get("authority") if self.manager else self.instance.authority
        if status in {"assigned", "in_progress", "waiting", "solved"} and not authority:
            self.add_error(None, "Assign an authority before starting or solving a case.")
        if status == "closed" and self.instance.status != "solved":
            self.add_error("status", "Only solved cases can be closed.")
        if status == "reopened" and self.instance.status not in {"solved", "closed", "rejected"}:
            self.add_error("status", "Only solved, closed, or rejected cases can be reopened.")
        if self.instance.status in {"closed", "rejected", "solved"} and status not in {"reopened", "closed"}:
            self.add_error("status", "Reopen this case before making further progress.")
        if status in {"rejected", "reopened"} and not (cleaned.get("comment") or "").strip():
            self.add_error("comment", "Explain why the case is rejected or reopened.")
        return cleaned


class AuthorityForm(forms.ModelForm):
    class Meta:
        model = Authority
        fields = ("name", "officer_name", "designation", "email", "phone", "unit", "is_active", "members")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "is_active")


def validate_evidence(files):
    """Validate file contents as well as extension; never trust browser MIME headers."""
    from pathlib import Path
    from PIL import Image, UnidentifiedImageError
    if len(files) > 5:
        raise ValidationError("Upload at most five evidence files at a time.")
    for uploaded in files:
        suffix = Path(uploaded.name).suffix.lower()
        head = uploaded.read(32)
        uploaded.seek(0)
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            if uploaded.size > 5 * 1024 * 1024:
                raise ValidationError("Images must not exceed 5 MiB.")
            try:
                image = Image.open(uploaded)
                image.verify()
                uploaded.content_type = Image.MIME.get(image.format, "image/jpeg")
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
                raise ValidationError("Upload a valid image.") from exc
            finally:
                uploaded.seek(0)
        elif suffix in {".mp4", ".webm"}:
            if uploaded.size > settings.INCIDENT_VIDEO_MAX_BYTES:
                raise ValidationError(f"Videos must not exceed {settings.INCIDENT_VIDEO_MAX_BYTES // (1024 * 1024)} MiB.")
            if suffix == ".mp4" and (len(head) < 12 or head[4:8] != b"ftyp"):
                raise ValidationError("Upload a valid MP4 video.")
            if suffix == ".webm" and not head.startswith(b"\x1a\x45\xdf\xa3"):
                raise ValidationError("Upload a valid WebM video.")
            validate_video(uploaded, suffix)
            uploaded.content_type = "video/mp4" if suffix == ".mp4" else "video/webm"
        else:
            raise ValidationError("Allowed evidence: JPEG, PNG, WebP, GIF, MP4, and WebM.")


def validate_video(uploaded, suffix):
    import json
    import math
    import subprocess
    import tempfile
    from pathlib import Path
    # Probe a private temporary file, without invoking a shell or allowing network protocols.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / f"evidence{suffix}"
        try:
            with path.open("wb") as target:
                for chunk in uploaded.chunks():
                    target.write(chunk)
            result = subprocess.run([
                settings.FFPROBE_PATH, "-v", "error", "-protocol_whitelist", "file",
                "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(path),
            ], capture_output=True, text=True, timeout=15, check=True)
            metadata = json.loads(result.stdout)
            duration = float(metadata["format"]["duration"])
            if not any(stream.get("codec_type") == "video" for stream in metadata.get("streams", [])):
                raise ValueError("Missing video stream")
            if not math.isfinite(duration) or duration <= 0 or duration > settings.INCIDENT_VIDEO_MAX_SECONDS:
                raise ValidationError(f"Video duration must be between 0 and {settings.INCIDENT_VIDEO_MAX_SECONDS} seconds.")
        except FileNotFoundError as exc:
            raise ValidationError("Video validation is unavailable. Contact the administrator or upload images instead.") from exc
        except (subprocess.SubprocessError, ValueError, KeyError, OSError) as exc:
            raise ValidationError("The video could not be validated. Upload a valid MP4 or WebM file.") from exc
        finally:
            uploaded.seek(0)
